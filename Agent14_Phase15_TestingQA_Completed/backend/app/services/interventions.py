"""Institutional intervention workflow built on canonical alerts."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, date, timedelta
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AlertIntervention, Assignment, InterventionRecord, Student, User
from app.services.alerts import OPEN_STATUSES, alert_item, get_active_alerts, sync_canonical_alerts
from app.services.rbac import can_access_student, scoped_student_ids, normalize_role
from app.services.risk_engine import normalize_risk_type
from app.services.audit import record_audit
from app.services.cases import COMPLETED_CASE, get_active_case, get_or_create_case, record_case_event

STATUS_ORDER = {
    "NEW": 0,
    "ACKNOWLEDGED": 1,
    "ACTION_TAKEN": 2,
    "FOLLOW_UP": 3,
    "RESOLVED": 4,
}

ALLOWED_TRANSITIONS = {
    "NEW": {"ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP", "RESOLVED"},
    "ACKNOWLEDGED": {"ACTION_TAKEN", "FOLLOW_UP", "RESOLVED"},
    "ACTION_TAKEN": {"FOLLOW_UP", "RESOLVED"},
    "FOLLOW_UP": {"ACTION_TAKEN", "FOLLOW_UP", "RESOLVED"},
    "RESOLVED": set(),
}


def parse_follow_up(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("follow_up_date must use YYYY-MM-DD") from exc


def _assert_transition(current: str, target: str) -> None:
    if current not in STATUS_ORDER or target not in STATUS_ORDER:
        raise ValueError("Unsupported intervention status")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Cannot move intervention from {current} to {target}")


def _record_history(
    db: Session,
    *,
    alert: AlertIntervention,
    user: User,
    from_status: str,
    to_status: str,
    notes: str | None,
    follow_up_date: str | None,
) -> InterventionRecord:
    record = InterventionRecord(
        id=f"INT-{uuid.uuid4().hex[:12].upper()}",
        alert_id=alert.id,
        student_id=alert.student_id,
        actor_id=user.id,
        from_status=from_status,
        to_status=to_status,
        notes=notes,
        follow_up_date=follow_up_date,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    return record


def update_intervention(
    db: Session,
    alert: AlertIntervention,
    user: User,
    *,
    status: str,
    notes: str | None,
    follow_up_date: str | None,
) -> dict:
    status = status.upper().strip()
    current = alert.status.upper().strip()
    _assert_transition(current, status)

    if status in {"ACTION_TAKEN", "FOLLOW_UP", "RESOLVED"} and not (notes or "").strip():
        raise ValueError("Notes are required when recording an intervention action")
    if status == "FOLLOW_UP" and not follow_up_date:
        raise ValueError("follow_up_date is required for FOLLOW_UP status")

    parsed = parse_follow_up(follow_up_date)
    if parsed and parsed < date.today() and status != "RESOLVED":
        raise ValueError("follow_up_date cannot be in the past for an active intervention")

    previous_data = dict(alert.data or {})
    _record_history(
        db,
        alert=alert,
        user=user,
        from_status=current,
        to_status=status,
        notes=(notes or "").strip() or None,
        follow_up_date=follow_up_date,
    )

    alert.status = status
    alert.intervention_notes = (notes or "").strip() or alert.intervention_notes
    alert.data = {
        **previous_data,
        "follow_up_date": follow_up_date,
        "action_taken": (notes or "").strip() or previous_data.get("action_taken"),
        "last_action_by": user.id,
        "last_action_at": datetime.utcnow().isoformat(timespec="seconds"),
        "intervention_active": status in OPEN_STATUSES,
    }
    record_audit(db, action="INTERVENTION_STATUS_CHANGED", actor=user, resource_type="alert", resource_id=alert.id, details={"student_id": alert.student_id, "from_status": current, "to_status": status})
    case = get_active_case(db, alert.student_id) or get_or_create_case(db, alert.student_id)
    alert.case_id = case.id
    case.updated_at = datetime.utcnow()
    record_case_event(db, case=case, actor_id=user.id, event_type="INTERVENTION_UPDATED", from_status=current, to_status=status, notes=(notes or "").strip() or None, metadata={"alert_id": alert.id, "follow_up_date": follow_up_date})
    db.commit()
    db.refresh(alert)
    from app.services.events import publish_case_event
    publish_case_event({"type": "INTERVENTION_UPDATED", "case_id": case.id, "student_id": alert.student_id, "alert_id": alert.id, "actor_id": user.id})
    return intervention_detail(db, alert, user)


def acknowledge_intervention(db: Session, alert: AlertIntervention, user: User) -> dict:
    """Record mentor acknowledgement as an explicit acknowledgement action.

    Acknowledgement is idempotent and may be recorded even when a legacy/demo
    alert was already progressed beyond ACKNOWLEDGED. Resolution is the only
    terminal state that cannot be acknowledged again.
    """
    if alert.status == "RESOLVED":
        raise ValueError("Resolved interventions cannot be acknowledged")
    if alert.status == "ACKNOWLEDGED":
        return {**alert_item(db, alert), "data": dict(alert.data or {}), "notes": alert.intervention_notes}
    previous = alert.status
    _record_history(
        db, alert=alert, user=user, from_status=previous, to_status="ACKNOWLEDGED",
        notes="Mentor acknowledged the intervention.", follow_up_date=(alert.data or {}).get("follow_up_date")
    )
    alert.status = "ACKNOWLEDGED"
    alert.data = {
        **(alert.data or {}),
        "last_action_by": user.id,
        "last_action_at": datetime.utcnow().isoformat(timespec="seconds"),
        "intervention_active": True,
    }
    record_audit(db, action="INTERVENTION_ACKNOWLEDGED", actor=user, resource_type="alert", resource_id=alert.id, details={"student_id": alert.student_id})
    case = get_active_case(db, alert.student_id) or get_or_create_case(db, alert.student_id)
    alert.case_id = case.id
    case.updated_at = datetime.utcnow()
    record_case_event(db, case=case, actor_id=user.id, event_type="INTERVENTION_ACKNOWLEDGED", from_status=previous, to_status="ACKNOWLEDGED", notes="Mentor acknowledged the intervention.", metadata={"alert_id": alert.id})
    db.commit(); db.refresh(alert)
    from app.services.events import publish_case_event
    publish_case_event({"type": "INTERVENTION_ACKNOWLEDGED", "case_id": case.id, "student_id": alert.student_id, "alert_id": alert.id, "actor_id": user.id})
    return {**alert_item(db, alert), "data": dict(alert.data or {}), "notes": alert.intervention_notes}


def complete_student_case(
    db: Session,
    student_id: str,
    user: User,
    *,
    action_category: str = "GENERAL_SUPPORT",
    completion_reason: str | None = None,
    notes: str | None = None,
    follow_up_outcome: str | None = None,
) -> dict:
    """Complete the student's current stable case transactionally."""
    if not can_access_student(db, user, student_id):
        raise PermissionError("Student is outside your access scope")
    from app.services.aggregation import ensure_current_predictions
    ensure_current_predictions(db, [student_id])
    sync_canonical_alerts(db, [student_id], include_support_attention=True)
    case = get_active_case(db, student_id)
    alerts = db.scalars(
        select(AlertIntervention).where(
            AlertIntervention.student_id == student_id,
            AlertIntervention.status.in_(OPEN_STATUSES),
            AlertIntervention.risk_type != "case_completion",
        ).order_by(AlertIntervention.priority_score.desc(), AlertIntervention.updated_at.desc())
    ).all()
    if case is None and alerts:
        case = get_or_create_case(db, student_id)
        for alert in alerts:
            alert.case_id = case.id
    if case is None:
        # A no-alert completion is only meaningful as confirmation of an already
        # completed case; do not manufacture an open case.
        latest = db.scalar(select(__import__('app.models.domain', fromlist=['StudentCase']).StudentCase).where(__import__('app.models.domain', fromlist=['StudentCase']).StudentCase.student_id == student_id).order_by(__import__('app.models.domain', fromlist=['StudentCase']).StudentCase.updated_at.desc()))
        if latest and latest.status == COMPLETED_CASE:
            return {"student_id": student_id, "case_id": latest.id, "status": COMPLETED_CASE, "resolved_alerts": 0, "alert_ids": [], "completed_at": latest.completed_at.isoformat() if latest.completed_at else None, "idempotent": True}
        raise ValueError("No active case is available for this student")

    completed_at = datetime.utcnow()
    resolved_ids: list[str] = []
    history_count = 0
    normalized_notes = (notes or "").strip() or "Student support case marked complete by mentor."
    for alert in alerts:
        current = alert.status.upper().strip()
        if alert.case_id and alert.case_id != case.id:
            continue
        _record_history(db, alert=alert, user=user, from_status=current, to_status="RESOLVED", notes=normalized_notes, follow_up_date=(alert.data or {}).get("follow_up_date"))
        history_count += 1
        alert.case_id = case.id
        alert.status = "RESOLVED"
        alert.intervention_notes = normalized_notes
        alert.data = {**(alert.data or {}), "last_action_by": user.id, "last_action_at": completed_at.isoformat(timespec="seconds"), "completed_at": completed_at.isoformat(timespec="seconds"), "completed_by": user.id, "intervention_active": False, "case_completed": True, "is_active": False}
        record_audit(db, action="INTERVENTION_STATUS_CHANGED", actor=user, resource_type="alert", resource_id=alert.id, details={"student_id": student_id, "case_id": case.id, "from_status": current, "to_status": "RESOLVED", "scope": "student_case"})
        resolved_ids.append(alert.id)

    case.status = COMPLETED_CASE
    case.completed_at = completed_at
    case.completed_by = user.id
    case.completion_category = action_category.strip()[:64] or "GENERAL_SUPPORT"
    case.completion_reason = (completion_reason or "").strip()[:255] or None
    case.completion_notes = normalized_notes
    case.follow_up_outcome = (follow_up_outcome or "").strip()[:128] or None
    case.completion_metadata = {**(case.completion_metadata or {}), "resolved_alert_count": len(resolved_ids), "history_records_created": history_count, "completed_by_name": user.name}
    case.updated_at = completed_at
    record_case_event(db, case=case, actor_id=user.id, event_type="CASE_COMPLETED", from_status="OPEN", to_status=COMPLETED_CASE, notes=normalized_notes, metadata={"action_category": case.completion_category, "completion_reason": case.completion_reason, "follow_up_outcome": case.follow_up_outcome, "resolved_alert_ids": resolved_ids})
    record_audit(db, action="CASE_COMPLETED", actor=user, resource_type="student_case", resource_id=case.id, details={"student_id": student_id, "action_category": case.completion_category, "completion_reason": case.completion_reason, "resolved_alerts": len(resolved_ids)})
    db.commit()
    from app.services.events import publish_case_event
    publish_case_event({"type": "CASE_COMPLETED", "case_id": case.id, "student_id": student_id, "actor_id": user.id})
    return {"student_id": student_id, "case_id": case.id, "status": COMPLETED_CASE, "resolved_alerts": len(resolved_ids), "alert_ids": resolved_ids, "completed_at": completed_at.isoformat(), "history_records_created": history_count, "completion_category": case.completion_category, "completion_reason": case.completion_reason, "follow_up_outcome": case.follow_up_outcome}


def intervention_history(db: Session, alert_id: str, user: User) -> list[dict]:
    alert = db.get(AlertIntervention, alert_id)
    if not alert or not can_access_student(db, user, alert.student_id):
        raise PermissionError("Intervention is outside your access scope")
    records = db.scalars(
        select(InterventionRecord)
        .where(InterventionRecord.alert_id == alert_id)
        .order_by(InterventionRecord.created_at.desc())
    ).all()
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_({r.actor_id for r in records}))).all()} if records else {}
    return [
        {
            "id": r.id,
            "alert_id": r.alert_id,
            "actor_id": r.actor_id,
            "actor_name": users.get(r.actor_id).name if r.actor_id in users else r.actor_id,
            "from_status": r.from_status,
            "to_status": r.to_status,
            "notes": r.notes,
            "follow_up_date": r.follow_up_date,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


def intervention_detail(db: Session, alert: AlertIntervention, user: User) -> dict:
    item = alert_item(db, alert)
    follow_up = (alert.data or {}).get("follow_up_date")
    due_date = parse_follow_up(follow_up) if follow_up else None
    today = date.today()
    item.update({
        "data": dict(alert.data or {}),
        "notes": alert.intervention_notes,
        "follow_up_date": follow_up,
        "overdue": bool(due_date and due_date < today and alert.status in OPEN_STATUSES),
        "days_until_follow_up": (due_date - today).days if due_date else None,
        "allowed_next_statuses": sorted(ALLOWED_TRANSITIONS.get(alert.status, set()), key=lambda s: STATUS_ORDER[s]),
        "can_intervene": normalize_role(user.role) == "mentor",
        "history": intervention_history(db, alert.id, user),
    })
    return item


def intervention_summary(db: Session, user: User) -> dict:
    ids = scoped_student_ids(db, user)
    alerts = get_active_alerts(db, ids, user)
    all_scoped = db.scalars(
        select(AlertIntervention).where(AlertIntervention.student_id.in_(ids))
    ).all()

    active_counts = Counter(alert.status for alert in alerts)
    resolved = sum(alert.status == "RESOLVED" for alert in all_scoped)
    today = date.today()
    overdue = 0
    due_soon = 0
    for alert in alerts:
        raw = (alert.data or {}).get("follow_up_date")
        try:
            due = date.fromisoformat(raw) if raw else None
        except ValueError:
            due = None
        if due:
            if due < today:
                overdue += 1
            elif due <= today + timedelta(days=7):
                due_soon += 1

    return {
        "scope_role": normalize_role(user.role),
        "assigned_students": len(ids),
        "open_interventions": len(alerts),
        "new": active_counts.get("NEW", 0),
        "acknowledged": active_counts.get("ACKNOWLEDGED", 0),
        "action_taken": active_counts.get("ACTION_TAKEN", 0),
        "follow_up": active_counts.get("FOLLOW_UP", 0),
        "resolved": resolved,
        "overdue_follow_ups": overdue,
        "due_within_7_days": due_soon,
        "resolution_rate": round(resolved / max(1, len(all_scoped)) * 100, 1),
        "risk_source": "risk_predictions",
    }


def intervention_queue(db: Session, user: User, *, status: str | None = None, overdue_only: bool = False, limit: int = 50, page: int = 1, page_size: int = 25) -> dict:
    ids = scoped_student_ids(db, user)
    alerts = get_active_alerts(db, ids, user)
    if status:
        status = status.upper()
        alerts = [a for a in alerts if a.status == status]
    if overdue_only:
        today = date.today()
        filtered = []
        for alert in alerts:
            raw = (alert.data or {}).get("follow_up_date")
            try:
                due = date.fromisoformat(raw) if raw else None
            except ValueError:
                due = None
            if due and due < today:
                filtered.append(alert)
        alerts = filtered

    alerts.sort(key=lambda a: (a.status == "FOLLOW_UP", float(a.priority_score or 0), a.updated_at or datetime.min), reverse=True)
    total = len(alerts)
    size = max(1, min(int(page_size), int(limit), 100)); page = max(1, int(page))
    start = (page - 1) * size
    page_items = alerts[start:start + size]
    return {"items": [intervention_detail(db, alert, user) for alert in page_items], "returned": len(page_items), "total": total, "page": page, "page_size": size, "total_pages": max(1, (total + size - 1) // size), "status": status, "overdue_only": overdue_only, "risk_source": "risk_predictions"}
