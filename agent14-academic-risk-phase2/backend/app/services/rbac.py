from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Assignment, Student, User


class Role(str, Enum):
    MENTOR = "mentor"
    HOD = "hod"
    DEAN = "dean"
    ADMIN = "admin"


def can_view_support_attention_risk(role: str | Role) -> bool:
    return str(role) in {Role.MENTOR.value, Role.HOD.value, Role.DEAN.value}


def can_access_student(db: Session, user: User, student_id: str) -> bool:
    if user.role in (Role.DEAN.value, Role.ADMIN.value):
        return True
    if user.role == Role.MENTOR.value:
        return db.scalar(select(Assignment.id).where(Assignment.teacher_id == user.id, Assignment.student_id == student_id)) is not None
    if user.role == Role.HOD.value:
        return db.scalar(select(Student.id).where(Student.id == student_id, Student.department == user.department)) is not None
    return False


def scoped_student_ids(db: Session, user: User) -> list[str]:
    if user.role in (Role.DEAN.value, Role.ADMIN.value):
        return list(db.scalars(select(Student.id)).all())
    if user.role == Role.MENTOR.value:
        return list(db.scalars(select(Assignment.student_id).where(Assignment.teacher_id == user.id)).all())
    if user.role == Role.HOD.value:
        return list(db.scalars(select(Student.id).where(Student.department == user.department)).all())
    return []
