from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Student, SystemSetting, Teacher, User
from app.core.dependencies import require_roles
from app.services.audit import record_audit

router = APIRouter()


class ThresholdConfig(BaseModel):
    gpa_threshold: float = Field(ge=0, le=10)
    attendance_threshold: float = Field(ge=0, le=100)


@router.get("/students")
def list_students(q: str | None = None, page: int = 1, page_size: int = 50, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    query = select(Student).order_by(Student.name.asc())
    if q:
        needle = f"%{q.strip().lower()}%"
        query = query.where(__import__('sqlalchemy').or_(Student.id.ilike(needle), Student.name.ilike(needle), Student.department.ilike(needle), Student.roll_number.ilike(needle)))
    total = db.scalar(select(__import__('sqlalchemy').func.count()).select_from(query.subquery())) or 0
    page = max(1, page); page_size = max(1, min(page_size, 100))
    rows = db.scalars(query.offset((page-1)*page_size).limit(page_size)).all()
    return {"items": [{"student_id": s.id, "roll_number": s.roll_number, "student_name": s.name, "department": s.department, "batch": s.batch, "section": s.section} for s in rows], "page": page, "page_size": page_size, "total": total, "total_pages": max(1,(total+page_size-1)//page_size)}


@router.get("/teachers")
def list_teachers(q: str | None = None, page: int = 1, page_size: int = 50, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    query = select(Teacher).order_by(Teacher.name.asc())
    if q:
        needle=f"%{q.strip().lower()}%"
        query=query.where(__import__('sqlalchemy').or_(Teacher.id.ilike(needle), Teacher.name.ilike(needle), Teacher.department.ilike(needle), Teacher.role.ilike(needle)))
    total=db.scalar(select(__import__('sqlalchemy').func.count()).select_from(query.subquery())) or 0
    page=max(1,page); page_size=max(1,min(page_size,100))
    rows=db.scalars(query.offset((page-1)*page_size).limit(page_size)).all()
    return {"items":[{"teacher_id":t.id,"teacher_name":t.name,"role":t.role,"department":t.department,"email":t.email} for t in rows],"page":page,"page_size":page_size,"total":total,"total_pages":max(1,(total+page_size-1)//page_size)}


@router.get("/config")
def get_config(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    settings = {setting.key: setting.value for setting in db.query(SystemSetting).all()}
    return {"gpa_threshold": settings.get("gpa_threshold", 7.0), "attendance_threshold": settings.get("attendance_threshold", 75.0)}


@router.put("/config")
def update_config(payload: ThresholdConfig, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    values = payload.model_dump()
    for key, value in values.items():
        setting = db.get(SystemSetting, key)
        if setting:
            setting.value = value
        else:
            db.add(SystemSetting(key=key, value=value, description=f"{key.replace('_', ' ').title()}"))
    record_audit(db, action="SYSTEM_CONFIG_UPDATED", actor=user, resource_type="system_setting", details={"keys": sorted(values.keys())})
    db.commit()
    return values

@router.get("/audit-logs")
def audit_logs(q: str | None = None, page: int = 1, page_size: int = 25, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    from app.models.domain import AuditLog
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if q:
        needle = f"%{q.strip().lower()}%"
        query = query.where(or_(AuditLog.action.ilike(needle), AuditLog.resource_type.ilike(needle), AuditLog.resource_id.ilike(needle), AuditLog.actor_id.ilike(needle)))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    page=max(1,page); page_size=max(1,min(page_size,100))
    rows = db.scalars(query.offset((page-1)*page_size).limit(page_size)).all()
    return {"items":[{"id":r.id,"actor_id":r.actor_id,"action":r.action,"resource_type":r.resource_type,"resource_id":r.resource_id,"ip_address":r.ip_address,"details":r.details or {},"created_at":r.created_at.isoformat() if r.created_at else None} for r in rows],"total":total,"page":page,"page_size":page_size,"total_pages":max(1,(total+page_size-1)//page_size)}

@router.get("/case-summary")
def case_summary(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    from app.models.domain import AlertIntervention, StudentCase
    from app.services.alerts import OPEN_STATUSES
    alerts = db.scalars(select(AlertIntervention)).all()
    cases = db.scalars(select(StudentCase)).all()
    open_cases = {c.student_id for c in cases if c.status == "OPEN"}
    completed_cases = {c.student_id for c in cases if c.status == "COMPLETED"}
    open_work_items = sum(a.status in {"NEW","ACKNOWLEDGED","ACTION_TAKEN","FOLLOW_UP"} for a in alerts)
    return {
        "open_cases": len(open_cases),
        "open_work_items": open_work_items,
        "completed_cases": len(completed_cases),
        "resolution_rate": round(len(completed_cases) / max(1, len(completed_cases) + len(open_cases)) * 100, 1),
    }
