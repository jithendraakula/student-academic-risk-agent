"""
Heuristic risk scorer.

Used now to seed realistic alerts/interventions data before real ML
models exist (Phase 4). The weighted rules here double as the first
draft of the explainability rule templates (Section 16 of the PRD) and
as a sanity check for what the trained models SHOULD learn once
Phase 4 fits scikit-learn models on this same data.

Every score is 0-100. Do not treat as production-grade - it is a seed
heuristic, not a substitute for the trained models.
"""


def clip(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def course_failure_risk(course_row) -> float:
    marks_gap = max(0, 55 - course_row["internal_marks"]) * 1.4
    attendance_gap = max(0, 75 - course_row["course_attendance_percentage"]) * 0.9
    trend_penalty = 12 if course_row["course_attendance_trend"] == "declining" else 0
    repeat_penalty = 15 * course_row["previous_course_attempts"]
    return clip(marks_gap + attendance_gap + trend_penalty + repeat_penalty)


def backlog_risk(sem_row) -> float:
    base = sem_row["current_backlog_count"] * 18
    growth = max(0, sem_row["backlog_growth_rate"]) * 25
    decline_penalty = 20 if sem_row["academic_decline_flag"] else 0
    repeat_penalty = 15 if sem_row["repeated_backlog_flag"] else 0
    return clip(base + growth + decline_penalty + repeat_penalty)


def gpa_threshold_risk(sem_row, gpa_threshold: float = 7.0) -> float:
    gap = max(0, gpa_threshold - sem_row["current_gpa"]) * 30
    trend_penalty = 15 if sem_row["gpa_change"] < 0 else 0
    return clip(gap + trend_penalty)


def attendance_shortage_risk(sem_row, attendance_threshold: float = 75.0) -> float:
    gap = max(0, attendance_threshold - sem_row["projected_final_attendance"]) * 2.2
    consecutive_penalty = min(20, sem_row["consecutive_absence_days"] * 2.5)
    return clip(gap + consecutive_penalty)


def support_attention_risk(sem_row) -> float:
    """Discontinuation risk, displayed to users as 'Support Attention Risk'."""
    absence_penalty = 25 if sem_row["prolonged_absence_flag"] else 0
    backlog_penalty = 15 if sem_row["repeated_backlog_flag"] else 0
    decline_penalty = 20 if sem_row["academic_decline_flag"] else 0
    engagement_penalty = 30 if sem_row["engagement_decline_flag"] else 0
    fee_penalty = 25 if sem_row["fee_status"] == "overdue" else 0
    return clip(absence_penalty + backlog_penalty + decline_penalty + engagement_penalty + fee_penalty)


def confidence_label(score: float) -> str:
    # Simple placeholder: mid-range scores are treated as lower confidence
    # until real model calibration exists in Phase 4.
    if score >= 70 or score <= 20:
        return "High"
    if 35 <= score <= 65:
        return "Medium"
    return "Medium"


def intervenability_label(risk_type: str, sem_row) -> str:
    if risk_type == "attendance" and not sem_row["academic_decline_flag"]:
        return "High"
    if risk_type == "support_attention":
        return "Medium"
    if sem_row["current_backlog_count"] >= 3:
        return "Low"
    return "Medium"


def contributing_factors(risk_type: str, sem_row) -> list[str]:
    factors = []
    if risk_type == "attendance":
        if sem_row["current_attendance_percentage"] < 75:
            factors.append("Attendance has dropped below the required threshold")
        if sem_row["consecutive_absence_days"] >= 4:
            factors.append(f"{int(sem_row['consecutive_absence_days'])} consecutive absences detected")
        if sem_row["attendance_trend"] == "declining":
            factors.append("Attendance trend is declining over recent weeks")
    elif risk_type == "gpa":
        if sem_row["current_gpa"] < 7.0:
            factors.append("Current GPA is below the configured threshold")
        if sem_row["gpa_change"] < 0:
            factors.append("GPA has declined compared to the previous semester")
    elif risk_type == "backlog":
        if sem_row["current_backlog_count"] > 0:
            factors.append(f"{int(sem_row['current_backlog_count'])} active backlog(s) on record")
        if sem_row["repeated_backlog_flag"]:
            factors.append("Repeated backlog history increases risk of further backlogs")
    elif risk_type == "support_attention":
        if sem_row["engagement_decline_flag"]:
            factors.append("Engagement with coursework has been declining")
        if sem_row["fee_status"] == "overdue":
            factors.append("Fee payment is overdue")
        if sem_row["prolonged_absence_flag"]:
            factors.append("Prolonged absence pattern detected")
    return factors or ["No significant risk factors detected"]


def suggested_action(risk_type: str) -> str:
    return {
        "attendance": "Schedule a check-in to understand the cause of absences",
        "gpa": "Recommend academic counseling and a study plan review",
        "backlog": "Connect student with subject-specific remedial support",
        "course": "Arrange targeted revision sessions for the at-risk course",
        "support_attention": "Reach out proactively for a supportive, non-academic conversation",
    }.get(risk_type, "Schedule a mentor check-in")