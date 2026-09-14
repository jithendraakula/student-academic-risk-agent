from pathlib import Path
import sys
import tempfile
import types

# Test-only auth stub: this offline runner does not have python-jose/passlib.
fake_auth = types.ModuleType("app.services.auth")
fake_auth.hash_password = lambda password: "test-hash"
sys.modules["app.services.auth"] = fake_auth

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.models.domain import Base, RiskPrediction, SemesterFeature, CourseFeature, User
from app.db.session import seed_database
from app.services.what_if import simulate_student
from app.schemas.what_if import WhatIfRequest


def main():
    path = Path(tempfile.gettempdir()) / 'agent14_r12_whatif_runtime.db'
    path.unlink(missing_ok=True)
    engine = create_engine(f'sqlite:///{path}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session() as db:
        seed_database(db)
        user = db.get(User, 'T001')
        before_predictions = db.scalar(select(func.count(RiskPrediction.id)))
        student = 'S0001'
        semester = db.scalars(select(SemesterFeature).where(SemesterFeature.student_id == student).order_by(SemesterFeature.semester.desc(), SemesterFeature.id.desc())).first()
        before_data = dict(semester.data)
        course = db.scalars(select(CourseFeature).where(CourseFeature.student_id == student, CourseFeature.semester == semester.semester).order_by(CourseFeature.id.asc())).first()
        payload = WhatIfRequest(assignment_completion_rate=0.95)
        result = simulate_student(db, student, user, payload)
        assert result['simulation']['persistent'] is False
        assert result['simulation']['scenario_summary']['mode'] == 'single_factor'
        assert result['simulation']['scenario_summary']['factors'] == ['assignment completion']
        after_predictions = db.scalar(select(func.count(RiskPrediction.id)))
        assert after_predictions == before_predictions, (before_predictions, after_predictions)
        db.refresh(semester)
        assert semester.data['assignment_completion_rate'] == before_data['assignment_completion_rate']
        assert semester.data['assessment_participation_rate'] == before_data['assessment_participation_rate']
        print('R12 runtime what-if persistence test: PASS')
    path.unlink(missing_ok=True)

if __name__ == '__main__':
    main()
