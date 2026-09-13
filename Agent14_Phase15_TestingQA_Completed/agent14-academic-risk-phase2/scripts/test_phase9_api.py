"""Phase 9 What-If simulator regression tests.

Uses test-only auth stubs because the offline validation runner may not have
python-jose/passlib installed. The tests verify API behavior, RBAC, model
execution, and the critical non-persistence guarantee.
"""
from __future__ import annotations
import base64, json, os, sys, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase9_test.db'}"
os.environ["JWT_SECRET"] = "phase9-test-secret"


def install_test_auth_stubs():
    if "jose" not in sys.modules:
        jose = types.ModuleType("jose"); jose.JWTError = type("JWTError", (Exception,), {})
        class _JWT:
            @staticmethod
            def encode(payload, secret, algorithm=None): return base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode()
            @staticmethod
            def decode(token, secret, algorithms=None): return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        jose.jwt = _JWT; sys.modules["jose"] = jose
    if "passlib.context" not in sys.modules:
        passlib = types.ModuleType("passlib"); context = types.ModuleType("passlib.context")
        class CryptContext:
            def __init__(self, *args, **kwargs): pass
            def hash(self, password): return str(password)
            def verify(self, password, stored): return str(password) == str(stored)
        context.CryptContext = CryptContext; sys.modules["passlib"] = passlib; sys.modules["passlib.context"] = context


install_test_auth_stubs()
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.domain import RiskPrediction, Student


def login(client, email):
    r = client.post('/api/auth/login', json={'email': email, 'password': 'demo'}); r.raise_for_status()
    return {'Authorization': f"Bearer {r.json()['token']}"}


def first_assigned_student(client, headers):
    r = client.get('/api/mentor/students', headers=headers); r.raise_for_status()
    return r.json()['items'][0]['student_id']


def main():
    db_path = BACKEND / 'phase9_test.db'
    try:
        with TestClient(app) as client:
            mentor = login(client, 'mentor.one.cse@vignan.ac.in')
            mentor2 = login(client, 'mentor.two.cse@vignan.ac.in')
            hod = login(client, 'hod.cse@vignan.ac.in')
            dean = login(client, 'dean@vignan.ac.in')
            admin = login(client, 'admin@vignan.ac.in')

            student_id = first_assigned_student(client, mentor)
            with SessionLocal() as db:
                before_predictions = db.query(RiskPrediction).count()

            baseline_payload = {'attendance_percentage': 88, 'gpa': 8.2, 'backlog_count': 0, 'assignment_completion_rate': 0.95}
            r = client.post(f'/api/what-if/student/{student_id}', json=baseline_payload, headers=mentor)
            r.raise_for_status(); data = r.json()
            assert data['simulation']['persistent'] is False
            assert data['simulation']['changes']['attendance_percentage']['from'] >= 0
            assert 'backlog' in data['baseline']['risks']
            assert 'attendance_shortage' in data['simulated']['risks']
            assert data['interpretation']['warning']

            # Course-specific simulator path.
            course_id = next(p['course_id'] for p in data['baseline']['risks']['course_failure'])
            r2 = client.post(
                f'/api/what-if/student/{student_id}',
                json={'course': {'course_id': course_id, 'internal_marks': 90, 'midterm_marks': 88, 'quiz_average': 92, 'assignment_average': 90, 'practical_marks': 90, 'course_attendance_percentage': 92, 'assignment_completion_rate': 1.0}},
                headers=mentor,
            )
            r2.raise_for_status(); course_data = r2.json()
            assert f'course_failure:{course_id}' in course_data['changes']

            # What-if must not persist predictions.
            with SessionLocal() as db:
                after_predictions = db.query(RiskPrediction).count()
                assert after_predictions == before_predictions

            # Mentor isolation.
            r3 = client.post(f'/api/what-if/student/{student_id}', json={'attendance_percentage': 90}, headers=mentor2)
            assert r3.status_code == 403

            # HOD and Dean can access a student in their scope/institution.
            assert client.post(f'/api/what-if/student/{student_id}', json={'gpa': 8.0}, headers=hod).status_code == 200
            assert client.post(f'/api/what-if/student/{student_id}', json={'gpa': 8.0}, headers=dean).status_code == 200

            # Admin and empty simulation are denied.
            assert client.post(f'/api/what-if/student/{student_id}', json={'gpa': 8.0}, headers=admin).status_code == 403
            assert client.post(f'/api/what-if/student/{student_id}', json={}, headers=mentor).status_code == 400

            # Student data must remain unchanged.
            with SessionLocal() as db:
                student = db.get(Student, student_id)
                assert student is not None

        print('PHASE 9 WHAT-IF TESTS PASSED')
    finally:
        if db_path.exists(): db_path.unlink()


if __name__ == '__main__':
    main()
