import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(__file__).with_name('test.db')}")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.domain import Base, Student, Teacher, Assignment, User, StudentCase, AlertIntervention
from app.services.cases import get_or_create_case
from app.services.interventions import complete_student_case


def setup_db():
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_case_can_be_created_and_completed_transactionally():
    SessionLocal = setup_db()
    with SessionLocal() as db:
        db.add_all([
            Student(id="S1", name="Test Student", department="DEPT_CSE", program="BTECH", batch="2027", section="A", academic_year="2026-27", current_semester=5),
            Teacher(id="T1", name="Mentor", role="mentor", department="DEPT_CSE", email="mentor@test.local"),
            User(id="T1", name="Mentor", role="mentor", department="DEPT_CSE", email="mentor@test.local", password_hash="x"),
            Assignment(id="AS1", student_id="S1", teacher_id="T1", academic_year="2026-27", semester=5, assignment_type="mentor"),
        ])
        db.commit()
        case = get_or_create_case(db, "S1")
        alert = AlertIntervention(id="A1", student_id="S1", case_id=case.id, teacher_id="T1", risk_type="attendance_shortage", risk_score=80, priority_score=90, status="NEW", data={"risk_level":"CRITICAL"})
        db.add(alert); db.commit()
        user = db.get(User, "T1")
        result = complete_student_case(db, "S1", user, action_category="ATTENDANCE_FOLLOW_UP", notes="Discussed recovery plan")
        assert result["status"] == "COMPLETED"
        assert db.get(AlertIntervention, "A1").status == "RESOLVED"
        assert db.scalar(select(StudentCase).where(StudentCase.id == case.id)).status == "COMPLETED"


def test_case_creation_is_reusable_while_open():
    SessionLocal = setup_db()
    with SessionLocal() as db:
        db.add(Student(id="S2", name="Test Student 2", department="DEPT_CSE", program="BTECH", batch="2027", section="A", academic_year="2026-27", current_semester=5)); db.commit()
        first = get_or_create_case(db, "S2")
        second = get_or_create_case(db, "S2")
        assert first.id == second.id
