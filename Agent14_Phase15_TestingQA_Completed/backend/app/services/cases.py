"""Stable student case lifecycle and structured case events."""
from __future__ import annotations

from datetime import datetime
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AlertIntervention, CaseEvent, StudentCase

OPEN_CASE = "OPEN"
COMPLETED_CASE = "COMPLETED"


def get_active_case(db: Session, student_id: str) -> StudentCase | None:
    return db.scalar(
        select(StudentCase)
        .where(StudentCase.student_id == student_id, StudentCase.status == OPEN_CASE)
        .order_by(StudentCase.opened_at.desc())
    )


def get_or_create_case(db: Session, student_id: str, *, risk_snapshot_at: datetime | None = None) -> StudentCase:
    case = get_active_case(db, student_id)
    if case is None:
        case = StudentCase(
            id=f"CASE-{uuid.uuid4().hex[:14].upper()}",
            student_id=student_id,
            status=OPEN_CASE,
            opened_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_risk_snapshot_at=risk_snapshot_at,
            completion_metadata={},
        )
        db.add(case)
        db.flush()
        db.add(CaseEvent(
            id=f"CE-{uuid.uuid4().hex[:14].upper()}",
            case_id=case.id,
            student_id=student_id,
            event_type="CASE_OPENED",
            event_metadata={"source": "risk_engine"},
        ))
    elif risk_snapshot_at and (case.last_risk_snapshot_at is None or risk_snapshot_at > case.last_risk_snapshot_at):
        case.last_risk_snapshot_at = risk_snapshot_at
        case.updated_at = datetime.utcnow()
    return case


def record_case_event(
    db: Session,
    *, case: StudentCase,
    actor_id: str | None,
    event_type: str,
    from_status: str | None = None,
    to_status: str | None = None,
    notes: str | None = None,
    metadata: dict | None = None,
) -> CaseEvent:
    event = CaseEvent(
        id=f"CE-{uuid.uuid4().hex[:14].upper()}",
        case_id=case.id,
        student_id=case.student_id,
        actor_id=actor_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        notes=notes,
        event_metadata=metadata or {},
    )
    db.add(event)
    return event


def case_summary(db: Session, student_id: str) -> dict:
    active = get_active_case(db, student_id)
    latest = db.scalar(
        select(StudentCase)
        .where(StudentCase.student_id == student_id, StudentCase.status == COMPLETED_CASE)
        .order_by(StudentCase.completed_at.desc())
    )
    case = active or latest
    return {
        "case_id": case.id if case else None,
        "status": case.status if case else None,
        "case_completed": bool(case and case.status == COMPLETED_CASE),
        "opened_at": case.opened_at.isoformat() if case and case.opened_at else None,
        "completed_at": case.completed_at.isoformat() if case and case.completed_at else None,
        "completed_by": case.completed_by if case else None,
        "completion_category": case.completion_category if case else None,
        "completion_reason": case.completion_reason if case else None,
        "completion_notes": case.completion_notes if case else None,
        "follow_up_outcome": case.follow_up_outcome if case else None,
        "completion_metadata": case.completion_metadata if case else {},
    }


def backfill_student_cases(db: Session) -> None:
    """Backfill one stable case per student with existing alert history."""
    student_ids = db.scalars(select(AlertIntervention.student_id).distinct()).all()
    for student_id in student_ids:
        active = get_active_case(db, student_id)
        if active:
            continue
        open_alert = db.scalar(
            select(AlertIntervention)
            .where(AlertIntervention.student_id == student_id, AlertIntervention.status.in_(["NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"]))
            .order_by(AlertIntervention.updated_at.desc())
        )
        if open_alert:
            case = get_or_create_case(db, student_id, risk_snapshot_at=open_alert.updated_at)
            for alert in db.scalars(select(AlertIntervention).where(AlertIntervention.student_id == student_id, AlertIntervention.case_id.is_(None))).all():
                alert.case_id = case.id
            continue
        resolved = db.scalar(
            select(AlertIntervention)
            .where(AlertIntervention.student_id == student_id, AlertIntervention.status == "RESOLVED")
            .order_by(AlertIntervention.updated_at.desc())
        )
        if resolved and (resolved.data or {}).get("case_completed"):
            case = StudentCase(
                id=f"CASE-{uuid.uuid4().hex[:14].upper()}", student_id=student_id, status=COMPLETED_CASE,
                opened_at=resolved.updated_at or datetime.utcnow(), updated_at=resolved.updated_at or datetime.utcnow(),
                completed_at=resolved.updated_at or datetime.utcnow(), completed_by=(resolved.data or {}).get("completed_by"),
                completion_notes=resolved.intervention_notes, completion_metadata={"backfilled_from_alert": resolved.id},
            )
            db.add(case); db.flush()
            record_case_event(db, case=case, actor_id=case.completed_by, event_type="CASE_COMPLETED", to_status=COMPLETED_CASE,
                              notes=case.completion_notes, metadata={"backfilled_from_alert": resolved.id})
            for alert in db.scalars(select(AlertIntervention).where(AlertIntervention.student_id == student_id, AlertIntervention.case_id.is_(None))).all():
                alert.case_id = case.id
    db.commit()
