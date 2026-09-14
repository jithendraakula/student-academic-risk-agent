"""Phase 5 Mentor Workspace regression tests."""
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
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase5_test.db'}"
os.environ["JWT_SECRET"] = "phase5-test-secret"


def install_test_auth_stubs() -> None:
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

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.domain import Assignment  # noqa: E402


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['token']}"}


def main() -> None:
    with TestClient(app) as client:
        mentor1 = login(client, "mentor.one.cse@vignan.ac.in")
        mentor2 = login(client, "mentor.two.cse@vignan.ac.in")
        hod = login(client, "hod.cse@vignan.ac.in")

        summary = client.get("/api/mentor/summary", headers=mentor1)
        summary.raise_for_status()
        summary_data = summary.json()
        assert summary_data["risk_source"] == "risk_predictions"
        assert summary_data["assigned_students"] > 0
        assert summary_data["critical_students"] <= summary_data["assigned_students"]
        assert summary_data["students_needing_action"] <= summary_data["assigned_students"]

        students = client.get("/api/mentor/students", headers=mentor1)
        students.raise_for_status()
        data = students.json()
        assert data["assigned_students"] == summary_data["assigned_students"]
        assert len(data["items"]) == data["returned_students"] == summary_data["assigned_students"]
        assert all(row["student_id"] for row in data["items"])
        assert all(isinstance(row["risk_scores"], dict) for row in data["items"])

        action_only = client.get("/api/mentor/students?needs_action=true", headers=mentor1)
        action_only.raise_for_status()
        assert all(row["needs_action"] for row in action_only.json()["items"])
        assert action_only.json()["returned_students"] == summary_data["students_needing_action"]

        support = client.get("/api/mentor/students?risk_type=discontinuation", headers=mentor1)
        support.raise_for_status()
        assert all("discontinuation" in row["risk_types"] for row in support.json()["items"])

        with SessionLocal() as db:
            m1_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == "T001").first()[0]
            m2_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == "T002").first()[0]

        detail = client.get(f"/api/mentor/students/{m1_student}", headers=mentor1)
        detail.raise_for_status()
        assert detail.json()["student_id"] == m1_student
        assert detail.json()["student_id"] in {row["student_id"] for row in data["items"]}

        # Assignment-scoped mentor isolation.
        assert client.get(f"/api/mentor/students/{m2_student}", headers=mentor1).status_code == 404
        assert client.get(f"/api/predictions/student/{m2_student}", headers=mentor1).status_code == 403
        assert client.get("/api/mentor/students", headers=hod).status_code == 403

        # Search and severity filters remain valid and bounded by mentor scope.
        searched = client.get(f"/api/mentor/students?q={m1_student}", headers=mentor1)
        searched.raise_for_status()
        assert searched.json()["returned_students"] >= 1
        assert m1_student in {row["student_id"] for row in searched.json()["items"]}

        high = client.get("/api/mentor/students?severity=HIGH", headers=mentor1)
        high.raise_for_status()
        assert all(row["risk_level"] in {"HIGH", "CRITICAL"} for row in high.json()["items"])

        # Existing alert lifecycle remains compatible with the mentor workflow.
        first_alert = next((alert for row in data["items"] for alert in row["alerts"]), None)
        assert first_alert is not None, "Mentor should have at least one active alert in demo data"
        acknowledged = client.post(f"/api/mentor/alerts/{first_alert['alert_id']}/acknowledge", headers=mentor1)
        acknowledged.raise_for_status()
        assert acknowledged.json()["status"] == "ACKNOWLEDGED"

        updated = client.patch(
            f"/api/interventions/{first_alert['alert_id']}",
            headers=mentor1,
            json={"status": "FOLLOW_UP", "notes": "Phase 5 mentor workflow", "follow_up_date": "2026-09-20"},
        )
        updated.raise_for_status()
        assert updated.json()["status"] == "FOLLOW_UP"
        assert updated.json()["data"]["source"] == "risk_predictions"
        assert updated.json()["data"]["follow_up_date"] == "2026-09-20"

    print("PHASE 5 MENTOR TESTS PASSED")


if __name__ == "__main__":
    main()
