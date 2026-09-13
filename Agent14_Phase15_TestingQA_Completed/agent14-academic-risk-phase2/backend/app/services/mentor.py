"""Mentor workspace service built on the canonical current-risk store."""
from __future__ import annotations

from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AlertIntervention, Assignment, Student, User
from app.services.aggregation import student_summary
from app.services.alerts import get_active_alerts, alert_item
from app.services.risk_engine import normalize_risk_type, RISK_TYPES
from app.services.rbac import can_access_student, scoped_student_ids


def _student_rows(db: Session, user: User) -> tuple[list[str], dict[str, dict]]:
    ids = scoped_student_ids(db, user)
    summaries = student_summary(db, ids, include_support_attention=True)
    return ids, summaries


def mentor_workspace(db: Session, user: User) -> dict:
    student_ids, summaries = _student_rows(db, user)
    alerts = get_active_alerts(db, student_ids, user)
    alerts_by_student: dict[str, list[dict]] = defaultdict(list)
    for alert in alerts:
        alerts_by_student[alert.student_id].append(alert_item(db, alert))

    students = {
        student.id: student
        for student in db.scalars(select(Student).where(Student.id.in_(student_ids))).all()
    }
    rows = []
    for student_id in student_ids:
        summary = summaries.get(student_id, {})
        student_alerts = alerts_by_student.get(student_id, [])
        open_alerts = [a for a in student_alerts if a["status"] != "RESOLVED"]
        new_alerts = [a for a in student_alerts if a["status"] == "NEW"]
        rows.append({
            **summary,
            "open_alerts": len(open_alerts),
            "new_alerts": len(new_alerts),
            "alerts": student_alerts,
            "primary_alert": max(student_alerts, key=lambda a: a["priority_score"], default=None),
            "student_name": students[student_id].name if student_id in students else summary.get("student_name"),
        })

    rows.sort(key=lambda row: (row.get("needs_action", False), row.get("priority_score", 0)), reverse=True)
    return {
        "mentor_id": user.id,
        "mentor_name": user.name,
        "department": user.department,
        "assigned_students": len(student_ids),
        "critical_students": sum(1 for row in rows if row.get("critical")),
        "high_risk_students": sum(1 for row in rows if row.get("high_risk")),
        "students_needing_action": sum(1 for row in rows if row.get("needs_action")),
        "open_alerts": len(alerts),
        "new_alerts": sum(1 for alert in alerts if alert.status == "NEW"),
        "items": rows,
        "risk_source": "risk_predictions",
        "alert_policy": {"priority_threshold": 60, "critical_override": True},
    }


def filter_mentor_students(
    db: Session,
    user: User,
    *,
    query: str | None = None,
    risk_type: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    needs_action: bool | None = None,
) -> dict:
    workspace = mentor_workspace(db, user)
    canonical_risk = normalize_risk_type(risk_type) if risk_type else None
    query_norm = query.strip().lower() if query else None
    severity_norm = severity.upper() if severity else None
    status_norm = status.upper() if status else None

    filtered = []
    for row in workspace["items"]:
        if query_norm and query_norm not in f"{row.get('student_id','')} {row.get('student_name','')}".lower():
            continue
        if canonical_risk and canonical_risk not in row.get("risk_types", []):
            continue
        if severity_norm:
            row_level = str(row.get("risk_level", "LOW")).upper()
            if severity_norm == "HIGH" and row_level not in {"HIGH", "CRITICAL"}:
                continue
            if severity_norm != "HIGH" and row_level != severity_norm:
                continue
        if status_norm:
            statuses = {str(alert["status"]).upper() for alert in row.get("alerts", [])}
            if status_norm not in statuses:
                continue
        if needs_action is not None and bool(row.get("needs_action")) != needs_action:
            continue
        filtered.append(row)

    return {**workspace, "items": filtered, "returned_students": len(filtered)}


def mentor_student_detail(db: Session, user: User, student_id: str) -> dict:
    if not can_access_student(db, user, student_id):
        return None
    workspace = mentor_workspace(db, user)
    row = next((item for item in workspace["items"] if item["student_id"] == student_id), None)
    if row is None:
        return None
    return row
