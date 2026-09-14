"""Phase 6 HOD Workspace regression tests."""
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
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase6_test.db'}"
os.environ["JWT_SECRET"] = "phase6-test-secret"


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
from app.models.domain import Assignment, RiskPrediction, Student, Teacher  # noqa: E402


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['token']}"}


def main() -> None:
    with TestClient(app) as client:
        hod = login(client, "hod.cse@vignan.ac.in")
        mentor = login(client, "mentor.one.cse@vignan.ac.in")
        dean = login(client, "dean@vignan.ac.in")

        summary = client.get("/api/hod/summary", headers=hod)
        summary.raise_for_status()
        s = summary.json()
        assert s["department"] == "DEPT_CSE"
        assert s["total_students"] > 0
        assert s["total_mentors"] >= 1
        assert s["critical_students"] <= s["total_students"]
        assert s["students_needing_action"] <= s["total_students"]
        assert s["risk_source"] == "risk_predictions"
        assert len(s["risk_distribution"]) == 5
        assert {item["risk_type"] for item in s["risk_distribution"]} == {
            "course_failure", "backlog", "gpa_threshold", "attendance_shortage", "discontinuation"
        }

        comparison = client.get("/api/hod/mentor-comparison", headers=hod)
        comparison.raise_for_status()
        c = comparison.json()
        assert c["department"] == "DEPT_CSE"
        assert c["items"]
        assert all(row["department"] == "DEPT_CSE" for row in c["items"])
        assert all(row["assigned_students"] >= row["students_needing_action"] for row in c["items"])
        assert all(0 <= row["action_rate"] <= 100 for row in c["items"])

        risk = client.get("/api/hod/risk-overview", headers=hod)
        risk.raise_for_status()
        assert len(risk.json()["items"]) == 5

        with SessionLocal() as db:
            mentor_ids = [row[0] for row in db.query(Teacher.id).filter(Teacher.role == "mentor", Teacher.department == "DEPT_CSE").all()]
            assert mentor_ids
            chosen_mentor = mentor_ids[0]
            chosen_student = db.query(Assignment.student_id).filter(Assignment.teacher_id == chosen_mentor, Assignment.assignment_type == "mentor").first()[0]
            
        drill = client.get(f"/api/hod/mentors/{chosen_mentor}/students", headers=hod)
        drill.raise_for_status()
        d = drill.json()
        assert d["mentor_id"] == chosen_mentor
        assert d["department"] == "DEPT_CSE"
        assert d["assigned_students"] >= d["returned_students"] >= 1
        assert chosen_student in {row["student_id"] for row in d["items"]}
        assert all("priority_score" in row and "risk_types" in row for row in d["items"])

        filtered = client.get(f"/api/hod/mentors/{chosen_mentor}/students?section=A&needs_action=true", headers=hod)
        filtered.raise_for_status()
        assert all(row["section"] == "A" and row["needs_action"] for row in filtered.json()["items"])

        support = client.get(f"/api/hod/mentors/{chosen_mentor}/students?risk_type=discontinuation", headers=hod)
        support.raise_for_status()
        assert all("discontinuation" in row["risk_types"] for row in support.json()["items"])

        bad_risk = client.get(f"/api/hod/mentors/{chosen_mentor}/students?risk_type=not_a_risk", headers=hod)
        assert bad_risk.status_code == 400

        # Department isolation and role isolation.
        assert client.get(f"/api/hod/mentors/T999/students", headers=hod).status_code == 404
        assert client.get(f"/api/hod/students", headers=mentor).status_code == 403
        assert client.get("/api/hod/summary", headers=dean).status_code == 403
        
        dept_students = client.get("/api/hod/students", headers=hod)
        dept_students.raise_for_status()
        items = dept_students.json()["items"]
        assert items
        assert all(row["department"] == "DEPT_CSE" for row in items)
        assert all("risk_level" in row and "primary_risk" in row for row in items)

        # HOD student access is department-scoped and permitted for in-department profiles.
        profile = client.get(f"/api/predictions/student/{chosen_student}", headers=hod)
        profile.raise_for_status()
        assert "risks" in profile.json()

        with SessionLocal() as db:
            assert db.query(RiskPrediction).count() >= 500 * 9

    print("PHASE 6 HOD TESTS PASSED")


if __name__ == "__main__":
    main()
