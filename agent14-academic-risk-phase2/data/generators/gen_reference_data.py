"""Generates Dataset 8: Academic Reference Data (courses, thresholds)."""

import pandas as pd
from config import DEPARTMENTS, COURSES, CURRENT_SEMESTER, ATTENDANCE_THRESHOLD, GPA_THRESHOLD


def generate_reference_data():
    rows = []
    for dept in DEPARTMENTS:
        dept_id = dept["department_id"]
        for course in COURSES[dept_id]:
            rows.append({
                "department_id": dept_id,
                "department_name": dept["department_name"],
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "semester": CURRENT_SEMESTER,
                "course_credits": course["credits"],
                "passing_marks": course["passing_marks"],
                "attendance_threshold": ATTENDANCE_THRESHOLD,
                "gpa_threshold": GPA_THRESHOLD,
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_reference_data()
    df.to_csv("../processed/academic_reference_data.csv", index=False)
    print(f"Reference rows: {len(df)}")