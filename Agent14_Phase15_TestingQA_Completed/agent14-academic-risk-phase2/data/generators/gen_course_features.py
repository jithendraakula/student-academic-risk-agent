"""Generates Dataset 5: Student Course Features (one row per student per enrolled course)."""

import pandas as pd
from config import RNG, ACADEMIC_YEAR, CURRENT_SEMESTER, CHECKPOINT_WEEK, COURSES


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def generate_course_features(semester_df: pd.DataFrame):
    rows = []
    for _, s in semester_df.iterrows():
        dept_courses = COURSES[s["department"]]
        # Course failure risk is noisiest for the critical/declining archetype,
        # mild elsewhere - correlate with internal_marks_average and attendance.
        base_marks = s["internal_marks_average"]
        base_attendance = s["current_attendance_percentage"]

        for course in dept_courses:
            noise = RNG.uniform(-8, 8)
            internal_marks = round(clip(base_marks + noise, 0, 100), 1)
            midterm_marks = round(clip(internal_marks + RNG.uniform(-10, 10), 0, 100), 1)
            quiz_avg = round(clip(internal_marks + RNG.uniform(-10, 10), 0, 100), 1)
            assignment_avg = round(clip(internal_marks + RNG.uniform(-5, 10), 0, 100), 1)
            practical_marks = round(clip(internal_marks + RNG.uniform(-5, 10), 0, 100), 1)

            course_attendance = round(clip(base_attendance + RNG.uniform(-6, 6), 0, 100), 1)
            course_attendance_trend = RNG.choice(["improving", "stable", "declining"],
                                                  p=[0.25, 0.45, 0.3])

            previous_attempts = int(RNG.choice([0, 0, 0, 1], p=[0.85, 0.05, 0.05, 0.05]))
            previous_grade = None if previous_attempts == 0 else RNG.choice(["D", "F"])

            assessment_trend = s["assessment_trend"]
            assignment_completion_rate = s["assignment_completion_rate"]

            # Failure signal: weighted combination, then a boolean outcome flag
            # for below-passing-marks performance (used for historical outcomes too)
            course_failed = internal_marks < course["passing_marks"] and course_attendance < 65

            rows.append({
                "student_id": s["student_id"], "academic_year": ACADEMIC_YEAR,
                "semester": CURRENT_SEMESTER, "checkpoint_week": CHECKPOINT_WEEK,
                "course_id": course["course_id"], "course_name": course["course_name"],
                "course_credits": course["credits"],
                "internal_marks": internal_marks, "midterm_marks": midterm_marks,
                "quiz_average": quiz_avg, "assignment_average": assignment_avg,
                "practical_marks": practical_marks,
                "course_attendance_percentage": course_attendance,
                "course_attendance_trend": course_attendance_trend,
                "previous_course_attempts": previous_attempts,
                "previous_course_grade": previous_grade,
                "assessment_trend": assessment_trend,
                "assignment_completion_rate": assignment_completion_rate,
                "course_failed": course_failed,
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    semester_df = pd.read_csv("../processed/student_semester_features.csv")
    df = generate_course_features(semester_df)
    df.to_csv("../processed/student_course_features.csv", index=False)
    print(f"Course feature rows: {len(df)}")
    print(f"Failed-course rows: {df['course_failed'].sum()}")