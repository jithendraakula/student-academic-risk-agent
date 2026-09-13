from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.domain import AlertIntervention, User
from app.schemas.risk import InterventionUpdate
from app.services.rbac import can_access_student, normalize_role
from app.services.alerts import alert_item
from app.services.interventions import intervention_detail, intervention_history, intervention_queue, intervention_summary, update_intervention

router = APIRouter()


@router.get("/summary")
def get_intervention_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor", "hod", "dean")),
):
    return intervention_summary(db, user)


@router.get("/queue")
def get_intervention_queue(
    status: str | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor", "hod", "dean")),
):
    if status and status.upper() not in {"NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP", "RESOLVED"}:
        raise HTTPException(status_code=400, detail="Unsupported intervention status")
    return intervention_queue(db, user, status=status, overdue_only=overdue_only, limit=limit)


@router.patch("/{alert_id}")
def patch_intervention(
    alert_id: str,
    payload: InterventionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor")),
):
    alert = db.get(AlertIntervention, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not can_access_student(db, user, alert.student_id):
        raise HTTPException(status_code=403, detail="Alert is outside your access scope")
    try:
        return update_intervention(
            db, alert, user,
            status=payload.status,
            notes=payload.notes,
            follow_up_date=payload.follow_up_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{alert_id}/history")
def get_intervention_history(
    alert_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor", "hod", "dean")),
):
    try:
        return {"items": intervention_history(db, alert_id, user)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{alert_id}")
def get_intervention(
    alert_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor", "hod", "dean")),
):
    alert = db.get(AlertIntervention, alert_id)
    if not alert or not can_access_student(db, user, alert.student_id):
        raise HTTPException(status_code=404, detail="Intervention not found in your access scope")
    return intervention_detail(db, alert, user)
