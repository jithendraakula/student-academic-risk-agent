from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import User
from app.services.dean import (
    department_comparison,
    department_students,
    institution_summary,
    priority_queue,
    risk_heatmap,
)

router = APIRouter()


@router.get("/summary")
def get_dean_summary(db: Session = Depends(get_db), user: User = Depends(require_roles("dean"))):
    return institution_summary(db, user)


@router.get("/department-comparison")
def get_department_comparison(db: Session = Depends(get_db), user: User = Depends(require_roles("dean"))):
    return department_comparison(db, user)


@router.get("/risk-heatmap")
def get_risk_heatmap(db: Session = Depends(get_db), user: User = Depends(require_roles("dean"))):
    return risk_heatmap(db, user)


@router.get("/priority-queue")
def get_priority_queue(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("dean")),
):
    return priority_queue(db, user, limit=limit)


@router.get("/departments/{department}/students")
def list_department_students(
    department: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("dean")),
):
    result = department_students(db, user, department)
    if result is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return result
