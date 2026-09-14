from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from app.models.domain import AuditLog, User


def record_audit(
    db: Session,
    *,
    action: str,
    actor: User | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(AuditLog(
        actor_id=actor.id if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:512] or None,
        details=details or {},
    ))
