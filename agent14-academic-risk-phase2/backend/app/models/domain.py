from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    department: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(255))


class Student(Base):
    __tablename__ = "students"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(64), index=True)
    program: Mapped[str] = mapped_column(String(128))
    batch: Mapped[str] = mapped_column(String(32))
    section: Mapped[str] = mapped_column(String(16))
    academic_year: Mapped[str] = mapped_column(String(32))
    current_semester: Mapped[int] = mapped_column(Integer)


class Teacher(Base):
    __tablename__ = "teachers"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))
    department: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(32))
    semester: Mapped[int] = mapped_column(Integer)
    assignment_type: Mapped[str] = mapped_column(String(32))


class SemesterFeature(Base):
    __tablename__ = "semester_features"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    semester: Mapped[int] = mapped_column(Integer, index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class CourseFeature(Base):
    __tablename__ = "course_features"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[str] = mapped_column(String(32), index=True)
    semester: Mapped[int] = mapped_column(Integer, index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class HistoricalOutcome(Base):
    __tablename__ = "historical_outcomes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    semester: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class AcademicReference(Base):
    __tablename__ = "academic_reference_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class AlertIntervention(Base):
    __tablename__ = "alerts_interventions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), index=True)
    risk_type: Mapped[str] = mapped_column(String(64), index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    priority_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    intervention_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
