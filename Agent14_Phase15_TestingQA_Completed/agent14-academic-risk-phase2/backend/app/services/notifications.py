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
    level = str(data.get("risk_level") or "HIGH").upper()
    priority = float(alert.priority_score or 0)
    title = f"Academic risk alert: {student_name}"
    body = (
        f"{student_name} ({alert.student_id}) has a {level.lower()} {label} signal "
        f"with priority {priority:.1f}. Review the canonical alert and follow the "
        "appropriate academic support workflow."
    )
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
    total = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP)) or 0
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP, Notification.is_read.is_(False))) or 0
    return {"total": int(total), "unread": int(unread)}


def notification_list(db: Session, user: User, *, unread_only: bool = False, limit: int = 30) -> list[dict]:
    query = select(Notification).where(Notification.user_id == user.id, Notification.channel == CHANNEL_IN_APP)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    rows = db.scalars(query.order_by(Notification.created_at.desc()).limit(max(1, min(limit, 100)))).all()
    return [{
        "id": row.id, "alert_id": row.alert_id, "kind": row.kind,
        "title": row.title, "message": row.message, "status": row.status,
        "is_read": row.is_read,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    } for row in rows]


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
