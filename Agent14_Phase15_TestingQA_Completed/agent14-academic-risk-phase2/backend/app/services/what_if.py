"""Non-persistent academic What-If simulator.

The simulator deliberately never writes RiskPrediction, Student, or feature rows.
It clones the current feature snapshot in memory, applies user-supplied academic
changes, re-runs the existing ML models, and calculates priority for comparison.
"""
from __future__ import annotations

from pathlib import Path
import sys
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.domain import CourseFeature, SemesterFeature, Student, User
from app.schemas.what_if import WhatIfRequest
from app.services.rbac import can_access_student, can_view_support_attention_risk
from app.services.risk_engine import PriorityInputs, calculate_priority, intervenability_score, urgency_score


def _scalar(value):
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


def _features(data: dict) -> dict:
    return {key: _scalar(value) for key, value in data.items()}


def _trend(new_value: float, old_value: float) -> str:
    if new_value > old_value + 1:
        return "improving"
    if new_value < old_value - 1:
        return "declining"
    return "stable"


def _priority(risk_type: str, prediction: dict, student_data: dict) -> dict:
    iv = intervenability_score(risk_type, student_data)
    urg = urgency_score(risk_type, student_data)
    priority = calculate_priority(PriorityInputs(
        float(prediction["risk_score"]),
        str(prediction["confidence"]),
        iv,
        urg,
    ))
    return {
        **prediction,
        "intervenability_score": iv,
        "priority_score": priority,
    }


def _run(student_data: dict, course_data: list[dict]) -> dict:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    try:
        from ml.predictor import predict_all_risks
        result = predict_all_risks(student_data, course_data)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Risk prediction service unavailable: {exc}") from exc

    for risk_type in ("backlog", "gpa_threshold", "attendance_shortage", "discontinuation"):
        result["risks"][risk_type] = _priority(risk_type, result["risks"][risk_type], student_data)
    result["risks"]["course_failure"] = [
        _priority("course_failure", {**prediction, "course_id": prediction.get("course_id")}, {**student_data, **prediction})
        for prediction in result["risks"].get("course_failure", [])
    ]
    return result


def _risk_summary(result: dict, include_support: bool) -> dict:
    rows = []
    for risk_type, prediction in result["risks"].items():
        if risk_type == "course_failure":
            for item in prediction:
                if item.get("course_id"):
                    rows.append((risk_type, item.get("course_id"), item))
        elif include_support or risk_type != "discontinuation":
            rows.append((risk_type, None, prediction))
    primary = max(rows, key=lambda item: float(item[2].get("priority_score", 0)), default=None)
    return {
        "risk_score": round(float(max((float(item[2].get("risk_score", 0)) for item in rows), default=0)), 1),
        "priority_score": round(float(primary[2].get("priority_score", 0)) if primary else 0, 1),
        "primary_risk": primary[0] if primary else None,
        "primary_course_id": primary[1] if primary and primary[0] == "course_failure" else None,
        "risk_level": primary[2].get("risk_level") if primary else "LOW",
    }


def _apply_changes(student_data: dict, course_data: list[dict], payload: WhatIfRequest) -> tuple[dict, list[dict], dict]:
    adjusted = dict(student_data)
    changes = {}

    if payload.attendance_percentage is not None:
        old = float(adjusted.get("current_attendance_percentage", 0) or 0)
        new = float(payload.attendance_percentage)
        adjusted["current_attendance_percentage"] = new
        adjusted["attendance_last_30_days"] = new
        adjusted["projected_final_attendance"] = new
        adjusted["attendance_trend"] = _trend(new, old)
        changes["attendance_percentage"] = {"from": old, "to": new, "delta": round(new - old, 2)}

    if payload.gpa is not None:
        old = float(adjusted.get("current_gpa", 0) or 0)
        new = float(payload.gpa)
        adjusted["current_gpa"] = new
        previous = float(adjusted.get("previous_gpa", old) or old)
        adjusted["gpa_change"] = round(new - previous, 3)
        changes["gpa"] = {"from": old, "to": new, "delta": round(new - old, 2)}

    if payload.backlog_count is not None:
        old = int(adjusted.get("current_backlog_count", 0) or 0)
        new = int(payload.backlog_count)
        adjusted["current_backlog_count"] = new
        previous = int(adjusted.get("previous_backlog_count", old) or old)
        adjusted["new_backlogs_last_semester"] = max(0, new - previous)
        adjusted["backlog_growth_rate"] = round((new - previous) / max(1, previous), 3)
        adjusted["repeated_backlog_flag"] = bool(new > 0 and adjusted.get("repeated_backlog_subject_count", 0))
        changes["backlog_count"] = {"from": old, "to": new, "delta": new - old}

    if payload.assignment_completion_rate is not None:
        old = float(adjusted.get("assignment_completion_rate", 0) or 0)
        new = float(payload.assignment_completion_rate)
        adjusted["assignment_completion_rate"] = new
        adjusted["assessment_participation_rate"] = max(float(adjusted.get("assessment_participation_rate", 0) or 0), new)
        changes["assignment_completion_rate"] = {"from": old, "to": new, "delta": round(new - old, 4)}

    adjusted_courses = [dict(course) for course in course_data]
    if payload.course:
        match = next((course for course in adjusted_courses if str(course.get("course_id")) == payload.course.course_id), None)
        if match is None:
            raise HTTPException(status_code=404, detail="Course not found in the student's current semester")
        course_changes = {}
        for field in (
            "internal_marks", "midterm_marks", "quiz_average", "assignment_average",
            "practical_marks", "course_attendance_percentage", "assignment_completion_rate",
        ):
            value = getattr(payload.course, field)
            if value is not None:
                old = float(match.get(field, 0) or 0)
                match[field] = float(value)
                course_changes[field] = {"from": old, "to": float(value), "delta": round(float(value) - old, 2)}
        if "course_attendance_percentage" in course_changes:
            old = float(course_changes["course_attendance_percentage"]["from"])
            new = float(course_changes["course_attendance_percentage"]["to"])
            match["course_attendance_trend"] = _trend(new, old)
        changes["course"] = {"course_id": payload.course.course_id, "fields": course_changes}

    return adjusted, adjusted_courses, changes


def simulate_student(db: Session, student_id: str, user: User, payload: WhatIfRequest) -> dict:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not can_access_student(db, user, student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student is outside your access scope")
    if not payload.has_change():
        raise HTTPException(status_code=400, detail="Provide at least one academic what-if change")

    semester = db.scalars(
        select(SemesterFeature)
        .where(SemesterFeature.student_id == student_id)
        .order_by(SemesterFeature.id.desc())
    ).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Current semester features not found")
    courses = db.scalars(
        select(CourseFeature)
        .where(CourseFeature.student_id == student_id, CourseFeature.semester == semester.semester)
        .order_by(CourseFeature.id.asc())
    ).all()

    baseline_student = {"student_id": student.id, **_features(semester.data)}
    baseline_courses = [_features(course.data) for course in courses]
    adjusted_student, adjusted_courses, changes = _apply_changes(baseline_student, baseline_courses, payload)

    baseline = _run(baseline_student, baseline_courses)
    simulated = _run(adjusted_student, adjusted_courses)
    include_support = can_view_support_attention_risk(user.role)

    def visible(result):
        if include_support:
            return result
        clean = {**result, "risks": dict(result["risks"])}
        clean["risks"].pop("discontinuation", None)
        return clean

    baseline_visible = visible(baseline)
    simulated_visible = visible(simulated)
    baseline_summary = _risk_summary(baseline_visible, include_support)
    simulated_summary = _risk_summary(simulated_visible, include_support)

    risk_changes = {}
    for key in ("backlog", "gpa_threshold", "attendance_shortage", "discontinuation"):
        if key in simulated_visible["risks"] and key in baseline_visible["risks"]:
            b = baseline_visible["risks"][key]
            s = simulated_visible["risks"][key]
            risk_changes[key] = {
                "risk_score_delta": round(float(s["risk_score"]) - float(b["risk_score"]), 1),
                "priority_score_delta": round(float(s["priority_score"]) - float(b["priority_score"]), 1),
                "risk_level_changed": b["risk_level"] != s["risk_level"],
            }
    baseline_cf = {p.get("course_id"): p for p in baseline_visible["risks"].get("course_failure", [])}
    simulated_cf = {p.get("course_id"): p for p in simulated_visible["risks"].get("course_failure", [])}
    for cid, b in baseline_cf.items():
        if cid in simulated_cf:
            s = simulated_cf[cid]
            risk_changes[f"course_failure:{cid}"] = {
                "risk_score_delta": round(float(s["risk_score"]) - float(b["risk_score"]), 1),
                "priority_score_delta": round(float(s["priority_score"]) - float(b["priority_score"]), 1),
                "risk_level_changed": b["risk_level"] != s["risk_level"],
            }

    return {
        "simulation": {
            "persistent": False,
            "source": "current_feature_snapshot",
            "semester": int(semester.semester),
            "checkpoint_week": int(baseline_student.get("checkpoint_week", 6) or 6),
            "changes": changes,
        },
        "student": {
            "student_id": student.id,
            "student_name": student.name,
            "department": student.department,
            "batch": student.batch,
            "section": student.section,
        },
        "baseline": {"summary": baseline_summary, "risks": baseline_visible["risks"]},
        "simulated": {"summary": simulated_summary, "risks": simulated_visible["risks"]},
        "changes": risk_changes,
        "interpretation": {
            "overall_priority_delta": round(simulated_summary["priority_score"] - baseline_summary["priority_score"], 1),
            "improved": simulated_summary["priority_score"] < baseline_summary["priority_score"],
            "warning": "What-if results are estimates only and do not update the student's academic record or canonical risk history.",
        },
    }
