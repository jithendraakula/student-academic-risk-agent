"""Canonical alert synchronization and lifecycle helpers."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AcademicObservation, AlertIntervention, Assignment, RiskPrediction, Student, Teacher, User
from app.services.risk_engine import normalize_risk_type, should_create_alert, RISK_TYPES
from app.services.rbac import can_view_support_attention_risk
from app.services.context_intelligence import classify_observation

OPEN_STATUSES = {"NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"}


def _course_id(alert: AlertIntervention) -> str | None:
    return (alert.data or {}).get("course_id")


def _prediction_key(prediction: RiskPrediction) -> tuple[str, str, str | None]:
    return (prediction.student_id, prediction.risk_type, prediction.course_id)


def _alert_key(alert: AlertIntervention) -> tuple[str, str | None, str | None]:
    return (alert.student_id, normalize_risk_type(alert.risk_type), _course_id(alert))


def _mentor_for_student(db: Session, student_id: str) -> str | None:
    assignment = db.scalar(
        select(Assignment)
        .where(
            Assignment.student_id == student_id,
            Assignment.assignment_type == "mentor",
        )
        .order_by(Assignment.id.desc())
    )
    return assignment.teacher_id if assignment else None


def _suggested_action(risk_type: str) -> str:
    actions = {
        "course_failure": "Review course performance and create a focused recovery plan.",
        "backlog": "Review pending courses and create a backlog clearance plan.",
        "gpa_threshold": "Review GPA drivers and set an academic improvement target.",
        "attendance_shortage": "Review the attendance barrier and create a recovery plan.",
        "discontinuation": "Coordinate appropriate academic/support follow-up and monitor continuity.",
    }
    return actions[normalize_risk_type(risk_type) or risk_type]


_CONTEXT_TO_RISKS = {
    "health_recovery": {"attendance_shortage", "discontinuation"},
    "transport_attendance": {"attendance_shortage"},
    "attendance_pattern": {"attendance_shortage"},
    "assessment_support": {"course_failure", "gpa_threshold", "backlog"},
    "subject_academic_support": {"course_failure", "gpa_threshold", "backlog"},
    "family_support": {"attendance_shortage", "discontinuation", "gpa_threshold"},
    "improvement_maintain": set(),
    "general_support": set(),
}


def _context_for_alert(db: Session, student_id: str, risk_type: str) -> dict:
    canonical = normalize_risk_type(risk_type) or risk_type
    observations = db.scalars(
        select(AcademicObservation)
        .where(AcademicObservation.student_id == student_id)
        .order_by(AcademicObservation.observed_on.desc(), AcademicObservation.id.desc())
    ).all()
    # Prefer active/open observations and recent evidence. Closed history is
    # retained for the student record but should not normally route a new alert.
    candidates = [o for o in observations if (getattr(o, "status", None) or "OPEN") != "CLOSED"]
    for observation in candidates:
        context = classify_observation(observation.category, observation.observation_text)
        if canonical in _CONTEXT_TO_RISKS.get(context["intent"], set()):
            return {
                **context,
                "observation_text": observation.observation_text,
                "observation_date": str(observation.observed_on) if getattr(observation, "observed_on", None) else None,
            }
    return {}


def _upsert_alert(db: Session, prediction: RiskPrediction, existing: AlertIntervention | None) -> AlertIntervention:
    student = db.get(Student, prediction.student_id)
    teacher_id = existing.teacher_id if existing else _mentor_for_student(db, prediction.student_id)
    if existing is None:
        existing = AlertIntervention(
            id=f"ALC-{uuid.uuid4().hex[:12].upper()}",
            student_id=prediction.student_id,
            teacher_id=teacher_id or "SYSTEM",
            risk_type=prediction.risk_type,
            risk_score=prediction.risk_score,
            priority_score=prediction.priority_score,
            status="NEW",
            data={},
        )
        db.add(existing)

    existing.teacher_id = teacher_id or existing.teacher_id
    existing.risk_type = prediction.risk_type
    existing.risk_score = prediction.risk_score
    existing.priority_score = prediction.priority_score
    previous_data = existing.data or {}
    context = _context_for_alert(db, prediction.student_id, prediction.risk_type)
    existing.data = {
        **previous_data,
        "source": "risk_predictions",
        "prediction_id": prediction.id,
        "semester": prediction.semester,
        "checkpoint_week": prediction.checkpoint_week,
        "course_id": prediction.course_id,
        "risk_level": prediction.risk_level,
        "risk_probability": prediction.risk_probability,
        "confidence": prediction.confidence,
        "decision_threshold": prediction.decision_threshold,
        "intervenability_score": prediction.intervenability_score,
        "model_version": prediction.model_version,
        "suggested_action": context.get("recommended_action") or previous_data.get("suggested_action") or _suggested_action(prediction.risk_type),
        "context_intent": context.get("intent"),
        "context_intent_label": context.get("intent_label"),
        "context_action_type": context.get("action_type"),
        "context_urgency": context.get("urgency"),
        "context_support_only": context.get("support_only", False),
        "context_classifier": context.get("classifier"),
        "context_observation": context.get("observation_text"),
        "context_observation_date": context.get("observation_date"),
        "is_active": True,
        "last_synced_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    if existing.status == "RESOLVED" and previous_data.get("auto_resolved"):
        existing.status = "NEW"
        existing.data["auto_resolved"] = False
        existing.intervention_notes = None
    return existing


def sync_canonical_alerts(
    db: Session,
    student_ids: list[str] | None = None,
    *,
    include_support_attention: bool = True,
) -> list[AlertIntervention]:
    """Make AlertIntervention a lifecycle projection of current RiskPrediction rows.

    The prediction table is the sole source of risk/priority truth. This function
    only projects qualifying snapshots into actionable alert records and closes
    stale alerts when a prediction is no longer actionable.
    """
    predictions = db.scalars(
        select(RiskPrediction).where(
            RiskPrediction.student_id.in_(student_ids) if student_ids else True
        )
    ).all()

    latest: dict[tuple[str, str, str | None], RiskPrediction] = {}
    for prediction in predictions:
        key = _prediction_key(prediction)
        if key not in latest or (
            prediction.semester,
            prediction.checkpoint_week,
            prediction.id,
        ) > (
            latest[key].semester,
            latest[key].checkpoint_week,
            latest[key].id,
        ):
            latest[key] = prediction

    active_predictions = {
        key: prediction
        for key, prediction in latest.items()
        if should_create_alert(
            prediction.risk_score,
            prediction.risk_level,
            prediction.priority_score,
        )
        and (include_support_attention or prediction.risk_type != "discontinuation")
    }

    alerts = db.scalars(
        select(AlertIntervention).where(
            AlertIntervention.student_id.in_(student_ids) if student_ids else True
        )
    ).all()

    # Normalize any legacy dataset alert keys while preserving their lifecycle.
    alerts_by_key: dict[tuple[str, str, str | None], list[AlertIntervention]] = defaultdict(list)
    for alert in alerts:
        canonical = normalize_risk_type(alert.risk_type)
        if canonical:
            key = (alert.student_id, canonical, _course_id(alert))
            alert.risk_type = canonical
            alerts_by_key[key].append(alert)

    selected_active: list[AlertIntervention] = []
    for key, prediction in active_predictions.items():
        candidates = alerts_by_key.get(key, [])
        matching_current = next(
            (a for a in candidates if (a.data or {}).get("prediction_id") == prediction.id),
            None,
        )
        open_candidate = next((a for a in candidates if a.status in OPEN_STATUSES), None)
        existing = matching_current or open_candidate
        alert = _upsert_alert(db, prediction, existing)
        selected_active.append(alert)

    active_keys = set(active_predictions)
    for key, candidates in alerts_by_key.items():
        if key in active_keys:
            for alert in candidates:
                if alert in selected_active:
                    continue
                # Older alert projections remain historical once a new canonical
                # snapshot replaces them.
                if alert.status != "RESOLVED":
                    alert.status = "RESOLVED"
                alert.data = {
                    **(alert.data or {}),
                    "source": "risk_predictions",
                    "is_active": False,
                    "auto_resolved": True,
                    "resolved_reason": "Superseded by newer canonical prediction snapshot",
                }
        else:
            for alert in candidates:
                if alert.status != "RESOLVED":
                    alert.status = "RESOLVED"
                alert.data = {
                    **(alert.data or {}),
                    "source": "risk_predictions",
                    "is_active": False,
                    "auto_resolved": True,
                    "resolved_reason": "Prediction no longer meets canonical alert policy",
                }

    db.commit()
    from app.services.notifications import emit_alert_notifications
    emit_alert_notifications(db, selected_active)
    return selected_active


def get_active_alerts(
    db: Session,
    student_ids: list[str],
    user: User | None = None,
    *,
    synchronize: bool = False,
) -> list[AlertIntervention]:
    """Read active alert work items without re-running ML/sync on every GET.

    Callers that intentionally changed current predictions can opt into
    synchronization; ordinary dashboard reads should remain read-only.
    """
    if synchronize:
        from app.services.aggregation import ensure_current_predictions
        ensure_current_predictions(db, student_ids)
        sync_canonical_alerts(
            db,
            student_ids,
            include_support_attention=(user is None or can_view_support_attention_risk(user.role)),
        )
    alerts = db.scalars(
        select(AlertIntervention)
        .where(
            AlertIntervention.student_id.in_(student_ids),
            AlertIntervention.status.in_(OPEN_STATUSES),
        )
        .order_by(AlertIntervention.priority_score.desc(), AlertIntervention.updated_at.desc())
    ).all()
    if user is not None and not can_view_support_attention_risk(user.role):
        alerts = [a for a in alerts if normalize_risk_type(a.risk_type) != "discontinuation"]
    return alerts


def alert_item(db: Session, alert: AlertIntervention) -> dict:
    student = db.get(Student, alert.student_id)
    data = alert.data or {}
    item = dict(data)
    # Canonical API fields always win over legacy CSV payload keys.
    item.update({
        "alert_id": alert.id,
        "student_id": alert.student_id,
        "student_name": student.name if student else None,
        "teacher_id": alert.teacher_id,
        "risk_type": normalize_risk_type(alert.risk_type) or alert.risk_type,
        "risk_label": RISK_TYPES.get(normalize_risk_type(alert.risk_type) or alert.risk_type, alert.risk_type),
        "risk_score": float(alert.risk_score),
        "priority_score": float(alert.priority_score),
        "status": alert.status,
        "risk_level": data.get("risk_level"),
        "confidence": data.get("confidence"),
        "intervenability_score": data.get("intervenability_score"),
        "course_id": data.get("course_id"),
        "source": data.get("source"),
        "suggested_action": data.get("suggested_action"),
        "created_at": alert.updated_at.isoformat() if alert.updated_at else None,
    })
    return item
