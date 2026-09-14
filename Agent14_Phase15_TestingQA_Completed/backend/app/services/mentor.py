"""Mentor workspace service built on the canonical current-risk store."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AlertIntervention, Assignment, Student, User
from app.services.aggregation import scope_metrics, student_summary
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
    from app.models.domain import StudentCase
    completed_cases = db.scalars(select(StudentCase).where(StudentCase.student_id.in_(student_ids), StudentCase.status == "COMPLETED")) .all() if student_ids else []
    completed_student_ids = {c.student_id for c in completed_cases}
    latest_open_alert_by_student: dict[str, object] = {}
    for alert in alerts:
        current = latest_open_alert_by_student.get(alert.student_id)
        if current is None or (alert.updated_at or datetime.min) > (current.updated_at or datetime.min):
            latest_open_alert_by_student[alert.student_id] = alert
    completed_student_ids = {sid for sid in completed_student_ids if sid not in latest_open_alert_by_student}
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
            "case_completed": student_id in completed_student_ids,
            "student_name": students[student_id].name if student_id in students else summary.get("student_name"),
            "risk_breakdown": summary.get("risk_breakdown", []),
            "actionable_risk_types": summary.get("actionable_risk_types", []),
            "roll_number": students[student_id].roll_number if student_id in students else summary.get("roll_number"),
        })

    rows.sort(key=lambda row: (row.get("needs_action", False), row.get("priority_score", 0)), reverse=True)
    metrics = scope_metrics(db, student_ids, include_support_attention=True, user=user)
    return {
        "mentor_id": user.id,
        "mentor_name": user.name,
        "department": user.department,
        "assigned_students": metrics["monitored_students"],
        "critical_students": metrics["critical_students"],
        "high_risk_students": metrics["high_risk_students"],
        "high_only_students": metrics["high_only_students"],
        "elevated_risk_students": metrics["elevated_risk_students"],
        "students_needing_action": metrics["students_needing_action"],
        "elevated_risk_students": metrics["elevated_risk_students"],
        "students_with_multiple_risks": metrics["students_with_multiple_risks"],
        "risk_signals": metrics["risk_signals"],
        "actionable_risk_signals": metrics["actionable_risk_signals"],
        "open_alerts": metrics["open_alerts"],
        "open_alert_students": metrics["open_alert_students"],
        "completed_cases": len(completed_student_ids),
        "new_alerts": metrics["new_alerts"],
        "new_alert_students": metrics["new_alert_students"],
        "risk_distribution": metrics["risk_distribution"],
        "metric_semantics": metrics["metric_semantics"],
        "risk_thresholds": metrics["risk_thresholds"],
        "items": rows,
        "risk_source": metrics["risk_source"],
        "alert_source": metrics["alert_source"],
        "alert_policy": metrics["alert_policy"],
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
    page: int = 1,
    page_size: int = 25,
) -> dict:
    workspace = mentor_workspace(db, user)
    canonical_risk = normalize_risk_type(risk_type) if risk_type else None
    query_norm = query.strip().lower() if query else None
    severity_norm = severity.upper() if severity else None
    if severity_norm == "MEDIUM":
        severity_norm = "MODERATE"
    status_norm = status.upper() if status else None

    filtered = []
    for row in workspace["items"]:
        if query_norm and query_norm not in f"{row.get('student_id','')} {row.get('student_name','')}".lower():
            continue
        if canonical_risk and canonical_risk not in row.get("risk_types", []):
            continue
        if severity_norm:
            row_level = str(row.get("risk_level", "LOW")).upper()
            if row_level == "MEDIUM":
                row_level = "MODERATE"
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

    total = len(filtered)
    page = max(1, int(page)); page_size = max(1, min(int(page_size), 100))
    start = (page - 1) * page_size
    paged = filtered[start:start + page_size]
    return {**workspace, "items": paged, "returned_students": len(paged), "total_students": total, "page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}


def mentor_student_detail(db: Session, user: User, student_id: str) -> dict:
    if not can_access_student(db, user, student_id):
        return None
    workspace = mentor_workspace(db, user)
    row = next((item for item in workspace["items"] if item["student_id"] == student_id), None)
    if row is None:
        return None
    return row
