"""Canonical current-risk aggregation and metric semantics for Agent 14."""
from __future__ import annotations

from collections import defaultdict
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import CourseFeature, RiskPrediction, SemesterFeature, Student
from app.services.alerts import get_active_alerts
from app.services.risk import _upsert_prediction
from app.services.risk_engine import (
    PriorityInputs,
    RISK_TYPES,
    RISK_TYPE_ORDER,
    calculate_priority,
    intervenability_score,
    should_create_alert,
    urgency_score,
)

# Product metric semantics. These are deliberately centralized so every role
# (Mentor, HOD, Dean) speaks the same language.
ELEVATED_RISK_THRESHOLD = 40.0  # HIGH + CRITICAL risk bands
ALERT_PRIORITY_THRESHOLD = 60.0


def metric_definitions() -> dict[str, dict[str, str]]:
    return {
        "monitored_students": {
            "meaning": "Unique students inside the viewer's authorized scope.",
            "unit": "students",
        },
        "elevated_risk_students": {
            "meaning": "Unique students with at least one risk score at or above 40 (HIGH or CRITICAL).",
            "unit": "students",
        },
        "high_risk_students": {
            "meaning": "Unique students with at least one HIGH or CRITICAL risk.",
            "unit": "students",
        },
        "critical_students": {
            "meaning": "Unique students with at least one CRITICAL risk.",
            "unit": "students",
        },
        "students_needing_action": {
            "meaning": "Unique students with at least one risk signal that satisfies the canonical alert policy.",
            "unit": "students",
        },
        "risk_signals": {
            "meaning": "Unique student-risk-type combinations at elevated risk; multiple risks on one student count as multiple signals.",
            "unit": "signals",
        },
        "actionable_risk_signals": {
            "meaning": "Unique student-risk-type combinations that satisfy the canonical alert policy.",
            "unit": "signals",
        },
        "open_alerts": {
            "meaning": "Active AlertIntervention work items. One student can have more than one open alert.",
            "unit": "alerts",
        },
        "open_alert_students": {
            "meaning": "Unique students represented by at least one open alert.",
            "unit": "students",
        },
    }


def _scalar_value(value):
    if value in (None, "", "None"):
        return None
    if isinstance(value, str):
        if value in ("True", "False"):
            return value == "True"
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except ValueError:
            return value
    return value


def ensure_current_predictions(db: Session, student_ids: list[str] | None = None) -> None:
    """Generate missing current prediction snapshots in batches with bounded DB work."""
    ids = student_ids if student_ids is not None else list(db.scalars(select(Student.id)).all())
    if not ids:
        return

    students = db.scalars(select(Student).where(Student.id.in_(ids))).all()
    semesters = db.scalars(
        select(SemesterFeature)
        .where(SemesterFeature.student_id.in_(ids))
        .order_by(SemesterFeature.id.desc())
    ).all()
    latest_semester: dict[str, SemesterFeature] = {}
    for semester in semesters:
        latest_semester.setdefault(semester.student_id, semester)

    expected_by_student: dict[str, tuple[SemesterFeature, int]] = {}
    for sid in ids:
        semester = latest_semester.get(sid)
        if semester:
            expected_by_student[sid] = (semester, 4)

    if not expected_by_student:
        return

    course_counts = {
        (row[0], int(row[1])): int(row[2])
        for row in db.execute(
            select(CourseFeature.student_id, CourseFeature.semester, func.count(CourseFeature.id))
            .where(CourseFeature.student_id.in_(ids))
            .group_by(CourseFeature.student_id, CourseFeature.semester)
        ).all()
    }
    for sid, (semester, _) in list(expected_by_student.items()):
        expected_by_student[sid] = (semester, 4 + int(course_counts.get((sid, int(semester.semester)), 0)))

    current_counts = {
        (row[0], int(row[1]), int(row[2])): int(row[3])
        for row in db.execute(
            select(RiskPrediction.student_id, RiskPrediction.semester, RiskPrediction.checkpoint_week, func.count(RiskPrediction.id))
            .where(RiskPrediction.student_id.in_(ids))
            .group_by(RiskPrediction.student_id, RiskPrediction.semester, RiskPrediction.checkpoint_week)
        ).all()
    }
    missing_ids = []
    for sid, (semester, expected) in expected_by_student.items():
        checkpoint = int((semester.data or {}).get("checkpoint_week", 6) or 6)
        if int(current_counts.get((sid, int(semester.semester), checkpoint), 0)) < expected:
            missing_ids.append(sid)

    if not missing_ids:
        return

    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from ml.predictor import predict_course_batch, predict_student_batch

    student_rows = []
    student_objs = []
    course_students = []
    course_rows = []
    missing_set = set(missing_ids)
    for student in students:
        if student.id not in missing_set:
            continue
        pair = expected_by_student.get(student.id)
        if not pair:
            continue
        semester, _ = pair
        student_data = {
            "student_id": student.id,
            **{k: _scalar_value(v) for k, v in (semester.data or {}).items()},
        }
        student_rows.append(student_data)
        student_objs.append((student, semester, student_data))
        courses = db.scalars(
            select(CourseFeature).where(
                CourseFeature.student_id == student.id,
                CourseFeature.semester == semester.semester,
            )
        ).all()
        for course in courses:
            course_data = {k: _scalar_value(v) for k, v in (course.data or {}).items()}
            course_rows.append(course_data)
            course_students.append((student, semester, course, student_data))

    student_predictions = predict_student_batch(student_rows)
    course_predictions = predict_course_batch(
        [row[3] for row in course_students],
        course_rows,
    )

    for idx, (student, semester, student_data) in enumerate(student_objs):
        checkpoint = int(student_data.get("checkpoint_week", 6) or 6)
        for key in ("backlog", "gpa_threshold", "attendance_shortage", "discontinuation"):
            prediction = student_predictions[key][idx]
            iv = intervenability_score(key, student_data)
            urgency = urgency_score(key, student_data)
            prediction["intervenability_score"] = iv
            prediction["priority_score"] = calculate_priority(
                PriorityInputs(float(prediction["risk_score"]), str(prediction["confidence"]), iv, urgency)
            )
            _upsert_prediction(db, student.id, int(semester.semester), checkpoint, key, None, prediction, student_data)

    for prediction, (student, semester, course, student_data) in zip(course_predictions, course_students):
        iv = intervenability_score("course_failure", {**student_data, **prediction})
        urgency = urgency_score("course_failure", {**student_data, **prediction})
        prediction["intervenability_score"] = iv
        prediction["priority_score"] = calculate_priority(
            PriorityInputs(float(prediction["risk_score"]), str(prediction["confidence"]), iv, urgency)
        )
        prediction["course_id"] = course.course_id
        _upsert_prediction(
            db,
            student.id,
            int(semester.semester),
            int(student_data.get("checkpoint_week", 6) or 6),
            "course_failure",
            course.course_id,
            prediction,
            student_data,
        )
    db.commit()


def current_predictions(db: Session, student_ids: list[str]) -> list[RiskPrediction]:
    if not student_ids:
        return []
    ensure_current_predictions(db, student_ids)
    records = db.scalars(
        select(RiskPrediction).where(RiskPrediction.student_id.in_(student_ids))
    ).all()
    latest: dict[tuple[str, str, str | None], RiskPrediction] = {}
    for record in records:
        key = (record.student_id, record.risk_type, record.course_id)
        if key not in latest or (
            record.semester,
            record.checkpoint_week,
            record.id,
        ) > (
            latest[key].semester,
            latest[key].checkpoint_week,
            latest[key].id,
        ):
            latest[key] = record
    return list(latest.values())


def student_summary(db: Session, student_ids: list[str], *, include_support_attention: bool = False) -> dict[str, dict]:
    if not student_ids:
        return {}
    students = {
        student.id: student
        for student in db.scalars(select(Student).where(Student.id.in_(student_ids))).all()
    }
    records = current_predictions(db, student_ids)
    by_student: dict[str, list[RiskPrediction]] = defaultdict(list)
    for record in records:
        by_student[record.student_id].append(record)

    result: dict[str, dict] = {}
    for sid in student_ids:
        rows = by_student.get(sid, [])
        visible = [record for record in rows if include_support_attention or record.risk_type != "discontinuation"]
        elevated = [record for record in visible if float(record.risk_score) >= ELEVATED_RISK_THRESHOLD]
        actionable = [
            record for record in visible
            if should_create_alert(record.risk_score, record.risk_level, record.priority_score)
        ]

        # Course failure can have several course rows. For student-level risk
        # metrics, each risk type is counted once; course detail remains available
        # in the underlying prediction rows.
        elevated_types = {record.risk_type for record in elevated}
        actionable_types = {record.risk_type for record in actionable}
        elevated_by_type: dict[str, list[RiskPrediction]] = defaultdict(list)
        for record in elevated:
            elevated_by_type[record.risk_type].append(record)

        primary = max(actionable or elevated or visible, key=lambda record: record.priority_score, default=None)
        highest_risk = max(elevated or visible, key=lambda record: record.risk_score, default=None)
        risk_scores = {
            key: round(max((r.risk_score for r in visible if r.risk_type == key), default=0.0), 1)
            for key in RISK_TYPES
            if include_support_attention or key != "discontinuation"
        }
        priorities = {
            key: round(max((r.priority_score for r in visible if r.risk_type == key), default=0.0), 1)
            for key in RISK_TYPES
            if include_support_attention or key != "discontinuation"
        }
        # Expose a student-level risk breakdown so every queue row can show
        # exactly which risk signal(s) the student belongs to. For course
        # failure, keep the highest-scoring course and all affected course ids.
        risk_breakdown = []
        for key in RISK_TYPE_ORDER:
            if not include_support_attention and key == "discontinuation":
                continue
            matching = [r for r in visible if r.risk_type == key]
            if not matching:
                continue
            top = max(matching, key=lambda r: (float(r.priority_score or 0), float(r.risk_score or 0), r.id))
            risk_breakdown.append({
                "risk_type": key,
                "risk_label": RISK_TYPES.get(key, key),
                "risk_level": top.risk_level,
                "risk_score": round(float(top.risk_score or 0), 1),
                "priority_score": round(float(top.priority_score or 0), 1),
                "actionable": any(should_create_alert(r.risk_score, r.risk_level, r.priority_score) for r in matching),
                "elevated": any(float(r.risk_score or 0) >= ELEVATED_RISK_THRESHOLD for r in matching),
                "course_ids": sorted({r.course_id for r in matching if r.course_id}),
            })
        risk_breakdown.sort(key=lambda item: (item["actionable"], item["priority_score"], item["risk_score"]), reverse=True)
        risk_level = primary.risk_level if primary else (highest_risk.risk_level if highest_risk else "LOW")
        result[sid] = {
            "student_id": sid,
            "student_name": students[sid].name if sid in students else None,
            "roll_number": students[sid].roll_number if sid in students else None,
            "department": students[sid].department if sid in students else None,
            "batch": students[sid].batch if sid in students else None,
            "section": students[sid].section if sid in students else None,
            # The summary status must describe one coherent primary signal: its
            # risk score, priority, and level all come from the same prediction.
            # The separate highest_risk_score is retained for analytical use.
            "risk_score": round(primary.risk_score, 1) if primary else 0.0,
            "highest_risk_score": round(highest_risk.risk_score, 1) if highest_risk else 0.0,
            "priority_score": round(primary.priority_score, 1) if primary else 0.0,
            "risk_level": risk_level,
            "critical": any(record.risk_level == "CRITICAL" for record in elevated),
            "high_risk": bool(elevated),
            "needs_action": bool(actionable),
            "primary_risk": primary.risk_type if primary else None,
            "risk_types": sorted(elevated_types),
            "actionable_risk_types": sorted(actionable_types),
            "risk_signal_count": len(elevated_types),
            "actionable_risk_signal_count": len(actionable_types),
            "multiple_risks": len(elevated_types) >= 2,
            "risk_scores": risk_scores,
            "priority_scores": priorities,
            "risk_breakdown": risk_breakdown,
        }
    return result


def scope_metrics(
    db: Session,
    student_ids: Iterable[str],
    *,
    include_support_attention: bool = True,
    user=None,
    summaries: dict[str, dict] | None = None,
) -> dict:
    """Return the canonical KPI contract for a role's authorized student scope."""
    ids = list(dict.fromkeys(str(sid) for sid in student_ids))
    if summaries is None:
        summaries = student_summary(
            db,
            ids,
            include_support_attention=include_support_attention,
        )
    alerts = get_active_alerts(db, ids, user) if ids else []

    critical_students = {sid for sid, s in summaries.items() if s.get("critical")}
    high_risk_students = {sid for sid, s in summaries.items() if s.get("high_risk")}
    elevated_students = {sid for sid, s in summaries.items() if s.get("risk_types")}
    open_alert_students = {alert.student_id for alert in alerts}
    action_students = {sid for sid, s in summaries.items() if s.get("needs_action") and sid in open_alert_students}
    multiple_risk_students = {sid for sid, s in summaries.items() if s.get("multiple_risks")}

    risk_distribution = []
    for risk_type in RISK_TYPE_ORDER:
        affected_students = {
            sid for sid, summary in summaries.items() if risk_type in summary.get("risk_types", [])
        }
        actionable_students = {
            sid for sid, summary in summaries.items() if risk_type in summary.get("actionable_risk_types", [])
        }
        priorities = [
            float(summary.get("priority_scores", {}).get(risk_type, 0.0))
            for sid, summary in summaries.items()
            if risk_type in summary.get("risk_types", [])
        ]
        risk_distribution.append({
            "risk_type": risk_type,
            "risk_label": RISK_TYPES[risk_type],
            "affected_students": len(affected_students),
            "affected_rate": round(len(affected_students) / max(1, len(ids)) * 100, 1),
            "actionable_students": len(actionable_students),
            "average_priority": round(sum(priorities) / max(1, len(priorities)), 1),
        })

    return {
        "monitored_students": len(ids),
        "elevated_risk_students": len(elevated_students),
        "critical_students": len(critical_students),
        "high_risk_students": len(high_risk_students),
        "high_only_students": len(high_risk_students - critical_students),
        "students_needing_action": len(action_students),
        "students_with_multiple_risks": len(multiple_risk_students),
        "risk_signals": sum(int(s.get("risk_signal_count", 0)) for s in summaries.values()),
        "actionable_risk_signals": sum(int(s.get("actionable_risk_signal_count", 0)) for s in summaries.values()),
        "open_alerts": len(alerts),
        "open_alert_students": len({alert.student_id for alert in alerts}),
        "new_alerts": sum(alert.status == "NEW" for alert in alerts),
        "new_alert_students": len({alert.student_id for alert in alerts if alert.status == "NEW"}),
        "intervention_load": round(sum(float(alert.priority_score or 0.0) for alert in alerts), 1),
        "average_priority": round(
            sum(float(summary.get("priority_score", 0.0)) for summary in summaries.values()) / max(1, len(summaries)),
            1,
        ),
        "risk_distribution": risk_distribution,
        "metric_semantics": metric_definitions(),
        "risk_source": "risk_predictions",
        "alert_source": "active_alert_interventions",
        "alert_policy": {"priority_threshold": ALERT_PRIORITY_THRESHOLD, "critical_override": True},
        "risk_thresholds": {"elevated": ELEVATED_RISK_THRESHOLD, "critical": 60.0},
    }
