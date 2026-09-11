from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import AlertIntervention, User
from app.schemas.risk import InterventionUpdate
from app.services.auth import get_current_user
from app.services.rbac import can_access_student

router = APIRouter()


@router.patch("/{alert_id}")
def update_intervention(alert_id: str, payload: InterventionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = db.get(AlertIntervention, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not can_access_student(db, user, alert.student_id):
        raise HTTPException(status_code=403, detail="Alert is outside your access scope")
    alert.status = payload.status
    alert.intervention_notes = payload.notes
    alert.data = {**(alert.data or {}), "follow_up_date": payload.follow_up_date, "action_taken": payload.notes}
    db.commit()
    db.refresh(alert)
    return {"alert_id": alert.id, "student_id": alert.student_id, "status": alert.status, "notes": alert.intervention_notes, "data": alert.data}
