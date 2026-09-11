"""
Runs all synthetic data generators in dependency order and writes
CSVs to data/processed/. Deterministic (seeded) so re-running produces
identical demo data every time.
"""

import os
import pandas as pd

import gen_students_teachers as g1
import gen_reference_data as g8
import gen_semester_features as g4
import gen_course_features as g5
import gen_historical_outcomes as g7
import gen_alerts as g6

OUT = os.path.join(os.path.dirname(__file__), "..", "processed")
os.makedirs(OUT, exist_ok=True)


def main():
    print("== Dataset 2/1/3: Teachers, Students, Assignments ==")
    teachers_df = g1.generate_teachers()
    students_df = g1.generate_students()
    assignments_df = g1.generate_assignments(students_df, teachers_df)
    teachers_df.to_csv(f"{OUT}/teachers.csv", index=False)
    students_df.to_csv(f"{OUT}/students.csv", index=False)
    assignments_df.to_csv(f"{OUT}/assignments.csv", index=False)
    print(f"  teachers={len(teachers_df)} students={len(students_df)} assignments={len(assignments_df)}")

    print("== Dataset 8: Academic Reference Data ==")
    ref_df = g8.generate_reference_data()
    ref_df.to_csv(f"{OUT}/academic_reference_data.csv", index=False)
    print(f"  reference_rows={len(ref_df)}")

    print("== Dataset 4: Student Semester Features ==")
    semester_df = g4.generate_semester_features(students_df, assignments_df)
    semester_df.to_csv(f"{OUT}/student_semester_features.csv", index=False)
    print(f"  rows={len(semester_df)}")
    print(f"  archetypes:\n{semester_df['_archetype'].value_counts().to_string()}")

    print("== Dataset 5: Student Course Features ==")
    course_df = g5.generate_course_features(semester_df)
    course_df.to_csv(f"{OUT}/student_course_features.csv", index=False)
    print(f"  rows={len(course_df)} failed_rows={int(course_df['course_failed'].sum())}")

    print("== Dataset 7: Historical Outcomes ==")
    hist_df = g7.generate_historical_outcomes(semester_df)
    hist_df.to_csv(f"{OUT}/historical_outcomes.csv", index=False)
    print(f"  rows={len(hist_df)}")

    print("== Dataset 6: Alerts and Interventions ==")
    alerts_df = g6.generate_alerts(semester_df, assignments_df)
    alerts_df.to_csv(f"{OUT}/alerts_interventions.csv", index=False)
    print(f"  rows={len(alerts_df)}")
    print(f"  status breakdown:\n{alerts_df['alert_status'].value_counts().to_string()}")
    print(f"  risk_type breakdown:\n{alerts_df['risk_type'].value_counts().to_string()}")

    print("\nAll datasets written to data/processed/")


if __name__ == "__main__":
    main()