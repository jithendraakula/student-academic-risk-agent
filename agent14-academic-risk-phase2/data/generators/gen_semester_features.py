"""
Generates Dataset 4: Student Semester Features.

Uses per-mentor archetype slots (see config.ARCHETYPE_PLAN) so every
mentor's cohort has at least one clearly critical student, one
attendance-only case, and one "looks fine academically but flagged for
support attention" case (this last one exercises the discontinuation
guardrail: high support-attention risk must never imply academic failure).
"""

import pandas as pd
from config import RNG, ACADEMIC_YEAR, CURRENT_SEMESTER, CHECKPOINT_WEEK, ARCHETYPE_PLAN


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def archetype_for(position_within_mentor: int) -> str:
    return ARCHETYPE_PLAN.get(position_within_mentor, "normal")


def sample_features(archetype: str) -> dict:
    if archetype == "critical_multi_risk":
        gpa = round(RNG.uniform(4.8, 6.3), 2)
        attendance = round(RNG.uniform(52, 68), 1)
        backlog_count = int(RNG.integers(1, 4))
        engagement = round(RNG.uniform(0.2, 0.45), 2)
        fee_status = "overdue"
        fee_arrears = int(RNG.integers(8000, 30000))
        prolonged_absence = True
        academic_decline = True
        repeated_backlog = backlog_count >= 2

    elif archetype == "attendance_only":
        gpa = round(RNG.uniform(7.4, 9.0), 2)
        attendance = round(RNG.uniform(48, 66), 1)
        backlog_count = 0
        engagement = round(RNG.uniform(0.55, 0.75), 2)
        fee_status = "paid"
        fee_arrears = 0
        prolonged_absence = True
        academic_decline = False
        repeated_backlog = False

    elif archetype == "discontinuation_watch":
        gpa = round(RNG.uniform(7.0, 8.6), 2)
        attendance = round(RNG.uniform(78, 90), 1)
        backlog_count = 0
        engagement = round(RNG.uniform(0.25, 0.4), 2)
        fee_status = "overdue"
        fee_arrears = int(RNG.integers(15000, 40000))
        prolonged_absence = False
        academic_decline = False
        repeated_backlog = False

    else:  # normal distribution
        gpa = round(RNG.uniform(6.8, 9.2), 2)
        attendance = round(RNG.uniform(76, 97), 1)
        backlog_count = int(RNG.choice([0, 0, 0, 1], p=[0.7, 0.15, 0.1, 0.05]))
        engagement = round(RNG.uniform(0.6, 0.9), 2)
        fee_status = RNG.choice(["paid", "pending"], p=[0.9, 0.1])
        fee_arrears = 0 if fee_status == "paid" else int(RNG.integers(1000, 5000))
        prolonged_absence = False
        academic_decline = False
        repeated_backlog = False

    previous_gpa = round(clip(gpa + RNG.uniform(-0.4, 0.4), 3.0, 10.0), 2)
    cgpa = round(clip((gpa + previous_gpa) / 2 + RNG.uniform(-0.2, 0.2), 3.0, 10.0), 2)
    previous_cgpa = round(clip(cgpa + RNG.uniform(-0.15, 0.15), 3.0, 10.0), 2)

    internal_avg = round(clip(gpa * 8 + RNG.uniform(-8, 8), 10, 100), 1)
    midterm_avg = round(clip(internal_avg + RNG.uniform(-10, 10), 0, 100), 1)
    quiz_avg = round(clip(internal_avg + RNG.uniform(-10, 10), 0, 100), 1)
    assignment_avg = round(clip(internal_avg + RNG.uniform(-5, 15), 0, 100), 1)
    practical_avg = round(clip(internal_avg + RNG.uniform(-5, 10), 0, 100), 1)
    assessment_trend = RNG.choice(
        ["improving", "stable", "declining"],
        p=[0.25, 0.45, 0.3] if archetype != "critical_multi_risk" else [0.05, 0.25, 0.7],
    )
    assignment_completion_rate = round(clip(engagement + RNG.uniform(-0.1, 0.1), 0, 1), 2)

    attendance_last_30 = round(clip(attendance + RNG.uniform(-8, 5), 0, 100), 1)
    attendance_trend = "declining" if attendance_last_30 < attendance else RNG.choice(["stable", "improving"])
    consecutive_absence_days = int(RNG.integers(4, 10)) if prolonged_absence else int(RNG.integers(0, 3))
    total_absent_days = int(RNG.integers(15, 35)) if attendance < 70 else int(RNG.integers(2, 14))
    recent_absence_rate = round(clip((100 - attendance_last_30) / 100, 0, 1), 2)
    projected_final_attendance = round(clip(attendance - RNG.uniform(0, 5), 0, 100), 1)

    previous_backlog_count = max(0, backlog_count - int(RNG.integers(0, 2)))
    total_historical_backlogs = backlog_count + previous_backlog_count + int(RNG.integers(0, 2))
    new_backlogs_last_semester = max(0, backlog_count - previous_backlog_count)
    repeated_backlog_subject_count = 1 if repeated_backlog else 0
    backlog_growth_rate = round((backlog_count - previous_backlog_count) / max(1, previous_backlog_count + 1), 2)

    recent_engagement_score = engagement
    engagement_trend = "declining" if engagement < 0.5 else RNG.choice(["stable", "improving"])
    assessment_participation_rate = round(clip(engagement + RNG.uniform(-0.05, 0.1), 0, 1), 2)

    payment_delay_days = int(RNG.integers(15, 60)) if fee_status == "overdue" else 0
    installment_pending = fee_status == "overdue"

    return {
        "current_gpa": gpa, "current_cgpa": cgpa, "previous_gpa": previous_gpa,
        "previous_cgpa": previous_cgpa, "gpa_change": round(gpa - previous_gpa, 2),
        "internal_marks_average": internal_avg, "midterm_marks_average": midterm_avg,
        "quiz_average": quiz_avg, "assignment_average": assignment_avg,
        "practical_marks_average": practical_avg, "assessment_trend": assessment_trend,
        "assignment_completion_rate": assignment_completion_rate,
        "current_attendance_percentage": attendance, "attendance_last_30_days": attendance_last_30,
        "attendance_trend": attendance_trend, "consecutive_absence_days": consecutive_absence_days,
        "total_absent_days": total_absent_days, "recent_absence_rate": recent_absence_rate,
        "projected_final_attendance": projected_final_attendance,
        "current_backlog_count": backlog_count, "previous_backlog_count": previous_backlog_count,
        "total_historical_backlogs": total_historical_backlogs,
        "new_backlogs_last_semester": new_backlogs_last_semester,
        "repeated_backlog_subject_count": repeated_backlog_subject_count,
        "backlog_growth_rate": backlog_growth_rate,
        "assessment_participation_rate": assessment_participation_rate,
        "recent_engagement_score": recent_engagement_score, "engagement_trend": engagement_trend,
        "fee_status": fee_status, "fee_arrears_amount": fee_arrears,
        "payment_delay_days": payment_delay_days, "installment_pending": installment_pending,
        "prolonged_absence_flag": prolonged_absence,
        "prolonged_absence_days": consecutive_absence_days if prolonged_absence else 0,
        "academic_decline_flag": academic_decline, "repeated_backlog_flag": repeated_backlog,
        "engagement_decline_flag": engagement_trend == "declining",
    }


def generate_semester_features(students_df: pd.DataFrame, assignments_df: pd.DataFrame):
    rows = []
    assignments_df = assignments_df.sort_values(["teacher_id", "student_id"]).reset_index(drop=True)
    assignments_df["position_within_mentor"] = assignments_df.groupby("teacher_id").cumcount()

    merged = students_df.merge(
        assignments_df[["student_id", "teacher_id", "position_within_mentor"]],
        on="student_id", how="left",
    )

    for _, s in merged.iterrows():
        archetype = archetype_for(int(s["position_within_mentor"]))
        feats = sample_features(archetype)
        row = {
            "student_id": s["student_id"], "cohort": s["batch"], "academic_year": ACADEMIC_YEAR,
            "semester": CURRENT_SEMESTER, "checkpoint_week": CHECKPOINT_WEEK,
            "department": s["department"], "batch": s["batch"], "section": s["section"],
            "_archetype": archetype,  # internal only, drives alert generation; not part of PRD schema
        }
        row.update(feats)
        rows.append(row)

    return pd.DataFrame(rows)


if __name__ == "__main__":
    students_df = pd.read_csv("../processed/students.csv")
    assignments_df = pd.read_csv("../processed/assignments.csv")
    df = generate_semester_features(students_df, assignments_df)
    df.to_csv("../processed/student_semester_features.csv", index=False)
    print(f"Semester feature rows: {len(df)}")
    print(df["_archetype"].value_counts())