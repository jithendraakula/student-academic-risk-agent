import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.domain import Assignment, Base, CourseFeature, AcademicObservation, SemesterFeature, Student, User
from app.services import risk as risk_service
from app.services.risk import build_student_risk_profile


def fake_predict(student_data, course_data):
    course_id = course_data[0].get('course_id', 'CSE501') if course_data else 'CSE501'
    return {
        'risks': {
            'course_failure': [{'course_id': course_id, 'course_name': 'Operating Systems', 'risk_probability': 0.12, 'risk_score': 12.0, 'risk_level': 'LOW', 'confidence': 'HIGH', 'decision_threshold': 0.1, 'top_factors': []}],
            'backlog': {'risk_probability': 0.18, 'risk_score': 18.0, 'risk_level': 'LOW', 'confidence': 'MEDIUM', 'decision_threshold': 0.12, 'top_factors': []},
            'gpa_threshold': {'risk_probability': 0.31, 'risk_score': 31.0, 'risk_level': 'MODERATE', 'confidence': 'MEDIUM', 'decision_threshold': 0.21, 'top_factors': []},
            'attendance_shortage': {'risk_probability': 0.42, 'risk_score': 42.0, 'risk_level': 'HIGH', 'confidence': 'HIGH', 'decision_threshold': 0.23, 'top_factors': []},
            'discontinuation': {'risk_probability': 0.10, 'risk_score': 10.0, 'risk_level': 'LOW', 'confidence': 'HIGH', 'decision_threshold': 0.1, 'top_factors': []},
        }
    }


def main():
    db_path = Path(tempfile.gettempdir()) / 'agent14_r15_context.db'
    if db_path.exists(): db_path.unlink()
    engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    risk_service._predict = fake_predict

    with Session() as db:
        student = Student(id='SCTX01', name='Context Test Student', department='DEPT_CSE', program='B.Tech CSE', batch='2024', section='CSE-A', academic_year='2026-27', current_semester=5)
        user = User(id='TCTX01', email='ctx@example.com', name='Mentor Context', role='mentor', department='DEPT_CSE', password_hash='x')
        assignment = Assignment(id='ACTX01', student_id=student.id, teacher_id=user.id, academic_year='2026-27', semester=5, assignment_type='mentor')
        semester = SemesterFeature(student_id=student.id, semester=5, data={'student_id':'SCTX01','semester':5,'checkpoint_week':6,'current_gpa':6.8,'current_cgpa':6.9,'current_attendance_percentage':67.0,'current_backlog_count':1,'internal_marks_average':54.0,'recent_absence_rate':0.22,'projected_final_attendance':69.0})
        course = CourseFeature(student_id=student.id, course_id='CSE501', semester=5, data={'course_id':'CSE501','course_name':'Operating Systems','internal_marks':54.0,'midterm_marks':51.0,'quiz_average':58.0,'assignment_average':62.0,'practical_marks':60.0,'course_attendance_percentage':67.0,'assignment_completion_rate':0.7})
        observations = [
            AcademicObservation(id='OBSCTX1', student_id=student.id, observed_on='2026-09-01', category='health_related', observation_text='Absent for three consecutive days due to fever; mentor requested a check-in after return.', source_role='mentor', follow_up_required=True, status='OPEN'),
            AcademicObservation(id='OBSCTX2', student_id=student.id, observed_on='2026-09-02', category='assessment', observation_text='Missed one internal assessment and two quiz attempts; subject support is being considered before the next checkpoint.', source_role='mentor', follow_up_required=True, status='OPEN'),
        ]
        db.add_all([student, user, assignment, semester, course, *observations])
        db.commit()
        profile = build_student_risk_profile(db, student.id, user)
        ctx = profile['academic_context']
        assert ctx['observation_count'] == 2
        assert ctx['active_follow_up_count'] == 2
        intents = {row['intent'] for row in ctx['observations']}
        assert {'health_recovery', 'assessment_support'} <= intents
        assert ctx['primary_action_path']['recommended_action']
        print('R1.5 database/profile integration: PASS')

    db_path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
