"""R9 runtime alert truth and canonical alert projection gate.

This test deliberately validates the *running database state* after application
startup, not the seed CSV alone.  It catches the class of QA bug where the seed
work-item count is mistaken for the live canonical alert count.

Run from the project root:
    python scripts/test_r9_runtime_alerts.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import types
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

DB_PATH = Path(tempfile.gettempdir()) / "agent14_r9_runtime_alerts.db"
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["JWT_SECRET"] = "r9-test-secret-change-me"
os.environ["ENVIRONMENT"] = "test"
os.environ["AGENT14_PREWARM_RISK"] = "true"


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
            def __init__(self, *args, **kwargs):
                pass

            def hash(self, password):
                return f"hashed:{password}"

            def verify(self, password, stored):
                return stored == f"hashed:{password}" or stored == password

        context.CryptContext = CryptContext
        sys.modules["passlib"] = passlib
        sys.modules["passlib.context"] = context


install_test_auth_stubs()

from app.main import app  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.domain import AlertIntervention, RiskPrediction, User  # noqa: E402
from app.services.alerts import get_active_alerts  # noqa: E402
from app.services.performance import warm_current_risk_store  # noqa: E402
from app.services.rbac import scoped_student_ids  # noqa: E402
from app.services.aggregation import scope_metrics  # noqa: E402

OPEN_STATUSES = {"NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"}


def login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    response.raise_for_status()
    return response.json()["token"]


def main() -> int:
    with TestClient(app) as client:
        with SessionLocal() as db:
            total_before = db.query(AlertIntervention).count()
            active_before = db.query(AlertIntervention).filter(AlertIntervention.status.in_(OPEN_STATUSES)).count()
            prediction_count = db.query(RiskPrediction).count()
            assert prediction_count == 4500, f"expected 500*9 current predictions, got {prediction_count}"

            # Canonical alert records are projections of qualifying current predictions.
            active_rows = db.query(AlertIntervention).filter(AlertIntervention.status.in_(OPEN_STATUSES)).all()
            assert active_rows, "runtime produced no active alerts; alert projection is unexpectedly empty"
            for alert in active_rows:
                data = alert.data or {}
                assert data.get("source") == "risk_predictions", f"active alert {alert.id} is not canonical"
                prediction_id = data.get("prediction_id")
                prediction = db.get(RiskPrediction, prediction_id) if prediction_id else None
                assert prediction is not None, f"active alert {alert.id} points to missing prediction"
                assert prediction.student_id == alert.student_id
                assert str(prediction.risk_type) == str(alert.risk_type)

            # The seed file is historical/demo input, not the live KPI source.
            import pandas as pd
            seed = pd.read_csv(ROOT / "data" / "processed" / "alerts_interventions.csv")
            seed_open = int(seed[seed["alert_status"].astype(str).str.upper().isin(OPEN_STATUSES)].shape[0])
            assert seed_open == 72, f"unexpected demo seed work-item count: {seed_open}"
            assert active_before != seed_open or total_before != seed_open, (
                "runtime alert state still equals the seed CSV by accident; the test must prove the live projection is distinct"
            )

            # Dashboard metrics must use the runtime active alert state.
            for uid in ("T001", "H001", "D001"):
                user = db.get(User, uid)
                ids = scoped_student_ids(db, user)
                metrics = scope_metrics(db, ids, include_support_attention=True, user=user)
                active = get_active_alerts(db, ids, user)
                assert metrics["open_alerts"] == len(active)
                assert metrics["open_alert_students"] == len({a.student_id for a in active})
                assert metrics["open_alert_students"] <= metrics["open_alerts"]

            before_repeat_total = total_before
            before_repeat_active = active_before
            warm_current_risk_store(db)
            db.expire_all()
            after_repeat_total = db.query(AlertIntervention).count()
            after_repeat_active = db.query(AlertIntervention).filter(AlertIntervention.status.in_(OPEN_STATUSES)).count()
            assert after_repeat_total == before_repeat_total, (
                f"warm/sync not idempotent: alerts {before_repeat_total} -> {after_repeat_total}"
            )
            assert after_repeat_active == before_repeat_active, (
                f"warm/sync not idempotent: active alerts {before_repeat_active} -> {after_repeat_active}"
            )

            # API summaries must expose the same runtime values the services report.
            for email, uid, path in [
                ("mentor.one.cse@vignan.ac.in", "T001", "/api/mentor/summary"),
                ("hod.cse@vignan.ac.in", "H001", "/api/hod/summary"),
                ("dean@vignan.ac.in", "D001", "/api/dean/summary"),
            ]:
                token = login(client, email)
                response = client.get(path, headers={"Authorization": f"Bearer {token}"})
                response.raise_for_status()
                payload = response.json()
                user = db.get(User, uid)
                ids = scoped_student_ids(db, user)
                metrics = scope_metrics(db, ids, include_support_attention=True, user=user)
                assert payload["open_alerts"] == metrics["open_alerts"]
                assert payload["open_alert_students"] == metrics["open_alert_students"]

            result = {
                "passed": True,
                "seed_alert_work_items": seed_open,
                "runtime_alert_total": total_before,
                "runtime_open_alerts": active_before,
                "runtime_open_alert_students_mentor": None,
                "current_risk_predictions": prediction_count,
                "idempotent": True,
                "message": "Runtime alert KPIs are derived from canonical AlertIntervention rows after RiskPrediction projection, not from the seed CSV.",
            }
            print(json.dumps(result, indent=2))
            report = ROOT / "test_artifacts" / "r9_runtime_alert_report.json"
            report.parent.mkdir(exist_ok=True)
            report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
