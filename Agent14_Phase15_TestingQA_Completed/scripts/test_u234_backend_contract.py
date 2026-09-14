from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

with tempfile.TemporaryDirectory(prefix="agent14-u234-") as tmp:
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp) / 'u234.db'}"
    os.environ["JWT_SECRET"] = "u234-test-secret"

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

    passlib = types.ModuleType("passlib")
    context = types.ModuleType("passlib.context")
    class CryptContext:
        def __init__(self, *args, **kwargs): pass
        def hash(self, password): return f"hashed:{password}"
        def verify(self, password, stored): return stored == f"hashed:{password}" or stored == password
    context.CryptContext = CryptContext
    sys.modules["passlib"] = passlib
    sys.modules["passlib.context"] = context

    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import SessionLocal
    from app.models.domain import Student

    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": "mentor.one.cse@vignan.ac.in", "password": "demo"})
        assert login.status_code == 200, login.text
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        with SessionLocal() as db:
            student = db.query(Student).filter(Student.section == "CSE-A").order_by(Student.id.asc()).first()
            assert student is not None
            assert student.roll_number == "241FA04001", student.roll_number
            sid = student.id
        profile = client.get(f"/api/predictions/student/{sid}", headers=headers)
        assert profile.status_code == 200, profile.text
        body = profile.json()
        assert body["student"]["roll_number"] == "241FA04001"
        assert body["student"]["student_id"] == sid

print("U2-U4 BACKEND CONTRACT: PASS")
