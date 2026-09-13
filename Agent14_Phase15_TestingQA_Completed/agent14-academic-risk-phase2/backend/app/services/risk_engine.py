"""Canonical risk, priority, and alert policy for Agent 14.

Risk answers *how much risk is predicted*. Priority answers *how strongly the
institution should act now*. Alerts are action records derived only from the
canonical prediction snapshots.
"""
from __future__ import annotations

from dataclasses import dataclass

RISK_TYPES = {
    "course_failure": "Course Failure Risk",
    "backlog": "Backlog Accumulation Risk",
    "gpa_threshold": "GPA Threshold Risk",
    "attendance_shortage": "Attendance Shortage Risk",
    "discontinuation": "Support Attention Risk",
}

# Legacy/demo dataset names are normalized here so every layer uses one key.
RISK_TYPE_ALIASES = {
    "attendance": "attendance_shortage",
    "gpa": "gpa_threshold",
    "backlog": "backlog",
    "support_attention": "discontinuation",
    "course": "course_failure",
    "course_failure_risk": "course_failure",
    "attendance_risk": "attendance_shortage",
    "gpa_risk": "gpa_threshold",
}

DISPLAY_TO_RISK_TYPE = {label: key for key, label in RISK_TYPES.items()}

RISK_TYPE_ORDER = tuple(RISK_TYPES.keys())

# One policy for the whole product. This is intentionally simple enough for
# mentors/HOD/Dean to explain during a demo and deterministic enough for tests.
ALERT_PRIORITY_THRESHOLD = 60.0
ALERT_CRITICAL_OVERRIDE = True
HEATMAP_RISK_THRESHOLD = 50.0

@dataclass(frozen=True)
class PriorityInputs:
    risk_score: float
    confidence: str
    intervenability_score: float
    urgency_score: float


def normalize_risk_type(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in RISK_TYPES:
        return normalized
    if normalized in RISK_TYPE_ALIASES:
        return RISK_TYPE_ALIASES[normalized]
    return None


def risk_label(risk_type: str) -> str:
    canonical = normalize_risk_type(risk_type)
    return RISK_TYPES.get(canonical or risk_type, str(risk_type))


def intervenability_score(risk_type: str, student_data: dict) -> float:
    risk_type = normalize_risk_type(risk_type) or risk_type
    attendance = float(student_data.get("current_attendance_percentage", 80) or 80)
    backlog = int(student_data.get("current_backlog_count", 0) or 0)
    decline = bool(
        student_data.get("academic_decline_flag", False)
        or student_data.get("engagement_decline_flag", False)
    )
    if risk_type == "attendance_shortage":
        return 90.0 if attendance >= 65 and not decline else 70.0
    if risk_type == "course_failure":
        return 82.0 if float(student_data.get("assignment_completion_rate", 0.6) or 0.6) >= 0.5 else 68.0
    if risk_type == "backlog":
        return 80.0 if backlog <= 2 else 55.0
    if risk_type == "gpa_threshold":
        return 85.0 if float(student_data.get("current_gpa", 7) or 7) >= 6 else 65.0
    # Support Attention is restricted to care/support workflows. It remains
    # actionable through mentor/HOD/Dean support coordination.
    return 60.0


def urgency_score(risk_type: str, student_data: dict) -> float:
    risk_type = normalize_risk_type(risk_type) or risk_type
    if risk_type == "attendance_shortage" and int(student_data.get("consecutive_absence_days", 0) or 0) >= 4:
        return 95.0
    if risk_type == "course_failure" and float(student_data.get("assignment_completion_rate", 1) or 1) < 0.5:
        return 85.0
    if risk_type == "backlog" and int(student_data.get("current_backlog_count", 0) or 0) >= 3:
        return 90.0
    if risk_type == "gpa_threshold" and float(student_data.get("gpa_change", 0) or 0) < -0.5:
        return 85.0
    if risk_type == "discontinuation" and bool(student_data.get("prolonged_absence_flag", False)):
        return 90.0
    return 55.0


def calculate_priority(inputs: PriorityInputs) -> float:
    confidence_weight = {
        "HIGH": 1.0,
        "MEDIUM": 0.85,
        "LOW": 0.70,
    }.get(inputs.confidence.upper(), 0.70)
    weighted_risk = inputs.risk_score * confidence_weight
    return round(
        min(
            100.0,
            0.60 * weighted_risk
            + 0.25 * inputs.intervenability_score
            + 0.15 * inputs.urgency_score,
        ),
        1,
    )


def should_create_alert(risk_score: float, risk_level: str, priority_score: float) -> bool:
    """Canonical alert decision used by every role/dashboard."""
    if ALERT_CRITICAL_OVERRIDE and str(risk_level).upper() == "CRITICAL":
        return True
    return float(priority_score) >= ALERT_PRIORITY_THRESHOLD


def risk_band_priority(risk_score: float) -> str:
    score = float(risk_score)
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MODERATE"
    return "LOW"
