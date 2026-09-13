"""Phase 3 backend regression tests.

Requires backend dependencies to be installed. Run from project root:
    python scripts/test_phase3_api.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{BACKEND / 'phase3_test.db'}")
os.environ.setdefault("JWT_SECRET", "phase3-test-secret-change-me")

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
            def hash(self, password): return f"hashed:{password}"
            def verify(self, password, stored): return stored == f"hashed:{password}" or stored == password
        context.CryptContext = CryptContext
        sys.modules["passlib"] = passlib
        sys.modules["passlib.context"] = context

install_test_auth_stubs()

from app.main import app  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.domain import Assignment, RiskPrediction, Student  # noqa: E402


def login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return response.json()["token"]


def main() -> None:
    with TestClient(app) as client:
        assert client.get("/api/health").json()["database"] == "connected"
        mentor_token = login(client, "mentor.one.cse@vignan.ac.in")
        hod_token = login(client, "hod.cse@vignan.ac.in")
        admin_token = login(client, "admin@vignan.ac.in")

        with SessionLocal() as db:
            mentor_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == "T001").first()[0]
            other_mentor_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == "T002").first()[0]
            
        headers = {"Authorization": f"Bearer {mentor_token}"}
        response = client.get(f"/api/predictions/student/{mentor_student}", headers=headers)
        response.raise_for_status()
        data = response.json()
        assert len(data["risks"]["course_failure"]) == 5
        assert "priority_score" in data["risks"]["course_failure"][0]
        assert "intervenability_score" in data["risks"]["course_failure"][0]

        assert client.get(f"/api/predictions/student/{other_mentor_student}", headers=headers).status_code == 403
        assert client.get("/api/admin/config", headers=headers).status_code == 403
        assert client.get("/api/admin/config", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200

        with SessionLocal() as db:
            assert db.query(RiskPrediction).count() >= 9

    print("PHASE 3 API TESTS PASSED")


if __name__ == "__main__":
    main()
