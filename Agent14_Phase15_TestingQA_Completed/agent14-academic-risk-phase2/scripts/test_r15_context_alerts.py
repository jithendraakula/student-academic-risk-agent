from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.domain import AcademicObservation, AlertIntervention, Assignment, Base, RiskPrediction, Student, User
from app.services.alerts import _context_for_alert


def main():
    path = Path(tempfile.gettempdir()) / 'agent14_r15_context_alerts.db'
    path.unlink(missing_ok=True)
    engine = create_engine(f'sqlite:///{path}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session() as db:
        db.add_all([
            Student(id='S1', name='Student One', department='DEPT_CSE', program='B.Tech CSE', batch='2024', section='CSE-A', academic_year='2026-27', current_semester=5),
            User(id='T1', email='t1@example.com', name='Mentor One', role='mentor', department='DEPT_CSE', password_hash='x'),
            Assignment(id='A1', student_id='S1', teacher_id='T1', academic_year='2026-27', semester=5, assignment_type='mentor'),
            AcademicObservation(id='O1', student_id='S1', observed_on='2026-09-01', category='health_related', observation_text='Absent for three consecutive days due to fever; mentor requested a check-in after return.', source_role='mentor', follow_up_required=True, status='OPEN'),
            AcademicObservation(id='O2', student_id='S1', observed_on='2026-09-02', category='assessment', observation_text='Missed one internal assessment and two quiz attempts; subject support is being considered before the next checkpoint.', source_role='mentor', follow_up_required=True, status='OPEN'),
        ])
        db.commit()
        assert _context_for_alert(db, 'S1', 'attendance_shortage')['intent'] == 'health_recovery'
        assert _context_for_alert(db, 'S1', 'course_failure')['intent'] == 'assessment_support'
        assert _context_for_alert(db, 'S1', 'backlog')['intent'] == 'assessment_support'
        assert _context_for_alert(db, 'S1', 'gpa_threshold')['intent'] == 'assessment_support'
        print('R1.5 alert-context routing tests: PASS')
    path.unlink(missing_ok=True)

if __name__ == '__main__':
    main()
