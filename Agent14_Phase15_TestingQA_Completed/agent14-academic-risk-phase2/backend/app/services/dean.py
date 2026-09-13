"""Institution-level Dean workspace built on the canonical risk store."""
from __future__ import annotations

from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AlertIntervention, RiskPrediction, Student, User
from app.services.aggregation import current_predictions, scope_metrics, student_summary
from app.services.alerts import get_active_alerts
from app.services.risk_engine import RISK_TYPE_ORDER, RISK_TYPES
from app.services.rbac import can_access_student


def _all_students(db: Session) -> list[Student]:
    return db.scalars(select(Student).order_by(Student.department.asc(), Student.name.asc())).all()


def institution_summary(db: Session, user: User) -> dict:
    students = _all_students(db)
    ids = [student.id for student in students]
    metrics = scope_metrics(db, ids, include_support_attention=True, user=user)
    all_alerts = db.scalars(select(AlertIntervention).where(AlertIntervention.student_id.in_(ids))).all() if ids else []
    resolved_interventions = sum(a.status == "RESOLVED" for a in all_alerts)
    overdue_follow_ups = sum(
        bool((a.data or {}).get("follow_up_date"))
        and str((a.data or {}).get("follow_up_date")) < __import__("datetime").date.today().isoformat()
        and a.status != "RESOLVED"
        for a in all_alerts
    )

    department_stats: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"students": 0, "critical": 0, "needs_action": 0, "priority_total": 0.0}
    )
    # The student summary is deliberately the same metric substrate used by HOD.
    summaries = student_summary(db, ids, include_support_attention=True)
    for student in students:
        summary = summaries.get(student.id, {})
        stats = department_stats[student.department]
        stats["students"] += 1
        stats["critical"] += int(bool(summary.get("critical")))
        stats["needs_action"] += int(bool(summary.get("needs_action")))
        stats["priority_total"] += float(summary.get("priority_score", 0.0))

    department_snapshot = []
    for department, stats in sorted(department_stats.items()):
        count = int(stats["students"])
        department_snapshot.append({
            "department": department,
            "students": count,
            "critical_students": int(stats["critical"]),
            "students_needing_action": int(stats["needs_action"]),
            "average_priority": round(float(stats["priority_total"]) / max(1, count), 1),
        })

    return {
        "total_students": metrics["monitored_students"],
        "departments": len(department_stats),
        "critical_students": metrics["critical_students"],
        "high_risk_students": metrics["high_risk_students"],
        "high_only_students": metrics["high_only_students"],
        "elevated_risk_students": metrics["elevated_risk_students"],
        "students_needing_action": metrics["students_needing_action"],
        "students_with_multiple_risks": metrics["students_with_multiple_risks"],
        "risk_signals": metrics["risk_signals"],
        "actionable_risk_signals": metrics["actionable_risk_signals"],
        "support_attention_students": next((x["affected_students"] for x in metrics["risk_distribution"] if x["risk_type"] == "discontinuation"), 0),
        "open_alerts": metrics["open_alerts"],
        "open_alert_students": metrics["open_alert_students"],
        "new_alerts": metrics["new_alerts"],
        "new_alert_students": metrics["new_alert_students"],
        "intervention_load": metrics["intervention_load"],
        "resolved_interventions": resolved_interventions,
        "overdue_follow_ups": overdue_follow_ups,
        "average_priority": metrics["average_priority"],
        "risk_distribution": metrics["risk_distribution"],
        "department_snapshot": department_snapshot,
        "metric_semantics": metrics["metric_semantics"],
        "risk_thresholds": metrics["risk_thresholds"],
        "risk_source": metrics["risk_source"],
        "alert_source": metrics["alert_source"],
        "alert_policy": metrics["alert_policy"],
    }

def department_comparison(db: Session, user: User) -> dict:
    students = _all_students(db)
    ids = [student.id for student in students]
    summaries = student_summary(db, ids, include_support_attention=True)
    alerts = get_active_alerts(db, ids, user)
    department_ids: dict[str, list[str]] = defaultdict(list)
    for student in students:
        department_ids[student.department].append(student.id)

    alerts_by_department: dict[str, list] = defaultdict(list)
    student_department = {student.id: student.department for student in students}
    for alert in alerts:
        alerts_by_department[student_department.get(alert.student_id, "UNKNOWN")].append(alert)

    rows = []
    for department in sorted(department_ids):
        dept_ids = department_ids[department]
        dept_summaries = [summaries[sid] for sid in dept_ids if sid in summaries]
        dept_alerts = alerts_by_department.get(department, [])
        affected_risk_types = {
            risk_type: len({sid for sid in dept_ids if risk_type in summaries.get(sid, {}).get("risk_types", [])})
            for risk_type in RISK_TYPE_ORDER
        }
        resolved = sum(a.status == "RESOLVED" for a in dept_alerts)
        overdue = sum(
            bool((a.data or {}).get("follow_up_date"))
            and str((a.data or {}).get("follow_up_date")) < __import__("datetime").date.today().isoformat()
            and a.status != "RESOLVED"
            for a in dept_alerts
        )
        rows.append({
            "department": department,
            "total_students": len(dept_ids),
            "critical_students": sum(1 for s in dept_summaries if s.get("critical")),
            "high_risk_students": sum(1 for s in dept_summaries if s.get("high_risk")),
            "students_needing_action": sum(1 for s in dept_summaries if s.get("needs_action")),
            "average_priority": round(sum(float(s.get("priority_score", 0)) for s in dept_summaries) / max(1, len(dept_summaries)), 1),
            "active_interventions": sum(a.status != "RESOLVED" for a in dept_alerts),
            "open_alert_students": len({a.student_id for a in dept_alerts}),
            "resolved_interventions": resolved,
            "overdue_follow_ups": overdue,
            "new_alerts": sum(a.status == "NEW" for a in dept_alerts),
            "support_attention_students": affected_risk_types.get("discontinuation", 0),
            "risk_counts": affected_risk_types,
            "risk_signal_count": sum(affected_risk_types.values()),
            "multiple_risk_students": sum(1 for sid in dept_ids if len([r for r in RISK_TYPE_ORDER if r in summaries.get(sid, {}).get("risk_types", [])]) >= 2),
            "risk_source": "risk_predictions",
        })
    rows.sort(key=lambda row: (row["students_needing_action"], row["critical_students"], row["average_priority"]), reverse=True)
    return {
        "items": rows,
        "risk_source": "risk_predictions",
        "alert_policy": {"priority_threshold": 60, "critical_override": True},
    }


def risk_heatmap(db: Session, user: User) -> dict:
    students = _all_students(db)
    ids = [student.id for student in students]
    records = current_predictions(db, ids)
    by_department: dict[str, list[str]] = defaultdict(list)
    for student in students:
        by_department[student.department].append(student.id)

    rows = []
    for department in sorted(by_department):
        dept_ids = set(by_department[department])
        row: dict[str, float | str] = {"department": department}
        for risk_type in RISK_TYPE_ORDER:
            affected = {
                record.student_id
                for record in records
                if record.student_id in dept_ids
                and record.risk_type == risk_type
                and record.risk_score >= 40.0
            }
            row[risk_type] = round(len(affected) / max(1, len(dept_ids)) * 100, 1)
        rows.append(row)
    return {
        "items": rows,
        "risk_source": "risk_predictions",
        "risk_threshold": 40.0,
        "metric_meaning": "Percent of department students with elevated (HIGH/CRITICAL) risk for this risk type.",
    }


def priority_queue(db: Session, user: User, limit: int = 25) -> dict:
    students = _all_students(db)
    ids = [student.id for student in students]
    summaries = student_summary(db, ids, include_support_attention=True)
    rows = []
    for student in students:
        summary = summaries.get(student.id, {})
        if not summary.get("needs_action"):
            continue
        rows.append({
            "student_id": student.id,
            "roll_number": student.roll_number,
            "student_name": student.name,
            "department": student.department,
            "batch": student.batch,
            "section": student.section,
            "primary_risk": summary.get("primary_risk"),
            "risk_score": summary.get("risk_score", 0.0),
            "priority_score": summary.get("priority_score", 0.0),
            "risk_level": summary.get("risk_level", "LOW"),
            "critical": bool(summary.get("critical")),
            "risk_types": summary.get("risk_types", []),
        })
    rows.sort(key=lambda row: (row["critical"], row["priority_score"], row["risk_score"]), reverse=True)
    return {
        "items": rows[: max(1, min(int(limit), 100))],
        "total_needing_action": len(rows),
        "risk_source": "risk_predictions",
    }


def department_students(db: Session, user: User, department: str) -> dict | None:
    valid_departments = {row[0] for row in db.query(Student.department).distinct().all()}
    if department not in valid_departments:
        return None
    students = db.scalars(select(Student).where(Student.department == department).order_by(Student.name.asc())).all()
    ids = [student.id for student in students]
    summaries = student_summary(db, ids, include_support_attention=True)
    return {
        "department": department,
        "items": [
            {
                "student_id": student.id,
                "student_name": student.name,
                "roll_number": student.roll_number,
                "batch": student.batch,
                "section": student.section,
                "department": student.department,
                "risk_score": summaries.get(student.id, {}).get("risk_score", 0.0),
                "priority_score": summaries.get(student.id, {}).get("priority_score", 0.0),
                "risk_level": summaries.get(student.id, {}).get("risk_level", "LOW"),
                "primary_risk": summaries.get(student.id, {}).get("primary_risk"),
                "needs_action": summaries.get(student.id, {}).get("needs_action", False),
                "risk_types": summaries.get(student.id, {}).get("risk_types", []),
            }
            for student in students
        ],
        "risk_source": "risk_predictions",
    }
