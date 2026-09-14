from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import User
from app.services.notifications import notification_list, notification_summary, mark_read, mark_all_read, notification_sync

router = APIRouter()
STAFF_ROLES = ("mentor", "hod", "dean")

@router.get("/summary")
def get_notification_summary(db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    return notification_summary(db, user)

@router.get("")
def get_notifications(unread_only: bool = Query(default=False), limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    return {"items": notification_list(db, user, unread_only=unread_only, limit=limit), **notification_summary(db, user)}

@router.post("/read-all")
def read_all_notifications(db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    return mark_all_read(db, user)

@router.patch("/{notification_id}/read")
def read_notification(notification_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    try:
        return mark_read(db, user, notification_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("/sync")
def sync_notifications(db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    return notification_sync(db, user)
