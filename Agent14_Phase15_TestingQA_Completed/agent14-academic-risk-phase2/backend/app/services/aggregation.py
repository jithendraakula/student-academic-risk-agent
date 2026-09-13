"""Single-source current risk/priority aggregation for all institutional roles."""
from __future__ import annotations

from collections import defaultdict
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import CourseFeature, RiskPrediction, SemesterFeature, Student
from app.services.alerts import get_active_alerts
from app.services.risk import _upsert_prediction
from app.services.risk_engine import (
    PriorityInputs,
    RISK_TYPES,
    calculate_priority,
    intervenability_score,
    urgency_score,
    should_create_alert,
)


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

    semester_values = [(sid, int(pair[0].semester)) for sid, pair in expected_by_student.items()]
    # Current dataset has one current semester per student; count all current-semester
    # courses in one grouped query instead of N queries.
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

    # Count existing canonical snapshots in one grouped query.
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
            _upsert_prediction(
                db,
                student.id,
                int(semester.semester),
                checkpoint,
                key,
                None,
                prediction,
                student_data,
            )

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
        primary = max(visible, key=lambda record: record.priority_score, default=None)
        highest_risk = max(visible, key=lambda record: record.risk_score, default=None)
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
        result[sid] = {
            "student_id": sid,
            "student_name": students[sid].name if sid in students else None,
            "department": students[sid].department if sid in students else None,
            "batch": students[sid].batch if sid in students else None,
            "section": students[sid].section if sid in students else None,
            "risk_score": round(highest_risk.risk_score, 1) if highest_risk else 0.0,
            "priority_score": round(primary.priority_score, 1) if primary else 0.0,
            "risk_level": primary.risk_level if primary else "LOW",
            "critical": any(record.risk_level == "CRITICAL" for record in visible),
            "high_risk": any(record.risk_level in {"HIGH", "CRITICAL"} for record in visible),
            "needs_action": any(
                should_create_alert(record.risk_score, record.risk_level, record.priority_score)
                for record in visible
            ),
            "primary_risk": primary.risk_type if primary else None,
            "risk_types": sorted({record.risk_type for record in visible}),
            "risk_scores": risk_scores,
            "priority_scores": priorities,
        }
    return result


def active_alerts(db: Session, student_ids: list[str], user=None):
    return get_active_alerts(db, student_ids, user)
