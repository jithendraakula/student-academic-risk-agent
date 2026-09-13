"""Phase 10 Mentor AI Copilot regression tests.

The live provider is deliberately not called in CI/offline validation. The test
injects a deterministic provider response to validate endpoint wiring, grounding,
RBAC and What-If behavior. A separate configuration test confirms a missing key
returns 503 rather than fabricating AI output.
"""
from __future__ import annotations

import base64, json, os, sys, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase10_test.db'}"
os.environ["JWT_SECRET"] = "phase10-test-secret"
os.environ["AI_PROVIDER"] = "gemini"
os.environ["AI_API_KEY"] = "test-key"
os.environ["AI_MODEL"] = "gemini-test-model"


def install_test_auth_stubs():
    if "jose" not in sys.modules:
        jose = types.ModuleType("jose"); jose.JWTError = type("JWTError", (Exception,), {})
        class _JWT:
            @staticmethod
            def encode(payload, secret, algorithm=None):
                return base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode()
            @staticmethod
            def decode(token, secret, algorithms=None):
                return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
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
from app.models.domain import RiskPrediction
import app.services.ai as ai_service


def login(client, email):
    response = client.post('/api/auth/login', json={'email': email, 'password': 'demo'})
    response.raise_for_status()
    return {'Authorization': f"Bearer {response.json()['token']}"}


def main():
    db_path = BACKEND / 'phase10_test.db'
    original_call = ai_service._call_provider
    try:
        with TestClient(app) as client:
            mentor = login(client, 'mentor1@vignan.ac.in')
            mentor2 = login(client, 'mentor2@vignan.ac.in')
            admin = login(client, 'admin@vignan.ac.in')

            students = client.get('/api/mentor/students', headers=mentor)
            students.raise_for_status()
            student_id = students.json()['items'][0]['student_id']

            fake_response = {
                'explanation': 'The strongest supplied signals are attendance shortage and course-level failure risk.',
                'recommended_actions': ['Review attendance recovery plan', 'Schedule academic follow-up'],
                'priority_rationale': 'Priority is driven by canonical risk and intervention urgency.',
                'cautions': ['Use support signals only for supportive intervention.'],
            }
            ai_service._call_provider = lambda messages: (json.dumps(fake_response), 'gemini-test-model')

            risk = client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'risk_summary'}, headers=mentor)
            risk.raise_for_status(); data = risk.json()
            assert data['grounded'] is True
            assert data['provider'] == 'gemini'
            assert data['model'] == 'gemini-test-model'
            assert data['intent'] == 'risk_summary'
            assert data['recommended_actions']
            assert data['source_snapshot']['risk_source'] == 'RiskPrediction + canonical priority engine'

            plan = client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'intervention_plan', 'focus': 'attendance recovery'}, headers=mentor)
            plan.raise_for_status(); assert plan.json()['intent'] == 'intervention_plan'

            # What-if explanation accepts the same structured scenario and must remain non-persistent.
            with SessionLocal() as db:
                before = db.query(RiskPrediction).count()
            what_if = client.post(
                f'/api/mentor/ai/copilot/{student_id}',
                json={'intent': 'what_if_explanation', 'what_if': {'attendance_percentage': 90, 'gpa': 8.0}},
                headers=mentor,
            )
            what_if.raise_for_status(); wi = what_if.json()
            assert wi['intent'] == 'what_if_explanation'
            assert wi['source_snapshot']['what_if_persistent'] is False
            with SessionLocal() as db:
                after = db.query(RiskPrediction).count()
                assert after == before

            # Mentor isolation remains in force.
            forbidden = client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'risk_summary'}, headers=mentor2)
            assert forbidden.status_code == 403
            assert client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'risk_summary'}, headers=admin).status_code == 403

            # Invalid intent and missing what-if are rejected.
            assert client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'not_an_intent'}, headers=mentor).status_code == 422
            assert client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'what_if_explanation'}, headers=mentor).status_code == 400

            # Missing provider key must return 503; no fabricated fallback is allowed.
            ai_service._call_provider = original_call
            ai_service.AI_API_KEY = ''
            missing = client.post(f'/api/mentor/ai/copilot/{student_id}', json={'intent': 'risk_summary'}, headers=mentor)
            assert missing.status_code == 503
            assert 'AI provider is not configured' in missing.json()['detail']

        print('PHASE 10 AI COPILOT TESTS PASSED')
    finally:
        ai_service._call_provider = original_call
        if db_path.exists(): db_path.unlink()


if __name__ == '__main__':
    main()
