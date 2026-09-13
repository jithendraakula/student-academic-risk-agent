"""Phase 14 security regression tests. Run from project root."""
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
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase14_security_test.db'}"
os.environ["JWT_SECRET"] = "phase14-test-secret-change-me"
os.environ["ENVIRONMENT"] = "development"
os.environ["ENABLE_DOCS"] = "true"

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

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.domain import AuditLog, RevokedToken, User  # noqa: E402
from app.core.security import hash_password  # noqa: E402


def main() -> None:
    try:
        with TestClient(app) as client:
            assert client.get("/api/health").json()["database"] == "connected"
            login = client.post("/api/auth/login", json={"email": "mentor.one.cse@vignan.ac.in", "password": "demo"})
            assert login.status_code == 200, login.text
            token = login.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            assert client.get("/api/auth/me", headers=headers).status_code == 200
            assert client.get("/api/admin/config", headers=headers).status_code == 403
            change = client.post("/api/auth/change-password", headers=headers, json={"current_password": "demo", "new_password": "DemoPass1"})
            assert change.status_code == 200, change.text
            assert client.post("/api/auth/logout", headers=headers).status_code == 401
            assert client.get("/api/auth/me", headers=headers).status_code == 401
            assert client.get("/api/health").headers.get("X-Content-Type-Options") == "nosniff"
            assert client.get("/api/health").headers.get("X-Frame-Options") == "DENY"
            assert client.get("/api/health").headers.get("X-Request-ID")

            # Failed login accounting is durable on the user and audit trail.
            failed = client.post("/api/auth/login", json={"email": "admin@vignan.ac.in", "password": "wrong"})
            assert failed.status_code == 401
            with SessionLocal() as db:
                assert db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILED").count() >= 1
                assert db.query(RevokedToken).count() >= 1
                assert db.query(User).filter(User.email == "mentor.one.cse@vignan.ac.in").first().is_active is True
                assert db.query(User).filter(User.email == "mentor.one.cse@vignan.ac.in").first().password_hash != "demo"
        print("PHASE 14 SECURITY TESTS PASSED")
    finally:
        try:
            (BACKEND / "phase14_security_test.db").unlink(missing_ok=True)
        except Exception:
            pass

if __name__ == "__main__":
    main()
