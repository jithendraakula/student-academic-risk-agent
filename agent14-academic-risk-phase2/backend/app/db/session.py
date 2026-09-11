import csv
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.domain import (
    AcademicReference, AlertIntervention, Assignment, CourseFeature,
    HistoricalOutcome, SemesterFeature, Student, SystemSetting, Teacher, User, Base,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'agent14.db'}")
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _read_csv(filename: str) -> list[dict]:
    with (PROJECT_DIR / "data" / "processed" / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _as_bool(value):
    return value in (True, "True", "true", "1", 1)


def _as_int(value):
    if value in (None, "", "None"):
        return None
    return int(float(value))


def seed_database(db) -> None:
    from app.services.auth import hash_password

    if db.query(Student).first():
        for user in db.query(User).all():
            if user.password_hash == "demo":
                user.password_hash = hash_password("demo")
        db.commit()
        if not db.get(SystemSetting, "gpa_threshold"):
            db.add_all([
                SystemSetting(key="gpa_threshold", value=7.0, description="GPA risk threshold"),
                SystemSetting(key="attendance_threshold", value=75.0, description="Attendance shortage threshold"),
            ])
            db.commit()
        return

    students = _read_csv("students.csv")
    teachers = _read_csv("teachers.csv")
    assignments = _read_csv("assignments.csv")
    references = _read_csv("academic_reference_data.csv")
    semester = _read_csv("student_semester_features.csv")
    courses = _read_csv("student_course_features.csv")
    historical = _read_csv("historical_outcomes.csv")
    alerts = _read_csv("alerts_interventions.csv")

    db.add_all([Teacher(id=row["teacher_id"], name=row["teacher_name"], role=row["role"], department=row["department"] or None, email=row["email"]) for row in teachers])
    db.add_all([Student(id=row["student_id"], name=row["student_name"], department=row["department"], program=row["program"], batch=row["batch"], section=row["section"], academic_year=row["academic_year"], current_semester=_as_int(row["current_semester"])) for row in students])
    db.add_all([Assignment(id=row["assignment_id"], student_id=row["student_id"], teacher_id=row["teacher_id"], academic_year=row["academic_year"], semester=_as_int(row["semester"]), assignment_type=row["assignment_type"]) for row in assignments])
    db.add_all([AcademicReference(data=row) for row in references])
    db.add_all([SemesterFeature(student_id=row["student_id"], semester=_as_int(row["semester"]), data=row) for row in semester])
    db.add_all([CourseFeature(student_id=row["student_id"], course_id=row["course_id"], semester=_as_int(row["semester"]), data=row) for row in courses])
    db.add_all([HistoricalOutcome(student_id=row["student_id"], semester=_as_int(row["semester"]), data=row) for row in historical])
    db.add_all([AlertIntervention(id=row["alert_id"], student_id=row["student_id"], teacher_id=row["teacher_id"], risk_type=row["risk_type"], risk_score=float(row["risk_score"]), priority_score=float(row["priority_score"]), status=row["alert_status"], data=row) for row in alerts])

    demo_users = [
        User(id="T001", email="mentor1@vignan.ac.in", name="Mentor One", role="mentor", department="DEPT_CSE", password_hash=hash_password("demo")),
        User(id="T002", email="mentor2@vignan.ac.in", name="Mentor Two", role="mentor", department="DEPT_CSE", password_hash=hash_password("demo")),
        User(id="H001", email="hod.cse@vignan.ac.in", name="HOD CSE", role="hod", department="DEPT_CSE", password_hash=hash_password("demo")),
        User(id="D001", email="dean@vignan.ac.in", name="Dean", role="dean", password_hash=hash_password("demo")),
        User(id="A001", email="admin@vignan.ac.in", name="Admin", role="admin", password_hash=hash_password("demo")),
    ]
    db.add_all(demo_users)
    db.add_all([
        SystemSetting(key="gpa_threshold", value=7.0, description="GPA risk threshold"),
        SystemSetting(key="attendance_threshold", value=75.0, description="Attendance shortage threshold"),
    ])
    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
