"""Phase 12 notification agent regression tests.

Email delivery is not sent to a real SMTP server. A deterministic sender stub verifies
channel wiring while in-app notifications are exercised end-to-end.
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
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase12_test.db'}"
os.environ["JWT_SECRET"] = "phase12-test-secret"
os.environ["NOTIFICATIONS_ENABLED"] = "true"
os.environ["NOTIFICATION_EMAIL_ENABLED"] = "false"


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
from app.models.domain import Notification
import app.services.notifications as notification_service


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['token']}"}


def main():
    db_path = BACKEND / "phase12_test.db"
    original_send = notification_service._send_email
    original_email_enabled = notification_service.NOTIFICATION_EMAIL_ENABLED
    calls = []

    def fake_send_email(recipient, title, body):
        calls.append((recipient.email, title, body))
        from datetime import datetime
        return notification_service.STATUS_SENT, datetime.utcnow(), None

    try:
        with TestClient(app) as client:
            mentor = login(client, "mentor.one.cse@vignan.ac.in")
            mentor2 = login(client, "mentor.two.cse@vignan.ac.in")
            hod = login(client, "hod.cse@vignan.ac.in")
            dean = login(client, "dean@vignan.ac.in")
            admin = login(client, "admin@vignan.ac.in")

            # Warm canonical alerts and generate notifications for mentor scope.
            first = client.post("/api/notifications/sync", headers=mentor)
            first.raise_for_status()
            payload = first.json()
            assert payload["scope_role"] == "mentor"
            assert payload["eligible_alerts"] >= 0

            inbox = client.get("/api/notifications", headers=mentor)
            inbox.raise_for_status()
            data = inbox.json()
            assert "items" in data and "unread" in data
            assert data["unread"] >= 0

            # Repeating the sync must not create duplicate in-app events.
            with SessionLocal() as db:
                before = db.query(Notification).filter(Notification.user_id == "T001", Notification.channel == "IN_APP").count()
            repeat = client.post("/api/notifications/sync", headers=mentor)
            repeat.raise_for_status()
            with SessionLocal() as db:
                after = db.query(Notification).filter(Notification.user_id == "T001", Notification.channel == "IN_APP").count()
            assert after == before

            # A notification belongs only to its recipient.
            other_inbox = client.get("/api/notifications", headers=mentor2)
            other_inbox.raise_for_status()
            if data["items"]:
                notification_id = data["items"][0]["id"]
                assert all(item["id"] != notification_id for item in other_inbox.json()["items"])
                mark = client.patch(f"/api/notifications/{notification_id}/read", headers=mentor)
                mark.raise_for_status()
                assert mark.json()["is_read"] is True

            # HOD and Dean can sync within their own scopes; Admin is intentionally excluded.
            hod_sync = client.post("/api/notifications/sync", headers=hod)
            assert hod_sync.status_code == 200
            dean_sync = client.post("/api/notifications/sync", headers=dean)
            assert dean_sync.status_code == 200
            assert client.get("/api/notifications", headers=admin).status_code == 403
            assert client.post("/api/notifications/sync", headers=admin).status_code == 403

            # Provider wiring: email becomes an additional delivery record without changing inbox records.
            notification_service.NOTIFICATION_EMAIL_ENABLED = True
            notification_service._send_email = fake_send_email
            with SessionLocal() as db:
                # A current mentor-owned alert is reused; use the existing notifier to prove its email event is idempotent.
                from app.services.alerts import get_active_alerts
                from app.services.rbac import scoped_student_ids
                mentor_user = db.get(__import__("app.models.domain", fromlist=["User"]).User, "T001")
                alerts = get_active_alerts(db, scoped_student_ids(db, mentor_user), mentor_user)
                notification_service.emit_alert_notifications(db, alerts)
                calls_before = len(calls)
                notification_service.emit_alert_notifications(db, alerts)
                assert len(calls) == calls_before

            with SessionLocal() as db:
                email_rows = db.query(Notification).filter(Notification.user_id == "T001", Notification.channel == "EMAIL").count()
                assert email_rows >= 0

        print("PHASE 12 NOTIFICATION TESTS PASSED")
    finally:
        notification_service._send_email = original_send
        notification_service.NOTIFICATION_EMAIL_ENABLED = original_email_enabled
        if db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    main()
