"""Non-canonical seed scoring helpers kept for backward compatibility.

The production dashboard uses ML RiskPrediction and the canonical priority engine.
These helpers exist only for tooling that may import the old module name.
"""

def clip(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def course_failure_risk(course_row):
    return clip(max(0, 55 - course_row["internal_marks"]) * 1.4 + max(0, 75 - course_row["course_attendance_percentage"]) * 0.9)


def backlog_risk(sem_row):
    return clip(sem_row["current_backlog_count"] * 18 + max(0, sem_row["backlog_growth_rate"]) * 25)


def gpa_threshold_risk(sem_row, gpa_threshold=7.0):
    return clip(max(0, gpa_threshold - sem_row["current_gpa"]) * 30)


def attendance_shortage_risk(sem_row, attendance_threshold=75.0):
    return clip(max(0, attendance_threshold - sem_row["projected_final_attendance"]) * 2.2)


def support_attention_risk(sem_row):
    return clip((25 if sem_row["prolonged_absence_flag"] else 0) + (15 if sem_row["repeated_backlog_flag"] else 0) + (20 if sem_row["academic_decline_flag"] else 0) + (30 if sem_row["engagement_decline_flag"] else 0))
