from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Student, SystemSetting, Teacher, User
from app.services.auth import require_roles

router = APIRouter()


class ThresholdConfig(BaseModel):
    gpa_threshold: float = Field(ge=0, le=10)
    attendance_threshold: float = Field(ge=0, le=100)


@router.get("/students")
def list_students(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    students = db.scalars(select(Student)).all()
    return {"items": [{"student_id": student.id, "student_name": student.name, "department": student.department, "batch": student.batch, "section": student.section} for student in students]}


@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    teachers = db.scalars(select(Teacher)).all()
    return {"items": [{"teacher_id": teacher.id, "teacher_name": teacher.name, "role": teacher.role, "department": teacher.department, "email": teacher.email} for teacher in teachers]}


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
    db.commit()
    return values
