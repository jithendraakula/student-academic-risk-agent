"""Phase 7 Dean Workspace regression tests."""
from __future__ import annotations
import base64
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase7_test.db'}"
os.environ["JWT_SECRET"] = "phase7-test-secret"


def install_test_auth_stubs():
    if "jose" not in sys.modules:
        jose = types.ModuleType("jose")
        jose.JWTError = type("JWTError", (Exception,), {})
        class _JWT:
            @staticmethod
            def encode(payload, secret, algorithm=None):
                return base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode()
            @staticmethod
            def decode(token, secret, algorithms=None):
                return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        jose.jwt = _JWT
        sys.modules["jose"] = jose
    if "passlib.context" not in sys.modules:
        passlib = types.ModuleType("passlib")
        context = types.ModuleType("passlib.context")
        class CryptContext:
            def __init__(self, *args, **kwargs): pass
            def hash(self, password): return str(password)
            def verify(self, password, stored): return str(password) == str(stored)
        context.CryptContext = CryptContext
        sys.modules["passlib"] = passlib
        sys.modules["passlib.context"] = context

install_test_auth_stubs()
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.domain import RiskPrediction, Student


def login(client, email):
    r = client.post('/api/auth/login', json={'email': email, 'password': 'demo'})
    r.raise_for_status()
    return {'Authorization': f"Bearer {r.json()['token']}"}


def main():
    with TestClient(app) as client:
        dean = login(client, 'dean@vignan.ac.in')
        mentor = login(client, 'mentor1@vignan.ac.in')
        hod = login(client, 'hod.cse@vignan.ac.in')
        admin = login(client, 'admin@vignan.ac.in')

        summary = client.get('/api/dean/summary', headers=dean)
        summary.raise_for_status()
        s = summary.json()
        assert s['total_students'] > 0
        assert s['departments'] >= 1
        assert s['critical_students'] <= s['total_students']
        assert s['students_needing_action'] <= s['total_students']
        assert s['risk_source'] == 'risk_predictions'
        assert len(s['risk_distribution']) == 5
        assert any(item['risk_type'] == 'discontinuation' for item in s['risk_distribution'])

        comparison = client.get('/api/dean/department-comparison', headers=dean)
        comparison.raise_for_status()
        rows = comparison.json()['items']
        assert rows
        assert sum(row['total_students'] for row in rows) == s['total_students']
        assert all(row['critical_students'] <= row['total_students'] for row in rows)
        assert all(row['students_needing_action'] <= row['total_students'] for row in rows)
        assert all('risk_counts' in row and len(row['risk_counts']) == 5 for row in rows)

        heatmap = client.get('/api/dean/risk-heatmap', headers=dean)
        heatmap.raise_for_status()
        heat_rows = heatmap.json()['items']
        assert {r['department'] for r in heat_rows} == {r['department'] for r in rows}
        assert all(0 <= r['attendance_shortage'] <= 100 for r in heat_rows)
        assert all(0 <= r['course_failure'] <= 100 for r in heat_rows)
        assert all(0 <= r['discontinuation'] <= 100 for r in heat_rows)

        queue = client.get('/api/dean/priority-queue?limit=7', headers=dean)
        queue.raise_for_status()
        q = queue.json()
        assert len(q['items']) <= 7
        assert q['total_needing_action'] >= len(q['items'])
        assert all(row['priority_score'] >= 60 or row['risk_level'] == 'CRITICAL' for row in q['items'])
        assert all('discontinuation' in row['risk_types'] or row['risk_types'] for row in q['items'])

        with SessionLocal() as db:
            dept = db.query(Student.department).distinct().first()[0]
            ece = db.query(Student.id).filter(Student.department != 'DEPT_CSE').first()
            assert ece is not None
            before = db.query(RiskPrediction).count()

        students = client.get(f'/api/dean/departments/{dept}/students', headers=dean)
        students.raise_for_status()
        d = students.json()
        assert d['department'] == dept
        assert d['items']
        assert all(row['department'] == dept for row in d['items'])
        assert all('priority_score' in row and 'risk_types' in row for row in d['items'])

        assert client.get('/api/dean/departments/NOT_A_REAL_DEPARTMENT/students', headers=dean).status_code == 404
        assert client.get('/api/dean/summary', headers=mentor).status_code == 403
        assert client.get('/api/dean/summary', headers=hod).status_code == 403
        assert client.get('/api/dean/summary', headers=admin).status_code == 403

        # Dean can access a college-wide student profile through the shared RBAC policy.
        profile = client.get(f'/api/predictions/student/{ece[0]}', headers=dean)
        profile.raise_for_status()
        assert 'risks' in profile.json()

        with SessionLocal() as db:
            after = db.query(RiskPrediction).count()
        assert after >= before

    print('PHASE 7 DEAN TESTS PASSED')

if __name__ == '__main__':
    main()
