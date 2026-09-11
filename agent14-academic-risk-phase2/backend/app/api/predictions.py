from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import User
from app.services.auth import get_current_user
from app.services.risk import build_student_risk_profile

router = APIRouter()


@router.get("/student/{student_id}")
def get_student_risk_profile(student_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return build_student_risk_profile(db, student_id, user)
