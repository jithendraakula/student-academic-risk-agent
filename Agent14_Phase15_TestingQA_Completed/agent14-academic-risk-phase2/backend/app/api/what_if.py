from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import User
from app.schemas.what_if import WhatIfRequest
from app.services.what_if import simulate_student

router = APIRouter()


@router.post("/student/{student_id}")
def run_student_what_if(
    student_id: str,
    payload: WhatIfRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor", "hod", "dean")),
):
    return simulate_student(db, student_id, user, payload)
