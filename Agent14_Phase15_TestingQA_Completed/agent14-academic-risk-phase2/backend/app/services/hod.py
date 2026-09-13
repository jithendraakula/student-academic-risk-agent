"""HOD department workspace aggregation and drill-down services."""
from __future__ import annotations

from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Assignment, Student, Teacher, User
from app.services.aggregation import student_summary
from app.services.alerts import get_active_alerts
from app.services.risk_engine import RISK_TYPE_ORDER, RISK_TYPES, normalize_risk_type
from app.services.rbac import can_access_student


def _department_student_ids(db: Session, user: User) -> list[str]:
    return list(db.scalars(select(Student.id).where(Student.department == user.department)).all())


def _intervention_metrics(db: Session, student_ids: list[str]) -> dict:
    from app.models.domain import AlertIntervention
    alerts = db.scalars(select(AlertIntervention).where(AlertIntervention.student_id.in_(student_ids))).all() if student_ids else []
    return {
        "resolved_interventions": sum(a.status == "RESOLVED" for a in alerts),
        "overdue_follow_ups": sum(
            bool((a.data or {}).get("follow_up_date"))
            and str((a.data or {}).get("follow_up_date")) < __import__("datetime").date.today().isoformat()
            and a.status != "RESOLVED"
            for a in alerts
        ),
    }


def _mentor_rows(db: Session, user: User) -> list[dict]:
    mentors = db.scalars(
        select(Teacher)
        .where(Teacher.role == "mentor", Teacher.department == user.department)
        .order_by(Teacher.name.asc())
    ).all()
    rows: list[dict] = []
    for mentor in mentors:
        student_ids = list(db.scalars(
            select(Assignment.student_id).where(
                Assignment.teacher_id == mentor.id,
                Assignment.assignment_type == "mentor",
            )
        ).all())
        summaries = student_summary(db, student_ids, include_support_attention=True)
        alerts = get_active_alerts(db, student_ids, user)
        action_students = sum(1 for sid in student_ids if summaries.get(sid, {}).get("needs_action"))
        high_students = sum(1 for sid in student_ids if summaries.get(sid, {}).get("high_risk"))
        critical_students = sum(1 for sid in student_ids if summaries.get(sid, {}).get("critical"))
        metrics = _intervention_metrics(db, student_ids)
        rows.append({
            "mentor_id": mentor.id,
            "mentor_name": mentor.name,
            "department": mentor.department,
            "assigned_students": len(student_ids),
            "critical_students": critical_students,
            "high_risk_students": high_students,
            "students_needing_action": action_students,
            "open_alerts": len(alerts),
            "new_alerts": sum(alert.status == "NEW" for alert in alerts),
            "intervention_load": round(sum(float(alert.priority_score or 0) for alert in alerts), 1),
            "resolved_interventions": metrics["resolved_interventions"],
            "overdue_follow_ups": metrics["overdue_follow_ups"],
            "action_rate": round((action_students / len(student_ids)) * 100, 1) if student_ids else 0.0,
            "risk_source": "risk_predictions",
        })
    return rows


def mentor_comparison(db: Session, user: User) -> dict:
    rows = _mentor_rows(db, user)
    rows.sort(
        key=lambda row: (row["students_needing_action"], row["high_risk_students"], row["intervention_load"]),
        reverse=True,
    )
    return {
        "department": user.department,
        "items": rows,
        "risk_source": "risk_predictions",
        "alert_policy": {"priority_threshold": 60, "critical_override": True},
    }


def department_summary(db: Session, user: User) -> dict:
    student_ids = _department_student_ids(db, user)
    summaries = student_summary(db, student_ids, include_support_attention=True)
    alerts = get_active_alerts(db, student_ids, user)

    by_risk: dict[str, set[str]] = defaultdict(set)
    risk_priority_totals: dict[str, list[float]] = defaultdict(list)
    for sid, summary in summaries.items():
        for risk_type in summary.get("risk_types", []):
            by_risk[risk_type].add(sid)
        for risk_type, value in summary.get("priority_scores", {}).items():
            if value > 0:
                risk_priority_totals[risk_type].append(float(value))

    risk_cards = []
    for risk_type in RISK_TYPE_ORDER:
        affected = by_risk.get(risk_type, set())
        risk_cards.append({
            "risk_type": risk_type,
            "risk_label": RISK_TYPES[risk_type],
            "affected_students": len(affected),
            "affected_rate": round(len(affected) / max(1, len(student_ids)) * 100, 1),
            "average_priority": round(sum(risk_priority_totals.get(risk_type, [])) / max(1, len(risk_priority_totals.get(risk_type, []))), 1),
        })

    mentor_rows = _mentor_rows(db, user)
    intervention_metrics = _intervention_metrics(db, student_ids)
    support_students = sum(1 for summary in summaries.values() if "discontinuation" in summary.get("risk_types", []))
    return {
        "department": user.department,
        "total_students": len(student_ids),
        "total_mentors": len(mentor_rows),
        "critical_students": sum(1 for s in summaries.values() if s.get("critical")),
        "high_risk_students": sum(1 for s in summaries.values() if s.get("high_risk")),
        "students_needing_action": sum(1 for s in summaries.values() if s.get("needs_action")),
        "open_alerts": len(alerts),
        "new_alerts": sum(alert.status == "NEW" for alert in alerts),
        "intervention_load": round(sum(float(alert.priority_score or 0) for alert in alerts), 1),
        "resolved_interventions": intervention_metrics["resolved_interventions"],
        "overdue_follow_ups": intervention_metrics["overdue_follow_ups"],
        "support_attention_students": support_students,
        "average_priority": round(sum(float(s.get("priority_score", 0)) for s in summaries.values()) / max(1, len(summaries)), 1),
        "risk_distribution": risk_cards,
        "risk_source": "risk_predictions",
        "alert_policy": {"priority_threshold": 60, "critical_override": True},
    }


def department_risk_overview(db: Session, user: User) -> dict:
    summary = department_summary(db, user)
    return {"department": user.department, "items": summary["risk_distribution"], "risk_source": "risk_predictions"}


def mentor_students(
    db: Session,
    user: User,
    mentor_id: str,
    *,
    query: str | None = None,
    section: str | None = None,
    risk_type: str | None = None,
    needs_action: bool | None = None,
) -> dict | None:
    mentor = db.scalar(select(Teacher).where(
        Teacher.id == mentor_id,
        Teacher.role == "mentor",
        Teacher.department == user.department,
    ))
    if not mentor:
        return None

    student_ids = list(db.scalars(select(Assignment.student_id).where(
        Assignment.teacher_id == mentor_id,
        Assignment.assignment_type == "mentor",
    )).all())
    summaries = student_summary(db, student_ids, include_support_attention=True)
    alerts = get_active_alerts(db, student_ids, user)
    counts = defaultdict(int)
    for alert in alerts:
        counts[alert.student_id] += 1

    students = {
        student.id: student
        for student in db.scalars(select(Student).where(Student.id.in_(student_ids))).all()
    }
    canonical_risk = normalize_risk_type(risk_type) if risk_type else None
    q = query.strip().lower() if query else None
    rows = []
    for sid in student_ids:
        student = students.get(sid)
        summary = summaries.get(sid, {})
        if not student:
            continue
        if q and q not in f"{student.id} {student.name}".lower():
            continue
        if section and student.section != section:
            continue
        if canonical_risk and canonical_risk not in summary.get("risk_types", []):
            continue
        if needs_action is not None and bool(summary.get("needs_action")) != needs_action:
            continue
        rows.append({
            **summary,
            "student_id": student.id,
            "student_name": student.name,
            "batch": student.batch,
            "section": student.section,
            "open_alerts": counts.get(student.id, 0),
        })

    rows.sort(key=lambda row: (row.get("needs_action", False), row.get("priority_score", 0)), reverse=True)
    return {
        "mentor_id": mentor.id,
        "mentor_name": mentor.name,
        "department": user.department,
        "assigned_students": len(student_ids),
        "returned_students": len(rows),
        "items": rows,
        "risk_source": "risk_predictions",
    }


def department_students(db: Session, user: User) -> list[dict]:
    students = db.scalars(select(Student).where(Student.department == user.department).order_by(Student.name.asc())).all()
    ids = [student.id for student in students]
    summaries = student_summary(db, ids, include_support_attention=True)
    return [
        {
            "student_id": student.id,
            "student_name": student.name,
            "batch": student.batch,
            "section": student.section,
            "department": student.department,
            "risk_score": summaries.get(student.id, {}).get("risk_score", 0.0),
            "priority_score": summaries.get(student.id, {}).get("priority_score", 0.0),
            "risk_level": summaries.get(student.id, {}).get("risk_level", "LOW"),
            "primary_risk": summaries.get(student.id, {}).get("primary_risk"),
            "needs_action": summaries.get(student.id, {}).get("needs_action", False),
        }
        for student in students
    ]
