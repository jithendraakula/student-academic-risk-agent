COURSE_EXCLUDED = {
    "student_id", "course_id", "course_name", "academic_year", "semester", "checkpoint_week",
}
STUDENT_EXCLUDED = {
    "student_id", "cohort", "academic_year", "semester", "checkpoint_week", "batch", "section", "_archetype",
    "current_gpa", "current_cgpa", "gpa_change", "current_backlog_count", "projected_final_attendance",
    "prolonged_absence_flag", "prolonged_absence_days", "fee_status", "fee_arrears_amount",
    "engagement_decline_flag", "repeated_backlog_flag", "backlog_target", "gpa_target",
    "attendance_target", "discontinuation_target", "historical_backlog_label", "historical_discontinued",
}


def select_features(frame, model_name: str):
    excluded = COURSE_EXCLUDED if model_name == "course_failure" else STUDENT_EXCLUDED
    return [column for column in frame.columns if column not in excluded]


FEATURE_EXPLANATIONS = {
    "current_attendance_percentage": "Current attendance is below the comfortable operating range.",
    "attendance_last_30_days": "Attendance over the last 30 days indicates recent absence pressure.",
    "attendance_trend": "Attendance trend suggests recent academic disruption.",
    "consecutive_absence_days": "Multiple consecutive absences were detected.",
    "total_absent_days": "The total number of absent days is elevated.",
    "previous_backlog_count": "Previous backlog history increases the likelihood of additional academic difficulty.",
    "total_historical_backlogs": "Historical backlogs indicate repeated academic difficulty.",
    "internal_marks": "Low internal assessment marks reduce the likelihood of course success.",
    "internal_marks_average": "The internal assessment average is a meaningful academic risk signal.",
    "midterm_marks": "Midterm performance contributes to course failure risk.",
    "assignment_average": "Assignment performance contributes to academic risk.",
    "assignment_completion_rate": "Incomplete assignments reduce available academic evidence of mastery.",
    "previous_gpa": "Previous GPA provides context for the current academic trajectory.",
    "gpa_change": "A declining GPA trend increases academic risk.",
    "fee_arrears_amount": "Fee arrears can indicate a need for support, not a punitive decision.",
    "payment_delay_days": "Payment delays are treated only as a support signal.",
    "recent_engagement_score": "Lower recent engagement suggests that proactive support may help.",
}
