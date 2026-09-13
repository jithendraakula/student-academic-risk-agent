from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import User
from app.services.hod import department_risk_overview, department_students, department_summary, mentor_comparison, mentor_students
from app.services.risk_engine import normalize_risk_type

router = APIRouter()


@router.get("/summary")
def get_hod_summary(db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    return department_summary(db, user)


@router.get("/mentor-comparison")
def get_mentor_comparison(db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    return mentor_comparison(db, user)


@router.get("/risk-overview")
def get_risk_overview(db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    return department_risk_overview(db, user)


@router.get("/mentors/{mentor_id}/students")
def list_mentor_students(
    mentor_id: str,
    q: str | None = Query(default=None, max_length=80),
    section: str | None = Query(default=None, max_length=8),
    risk_type: str | None = Query(default=None),
    needs_action: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("hod")),
):
    if risk_type and normalize_risk_type(risk_type) is None:
        raise HTTPException(status_code=400, detail="Unsupported risk type")
    result = mentor_students(db, user, mentor_id, query=q, section=section, risk_type=risk_type, needs_action=needs_action)
    if result is None:
        raise HTTPException(status_code=404, detail="Mentor not found in your department")
    return result


@router.get("/students")
def list_department_students(db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    return {
        "department": user.department,
        "items": department_students(db, user),
        "risk_source": "risk_predictions",
    }
