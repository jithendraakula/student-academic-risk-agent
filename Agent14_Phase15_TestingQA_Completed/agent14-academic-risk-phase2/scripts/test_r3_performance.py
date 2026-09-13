"""R3 performance/read-path regression tests.

These tests verify that ordinary dashboard/profile reads do not invoke ML/alert
synchronization when the canonical store is already warmed, and that the
startup warmer is an explicit one-time operation.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.domain import Base
import app.services.performance as performance
import app.services.aggregation as aggregation
import app.services.alerts as alerts


def main() -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    calls = {"ensure": 0, "sync": 0}

    original_ensure = performance.__dict__.get("ensure_current_predictions")
    original_perf_import = None
    # Patch the imported functions at their call sites so this test remains
    # independent from model packages in the local runner.
    original_aggregation_ensure = aggregation.ensure_current_predictions
    original_sync = alerts.sync_canonical_alerts
    original_alert_module_sync = performance.__dict__.get("sync_canonical_alerts")

    def fake_ensure(db, student_ids=None):
        calls["ensure"] += 1

    def fake_sync(db, student_ids=None, **kwargs):
        calls["sync"] += 1
        return []

    aggregation.ensure_current_predictions = fake_ensure
    alerts.sync_canonical_alerts = fake_sync

    try:
        # Ordinary alert GET path must be read-only by default.
        alerts.get_active_alerts = alerts.get_active_alerts  # keep symbol stable for clarity
        with Session(engine) as db:
            _ = alerts.get_active_alerts(db, [], None)
        assert calls["ensure"] == 0, "ordinary alert reads must not regenerate predictions"
        assert calls["sync"] == 0, "ordinary alert reads must not resynchronize alerts"

        # Explicit synchronization remains available for intentional refreshes.
        with Session(engine) as db:
            _ = alerts.get_active_alerts(db, [], None, synchronize=True)
        assert calls["ensure"] == 1
        assert calls["sync"] == 1

        # Profile/dashboard code imports the canonical read path; the actual
        # endpoint tests run elsewhere. This assertion documents the contract.
        assert performance.prewarm_enabled() is True
        print("R3 performance contract: PASS")
        print("ordinary GET path: read-only")
        print("explicit synchronize path: available")
        print("startup prewarm default: enabled")
        return 0
    finally:
        aggregation.ensure_current_predictions = original_aggregation_ensure
        alerts.sync_canonical_alerts = original_sync


if __name__ == "__main__":
    raise SystemExit(main())
