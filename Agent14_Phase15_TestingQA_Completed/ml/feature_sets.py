from __future__ import annotations

COMMON_EXCLUDED = {
    "student_id", "roll_number", "cohort", "academic_year", "semester", "checkpoint_week",
    "snapshot_type", "academic_year_outcome", "outcome_horizon", "course_failed", "new_backlog", "gpa_below_threshold", "attendance_shortage", "discontinued",
    "_archetype",
}
COURSE_EXCLUDED = COMMON_EXCLUDED | {"course_id", "course_name"}
STUDENT_EXCLUDED = COMMON_EXCLUDED

FEATURE_EXPLANATIONS = {
    "current_attendance_percentage": "Current attendance percentage",
    "attendance_last_30_days": "Attendance over the last 30 days",
    "attendance_trend": "Recent attendance trend",
    "consecutive_absence_days": "Consecutive absence days",
    "total_absent_days": "Total absent days",
    "projected_final_attendance": "Projected final attendance",
    "current_backlog_count": "Current backlog count",
    "previous_backlog_count": "Previous backlog count",
    "total_historical_backlogs": "Historical backlog count",
    "repeated_backlog_subject_count": "Repeated backlog subjects",
    "backlog_growth_rate": "Backlog growth rate",
    "current_gpa": "Current GPA",
    "previous_gpa": "Previous GPA",
    "current_cgpa": "Current CGPA",
    "gpa_change": "GPA change",
    "internal_marks_average": "Average internal assessment marks",
    "midterm_marks_average": "Average midterm marks",
    "quiz_average": "Average quiz performance",
    "assignment_average": "Average assignment performance",
    "assignment_completion_rate": "Assignment completion rate",
    "practical_marks_average": "Average practical marks",
    "assessment_trend": "Assessment performance trend",
    "recent_engagement_score": "Recent engagement score",
    "engagement_trend": "Engagement trend",
    "fee_status": "Fee payment status",
    "fee_arrears_amount": "Fee arrears amount",
    "payment_delay_days": "Payment delay days",
    "prolonged_absence_flag": "Prolonged absence indicator",
    "prolonged_absence_days": "Prolonged absence duration",
    "academic_decline_flag": "Recent academic decline indicator",
    "repeated_backlog_flag": "Repeated backlog indicator",
    "engagement_decline_flag": "Engagement decline indicator",
    "internal_marks": "Course internal assessment marks",
    "midterm_marks": "Course midterm marks",
    "course_attendance_percentage": "Course attendance percentage",
    "course_attendance_trend": "Course attendance trend",
    "previous_course_attempts": "Previous attempts in this course",
    "previous_course_grade": "Previous course grade",
    "course_credits": "Course credits",
}


def select_features(frame, model_name: str) -> list[str]:
    excluded = COURSE_EXCLUDED if model_name == "course_failure" else STUDENT_EXCLUDED
    return [c for c in frame.columns if c not in excluded]


def feature_label(feature: str) -> str:
    raw = feature.split("__", 1)[-1]
    for key, label in FEATURE_EXPLANATIONS.items():
        if raw == key or raw.startswith(key + "_"):
            return label
    return raw.replace("_", " ").capitalize()
