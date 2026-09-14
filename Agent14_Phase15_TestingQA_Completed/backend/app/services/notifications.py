"""Phase 12 notification agent: in-app delivery plus optional SMTP email."""
from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage
import smtplib
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import (
    NOTIFICATIONS_ENABLED,
    NOTIFICATION_EMAIL_ENABLED,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_USE_TLS,
    SMTP_FROM_EMAIL,
    NOTIFICATION_HOD_PRIORITY_THRESHOLD,
    NOTIFICATION_DEAN_PRIORITY_THRESHOLD,
)
from app.models.domain import AlertIntervention, Notification, Student, User
from app.services.rbac import normalize_role, scoped_student_ids

CHANNEL_IN_APP = "IN_APP"
CHANNEL_EMAIL = "EMAIL"
STATUS_SENT = "SENT"
STATUS_SKIPPED = "SKIPPED"
STATUS_FAILED = "FAILED"


def _recipients(db: Session, alert: AlertIntervention) -> list[User]:
    student = db.get(Student, alert.student_id)
    if not student:
        return []
    recipients: dict[str, User] = {}
    mentor = db.scalar(select(User).where(User.id == alert.teacher_id, User.role == "mentor"))
    if mentor:
        recipients[mentor.id] = mentor
    priority = float(alert.priority_score or 0)
    level = str((alert.data or {}).get("risk_level") or "").upper()
    if level == "CRITICAL" or priority >= NOTIFICATION_HOD_PRIORITY_THRESHOLD:
        for user in db.scalars(select(User).where(User.role == "hod", User.department == student.department)).all():
            recipients[user.id] = user
    if level == "CRITICAL" or priority >= NOTIFICATION_DEAN_PRIORITY_THRESHOLD:
        for user in db.scalars(select(User).where(User.role == "dean")).all():
            recipients[user.id] = user
    return list(recipients.values())


def _message(alert: AlertIntervention) -> tuple[str, str]:
    data = alert.data or {}
    label = str(data.get("risk_label") or alert.risk_type.replace("_", " ").title())
    student_name = data.get("student_name") or alert.student_id
    roll = data.get("roll_number")
    display_student = str(roll or student_name)
    level = str(data.get("risk_level") or "HIGH").upper()
    priority = float(alert.priority_score or 0)
    title = f"{label} · {display_student}"
    evidence = str(data.get("evidence") or data.get("context_observation") or data.get("context_summary") or "Current academic evidence needs review.")
    action = str(data.get("suggested_action") or "Review the student case and decide the next support action.")
    body = f"{level.title()} · Priority {priority:.0f}/100. {evidence} Recommended: {action}"
    return title, body


def _send_email(recipient: User, title: str, body: str) -> tuple[str, datetime | None, str | None]:
    if not NOTIFICATION_EMAIL_ENABLED:
        return STATUS_SKIPPED, None, "Email delivery is disabled by configuration"
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        return STATUS_SKIPPED, None, "SMTP is not configured"
    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = recipient.email
    msg.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)
        return STATUS_SENT, datetime.utcnow(), None
    except Exception as exc:
        return STATUS_FAILED, None, str(exc)[:500]


def _create_once(
    db: Session, *, alert: AlertIntervention, user: User, channel: str,
    kind: str, title: str, message: str, status: str,
    sent_at: datetime | None, error: str | None,
) -> Notification | None:
    prediction_id = (alert.data or {}).get("prediction_id") or "unknown"
    event_key = f"{alert.id}:{prediction_id}:{user.id}:{channel}"
    if db.scalar(select(Notification).where(Notification.event_key == event_key)):
        return None
    row = Notification(
        id=f"NTF-{uuid.uuid4().hex[:14].upper()}", event_key=event_key,
        user_id=user.id, alert_id=alert.id, channel=channel, kind=kind,
        title=title, message=message, status=status, is_read=False,
        created_at=datetime.utcnow(), sent_at=sent_at, error=error,
    )
    db.add(row)
    return row


def emit_alert_notifications(db: Session, alerts: list[AlertIntervention]) -> dict:
    """Emit idempotent notifications for observed canonical alert snapshots."""
    if not NOTIFICATIONS_ENABLED or not alerts:
        return {"created": 0, "email_sent": 0, "email_failed": 0}
    created = email_sent = email_failed = 0
    for alert in alerts:
        title, body = _message(alert)
        level = str((alert.data or {}).get("risk_level") or "").upper()
        kind = "critical_alert" if level == "CRITICAL" else "risk_alert"
        for recipient in _recipients(db, alert):
            row = _create_once(db, alert=alert, user=recipient, channel=CHANNEL_IN_APP,
                               kind=kind, title=title, message=body, status=STATUS_SENT,
                               sent_at=datetime.utcnow(), error=None)
            if row:
                created += 1
            prediction_id = (alert.data or {}).get("prediction_id") or "unknown"
            email_event_key = f"{alert.id}:{prediction_id}:{recipient.id}:{CHANNEL_EMAIL}"
            existing_email = db.scalar(select(Notification).where(Notification.event_key == email_event_key))
            if existing_email:
                continue
            status, sent_at, error = _send_email(recipient, title, body)
            email_row = _create_once(db, alert=alert, user=recipient, channel=CHANNEL_EMAIL,
                                     kind=kind, title=title, message=body, status=status,
                                     sent_at=sent_at, error=error)
            if email_row and status == STATUS_SENT:
                email_sent += 1
            elif email_row and status == STATUS_FAILED:
                email_failed += 1
    db.commit()
    return {"created": created, "email_sent": email_sent, "email_failed": email_failed}


def notification_summary(db: Session, user: User) -> dict:
    base = select(Notification).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP)
    total = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP)) or 0
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP, Notification.is_read.is_(False))) or 0
    rows = db.scalars(base.order_by(Notification.created_at.desc())).all()
    # Category counts are intentionally derived from the same live alert metadata
    # used by notification_list so the action-center tabs describe real work.
    action_required = follow_up = escalation = 0
    for row in rows:
        alert = db.get(AlertIntervention, row.alert_id) if row.alert_id else None
        data = (alert.data or {}) if alert else {}
        level = str(data.get("risk_level") or "").upper()
        status = str(alert.status or "") if alert else ""
        priority = float(alert.priority_score or 0) if alert else 0.0
        needs_action = alert is not None and status != "RESOLVED" and (status in {"NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"} or priority >= NOTIFICATION_HOD_PRIORITY_THRESHOLD)
        if status == "FOLLOW_UP":
            follow_up += 1
        elif row.kind == "critical_alert" or level == "CRITICAL":
            action_required += 1
        elif "escal" in row.kind.lower():
            escalation += 1
        elif needs_action:
            action_required += 1
    return {
        "total": int(total), "unread": int(unread),
        "action_required": int(action_required), "follow_up": int(follow_up), "escalation": int(escalation),
    }


def mark_all_read(db: Session, user: User) -> dict:
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP, Notification.is_read.is_(False))).all()
    now = datetime.utcnow()
    for row in rows:
        row.is_read = True
        row.read_at = now
    db.commit()
    return {"updated": len(rows), "marked_read_at": now.isoformat()}


def notification_list(db: Session, user: User, *, unread_only: bool = False, limit: int = 30) -> list[dict]:
    query = select(Notification).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    rows = db.scalars(query.order_by(Notification.created_at.desc()).limit(max(1, min(limit, 100)))).all()
    items = []
    for row in rows:
        alert = db.get(AlertIntervention, row.alert_id) if row.alert_id else None
        data = (alert.data or {}) if alert else {}
        student = db.get(Student, alert.student_id) if alert else None
        level = str(data.get("risk_level") or "").upper()
        risk_label = str(data.get("risk_label") or (alert.risk_type.replace("_", " ").title() if alert else "Academic risk"))
        priority = float(alert.priority_score or 0) if alert else 0.0
        alert_status = str(alert.status or "") if alert else ""
        action_required = alert is not None and alert_status != "RESOLVED" and (
            alert_status in {"NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"} or priority >= NOTIFICATION_HOD_PRIORITY_THRESHOLD
        )
        if alert_status == "FOLLOW_UP":
            category = "follow_up"
        elif row.kind == "critical_alert" or level == "CRITICAL":
            category = "action_required"
        elif "escal" in row.kind.lower():
            category = "escalation"
        else:
            category = "information"
        items.append({
            "id": row.id, "alert_id": row.alert_id, "kind": row.kind,
            "category": category, "title": row.title, "message": row.message,
            "status": row.status, "is_read": row.is_read,
            "student_id": alert.student_id if alert else data.get("student_id"),
            "student_name": data.get("student_name") or (student.name if student else None),
            "roll_number": student.roll_number if student else data.get("roll_number"),
            "section": student.section if student else data.get("section"),
            "department": student.department if student else data.get("department"),
            "risk_type": alert.risk_type if alert else data.get("risk_type"),
            "risk_label": risk_label, "risk_level": level or None,
            "priority_score": priority, "alert_status": alert_status or None,
            "recommended_action": data.get("suggested_action"),
            "evidence": data.get("evidence") or data.get("context_observation") or data.get("context_summary"),
            "action_required": action_required,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    return items


def mark_read(db: Session, user: User, notification_id: str) -> dict:
    row = db.get(Notification, notification_id)
    if not row or row.user_id != user.id or row.channel != CHANNEL_IN_APP:
        raise PermissionError("Notification not found")
    row.is_read = True
    row.read_at = datetime.utcnow()
    db.commit()
    return {"id": row.id, "is_read": True, "read_at": row.read_at.isoformat()}


def notification_sync(db: Session, user: User) -> dict:
    from app.services.alerts import get_active_alerts
    ids = scoped_student_ids(db, user)
    alerts = get_active_alerts(db, ids, user)
    delivery = emit_alert_notifications(db, alerts)
    return {"scope_role": normalize_role(user.role), "eligible_alerts": len(alerts), **delivery, **notification_summary(db, user)}
