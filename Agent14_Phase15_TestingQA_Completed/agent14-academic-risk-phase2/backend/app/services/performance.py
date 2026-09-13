"""Startup warming and read-path helpers for the canonical current-risk store."""
from __future__ import annotations

import os
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Student


def prewarm_enabled() -> bool:
    return os.getenv("AGENT14_PREWARM_RISK", "true").lower() in {"1", "true", "yes", "on"}


def warm_current_risk_store(db: Session) -> dict[str, int | float]:
    """Materialize current predictions/alerts once so request-time reads stay cheap."""
    if not prewarm_enabled():
        return {"students": 0, "predictions": 0, "alerts": 0}
    from app.services.aggregation import ensure_current_predictions
    from app.services.alerts import sync_canonical_alerts

    student_ids = list(db.scalars(select(Student.id)).all())
    ensure_current_predictions(db, student_ids)
    alerts = sync_canonical_alerts(db, student_ids, include_support_attention=True)
    return {
        "students": len(student_ids),
        "predictions": sum(9 for _ in student_ids),
        "alerts": len(alerts),
    }
