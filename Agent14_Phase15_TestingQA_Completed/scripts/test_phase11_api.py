"""Phase 11 HOD/Dean AI Analyst regression tests.

Live providers are not called. A deterministic provider is injected so this test
can validate role scope, canonical context, response parsing, and configuration
behavior without network access.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase11_test.db'}"
os.environ["JWT_SECRET"] = "phase11-test-secret"
os.environ["AI_PROVIDER"] = "gemini"
os.environ["AI_API_KEY"] = "test-key"
os.environ["AI_MODEL"] = "gemini-test-model"


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
            def __init__(self, *args, **kwargs):
                pass

            def hash(self, password):
                return str(password)

            def verify(self, password, stored):
                return str(password) == str(stored)

        context.CryptContext = CryptContext
        sys.modules["passlib"] = passlib
        sys.modules["passlib.context"] = context


install_test_auth_stubs()

from fastapi.testclient import TestClient
from app.main import app
from app.models.domain import RiskPrediction
from app.db.session import SessionLocal
import app.services.ai as ai_service
import app.services.institutional_ai as institutional_ai


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['token']}"}


def main():
    db_path = BACKEND / "phase11_test.db"
    original_call = ai_service._call_provider
    original_key = ai_service.AI_API_KEY
    calls = []
    fake_response = {
        "title": "Grounded institutional review",
        "executive_summary": "The supplied canonical metrics indicate the main areas needing coordinated support.",
        "key_findings": ["Priority is concentrated in a subset of monitored students.", "Risk mix should guide targeted academic support."],
        "recommended_actions": ["Review mentor coverage for the highest support demand.", "Schedule focused academic follow-ups."],
        "cautions": ["Support Attention is a support-only signal."],
    }

    def fake_call(messages):
        calls.append(messages)
        return json.dumps(fake_response), "gemini-test-model"

    try:
        ai_service._call_provider = fake_call
        with TestClient(app) as client:
            hod = login(client, "hod.cse@vignan.ac.in")
            dean = login(client, "dean@vignan.ac.in")
            mentor = login(client, "mentor.one.cse@vignan.ac.in")
            admin = login(client, "admin@vignan.ac.in")

            before_predictions = None
            with SessionLocal() as db:
                before_predictions = db.query(RiskPrediction).count()

            # First analysis may materialize missing canonical current predictions. Capture the
            # resulting canonical count, then ensure subsequent AI calls do not mutate it.
            # HOD: all permitted department-analysis intents.
            for intent in ("executive_summary", "mentor_workload", "intervention_coverage"):
                response = client.post("/api/institutional-ai/analyze", json={"intent": intent}, headers=hod)
                response.raise_for_status()
                data = response.json()
                assert data["role"] == "hod"
                assert data["scope"] == "DEPT_CSE"
                assert data["grounded"] is True
                assert data["intent"] == intent
                assert data["source_snapshot"]["risk_source"] == "RiskPrediction + canonical priority engine"
                assert data["key_findings"]

            # Dean: institution-level intents.
            for intent in ("executive_summary", "risk_analysis", "intervention_coverage", "priority_review"):
                response = client.post("/api/institutional-ai/analyze", json={"intent": intent, "focus": "attendance recovery"}, headers=dean)
                response.raise_for_status()
                data = response.json()
                assert data["role"] == "dean"
                assert data["scope"] == "institution"
                assert data["grounded"] is True
                assert data["intent"] == intent

            # Role guard: mentor/admin cannot call the institutional endpoint.
            assert client.post("/api/institutional-ai/analyze", json={"intent": "executive_summary"}, headers=mentor).status_code == 403
            assert client.post("/api/institutional-ai/analyze", json={"intent": "executive_summary"}, headers=admin).status_code == 403

            # Invalid intent is rejected.
            assert client.post("/api/institutional-ai/analyze", json={"intent": "made_up"}, headers=dean).status_code == 422

            # Inspect the provider context: role scope and canonical source must be present;
            # Dean context should not contain student names.
            assert calls, "provider was never invoked"
            last_call_text = "\n".join(message["content"] for message in calls[-1])
            assert "RiskPrediction + canonical priority engine" in last_call_text
            assert '"scope":{"institution":"CSE"}' in last_call_text
            assert "mentor.one.cse@vignan.ac.in" not in last_call_text
            assert "Mentor One" not in last_call_text or "mentor_name" in last_call_text

            # The first scoped analyses may materialize missing canonical predictions.
            # Once the canonical store is warm, repeated AI calls must not change it.
            with SessionLocal() as db:
                before_predictions = db.query(RiskPrediction).count()
            for role_headers in (hod, dean):
                repeat = client.post("/api/institutional-ai/analyze", json={"intent": "executive_summary"}, headers=role_headers)
                repeat.raise_for_status()
            with SessionLocal() as db:
                after_predictions = db.query(RiskPrediction).count()
            assert after_predictions == before_predictions

            # Missing API key must produce 503 rather than a fabricated answer.
            ai_service._call_provider = original_call
            ai_service.AI_API_KEY = ""
            missing = client.post("/api/institutional-ai/analyze", json={"intent": "executive_summary"}, headers=dean)
            assert missing.status_code == 503
            assert "AI provider is not configured" in missing.json()["detail"]

        print("PHASE 11 INSTITUTIONAL AI TESTS PASSED")
    finally:
        ai_service._call_provider = original_call
        ai_service.AI_API_KEY = original_key
        if db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    main()
