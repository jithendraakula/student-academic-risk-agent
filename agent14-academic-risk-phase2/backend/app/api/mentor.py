from fastapi import APIRouter
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import AlertIntervention, Student, User
from app.services.auth import get_current_user, require_roles
from app.services.rbac import scoped_student_ids

router = APIRouter()


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    student_ids = scoped_student_ids(db, user)
    alerts = db.scalars(select(AlertIntervention).where(AlertIntervention.student_id.in_(student_ids)).order_by(AlertIntervention.priority_score.desc())).all()
    return {"items": [_alert_item(db, alert) for alert in alerts], "assigned_students": len(student_ids), "open_alerts": sum(alert.status not in ("RESOLVED",) for alert in alerts)}


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    student_ids = scoped_student_ids(db, user)
    alerts = db.scalars(select(AlertIntervention).where(AlertIntervention.student_id.in_(student_ids)).order_by(AlertIntervention.priority_score.desc())).all()
    return {"items": [_alert_item(db, alert) for alert in alerts]}


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("mentor"))):
    alert = db.get(AlertIntervention, alert_id)
    if not alert or not _in_scope(db, user, alert.student_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "ACKNOWLEDGED"
    db.commit()
    return _alert_item(db, alert)


def _in_scope(db: Session, user: User, student_id: str) -> bool:
    return student_id in scoped_student_ids(db, user)


def _alert_item(db: Session, alert: AlertIntervention) -> dict:
    student = db.get(Student, alert.student_id)
    return {"alert_id": alert.id, "student_id": alert.student_id, "student_name": student.name if student else None, "teacher_id": alert.teacher_id, "risk_type": alert.risk_type, "risk_score": alert.risk_score, "priority_score": alert.priority_score, "status": alert.status, **(alert.data or {})}
