"""Phase 4 canonical-risk/priority/alert regression tests.

The offline runner used to build the deliverable may not have python-jose/passlib,
so this script installs tiny test-only auth stubs before importing the app. In a
normal developer environment, the real packages from backend/requirements.txt
are used instead.
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
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase4_test.db'}"
os.environ["JWT_SECRET"] = "phase4-test-secret"


def install_test_auth_stubs() -> None:
    if "jose" not in sys.modules:
        jose = types.ModuleType("jose")
        jose.JWTError = type("JWTError", (Exception,), {})

        class _JWT:
            @staticmethod
            def encode(payload, secret, algorithm=None):
                raw = json.dumps(payload, default=str).encode()
                return base64.urlsafe_b64encode(raw).decode()

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

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.domain import AlertIntervention, Assignment, RiskPrediction, Student  # noqa: E402
from app.services.risk_engine import normalize_risk_type, should_create_alert  # noqa: E402


def login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return response.json()["token"]


def main() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        assert health.json()["database"] == "connected"

        mentor1 = {"Authorization": f"Bearer {login(client, 'mentor.one.cse@vignan.ac.in')}"}
        mentor2 = {"Authorization": f"Bearer {login(client, 'mentor.two.cse@vignan.ac.in')}"}
        hod = {"Authorization": f"Bearer {login(client, 'hod.cse@vignan.ac.in')}"}
        dean = {"Authorization": f"Bearer {login(client, 'dean@vignan.ac.in')}"}

        watch = client.get("/api/mentor/watchlist", headers=mentor1)
        watch.raise_for_status()
        watch_data = watch.json()
        assert watch_data["risk_source"] == "risk_predictions"
        assert watch_data["open_alerts"] == len(watch_data["items"])
        assert all(item["risk_type"] in {"course_failure", "backlog", "gpa_threshold", "attendance_shortage", "discontinuation"} for item in watch_data["items"])
        assert all(item["source"] == "risk_predictions" for item in watch_data["items"])
        assert all(item["priority_score"] >= 60 or item["risk_level"] == "CRITICAL" for item in watch_data["items"])

        # Mentor isolation remains assignment-scoped.
        with SessionLocal() as db:
            m1_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == "T001").first()[0]
            m2_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == "T002").first()[0]
        assert client.get(f"/api/predictions/student/{m2_student}", headers=mentor1).status_code == 403
        
        # HOD and Dean consume the same current-risk store and expose canonical labels.
        comparison = client.get("/api/hod/mentor-comparison", headers=hod)
        comparison.raise_for_status()
        rows = comparison.json()["items"]
        assert comparison.json()["risk_source"] == "risk_predictions"
        assert rows and all("students_needing_action" in row for row in rows)

        dean_comparison = client.get("/api/dean/department-comparison", headers=dean)
        dean_comparison.raise_for_status()
        assert dean_comparison.json()["risk_source"] == "risk_predictions"
        heatmap = client.get("/api/dean/risk-heatmap", headers=dean)
        heatmap.raise_for_status()
        assert heatmap.json()["risk_source"] == "risk_predictions"

        with SessionLocal() as db:
            prediction_count = db.query(RiskPrediction).count()
            assert prediction_count == 500 * 9, prediction_count
            alerts = db.query(AlertIntervention).all()
            assert alerts, "canonical alert projection should not be empty"
            assert all((a.data or {}).get("source") == "risk_predictions" for a in alerts)
            assert all(normalize_risk_type(a.risk_type) in {"course_failure", "backlog", "gpa_threshold", "attendance_shortage", "discontinuation"} for a in alerts)

        # The intervention lifecycle updates the canonical alert record without
        # changing its risk/priority source.
        first_alert = next(item for item in watch_data["items"] if item["status"] == "NEW")
        patched = client.patch(
            f"/api/interventions/{first_alert['alert_id']}",
            headers=mentor1,
            json={"status": "ACKNOWLEDGED", "notes": "Phase 4 regression test"},
        )
        patched.raise_for_status()
        assert patched.json()["status"] == "ACKNOWLEDGED"
        assert patched.json()["data"]["source"] == "risk_predictions"

        # Canonical policy helpers are deterministic and legacy names normalize.
        assert normalize_risk_type("attendance") == "attendance_shortage"
        assert normalize_risk_type("support_attention") == "discontinuation"
        assert should_create_alert(40, "LOW", 61)
        assert should_create_alert(20, "CRITICAL", 20)
        assert not should_create_alert(40, "MODERATE", 59.9)

    print("PHASE 4 API TESTS PASSED")


if __name__ == "__main__":
    main()
