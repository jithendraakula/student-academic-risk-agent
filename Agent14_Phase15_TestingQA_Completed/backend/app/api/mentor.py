from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import AlertIntervention, User
from app.services.alerts import alert_item, get_active_alerts, sync_canonical_alerts
from app.services.mentor import filter_mentor_students, mentor_student_detail, mentor_workspace
from app.services.rbac import can_access_student, scoped_student_ids
from app.services.risk_engine import normalize_risk_type
from app.services.interventions import acknowledge_intervention, update_intervention

router = APIRouter()


def _in_scope(db: Session, user: User, student_id: str) -> bool:
    return can_access_student(db, user, student_id)


@router.get("/summary")
def get_mentor_summary(db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    workspace = mentor_workspace(db, user)
    return {key: workspace[key] for key in (
        "mentor_id", "mentor_name", "department", "assigned_students",
        "critical_students", "high_risk_students", "high_only_students", "elevated_risk_students",
        "students_needing_action", "students_with_multiple_risks", "risk_signals", "actionable_risk_signals",
        "open_alerts", "open_alert_students", "new_alerts", "new_alert_students",
        "risk_distribution", "metric_semantics", "risk_thresholds", "risk_source", "alert_source", "alert_policy",
    )}


@router.get("/students")
def get_mentor_students(
    q: str | None = Query(default=None, max_length=80),
    risk_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    needs_action: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor")),
):
    if risk_type and normalize_risk_type(risk_type) is None:
        raise HTTPException(status_code=400, detail="Unsupported risk type")

    # The attention queue is the operational view. Synchronize its intervention
    # records from the canonical current predictions before filtering so every
    # actionable student can receive the same completion workflow. Existing
    # manually-resolved alerts for the current prediction remain resolved.
    student_ids = scoped_student_ids(db, user)
    sync_canonical_alerts(
        db,
        student_ids,
        include_support_attention=True,
    )

    return filter_mentor_students(
        db, user, query=q, risk_type=risk_type, severity=severity,
        status=status, needs_action=needs_action, page=page, page_size=page_size,
    )


@router.get("/students/{student_id}")
def get_mentor_student(student_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    row = mentor_student_detail(db, user, student_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found in your assigned cohort")
    return row


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    student_ids = scoped_student_ids(db, user)
    alerts = get_active_alerts(db, student_ids, user)
    return {
        "items": [alert_item(db, alert) for alert in alerts],
        "assigned_students": len(student_ids),
        "open_alerts": len(alerts),
        "new_alerts": sum(alert.status == "NEW" for alert in alerts),
        "action_required": sum(alert.priority_score >= 60 for alert in alerts),
        "risk_source": "risk_predictions",
        "alert_policy": {"priority_threshold": 60, "critical_override": True},
    }


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    student_ids = scoped_student_ids(db, user)
    alerts = get_active_alerts(db, student_ids, user)
    return {"items": [alert_item(db, alert) for alert in alerts], "risk_source": "risk_predictions"}


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    alert = db.get(AlertIntervention, alert_id)
    if not alert or not _in_scope(db, user, alert.student_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    try:
        return acknowledge_intervention(db, alert, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
