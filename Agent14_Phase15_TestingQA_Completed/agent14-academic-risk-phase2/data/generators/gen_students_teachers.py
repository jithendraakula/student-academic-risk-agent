"""Generates Dataset 1 (Students), Dataset 2 (Teachers), Dataset 3 (Assignments)."""

import pandas as pd
from faker import Faker
from config import (
    RNG, DEPARTMENTS, BATCHES, SECTIONS, STUDENTS_PER_SECTION,
    MENTORS_PER_DEPARTMENT, ACADEMIC_YEAR, CURRENT_SEMESTER,
)

fake = Faker("en_IN")
Faker.seed(42)


def generate_teachers():
    rows = []
    teacher_counter = 1
    for dept in DEPARTMENTS:
        # N mentors + 1 HOD per department
        for i in range(MENTORS_PER_DEPARTMENT):
            tid = f"T{teacher_counter:03d}"
            rows.append({
                "teacher_id": tid,
                "teacher_name": fake.name(),
                "role": "mentor",
                "department": dept["department_id"],
                "email": f"mentor{i+1}.{dept['department_id'].lower().replace('dept_','')}@vignan.ac.in",
            })
            teacher_counter += 1
        hod_id = f"T{teacher_counter:03d}"
        rows.append({
            "teacher_id": hod_id,
            "teacher_name": fake.name(),
            "role": "hod",
            "department": dept["department_id"],
            "email": f"hod.{dept['department_id'].lower().replace('dept_','')}@vignan.ac.in",
        })
        teacher_counter += 1

    # One Dean, college-wide (department = None)
    rows.append({
        "teacher_id": f"T{teacher_counter:03d}",
        "teacher_name": fake.name(),
        "role": "dean",
        "department": None,
        "email": "dean@vignan.ac.in",
    })

    return pd.DataFrame(rows)


def generate_students():
    rows = []
    student_counter = 1
    for dept in DEPARTMENTS:
        for batch in BATCHES:
            for section in SECTIONS:
                for _ in range(STUDENTS_PER_SECTION):
                    sid = f"S{student_counter:04d}"
                    rows.append({
                        "student_id": sid,
                        "student_name": fake.name(),
                        "department": dept["department_id"],
                        "program": "B.Tech",
                        "batch": batch,
                        "section": section,
                        "academic_year": ACADEMIC_YEAR,
                        "current_semester": CURRENT_SEMESTER,
                    })
                    student_counter += 1
    return pd.DataFrame(rows)


def generate_assignments(students_df: pd.DataFrame, teachers_df: pd.DataFrame):
    """Evenly assigns each department's students round-robin across that
    department's mentors, so each mentor gets a comparable, non-overlapping
    student set (enforces the mentor-isolation requirement at the data level)."""
    rows = []
    assignment_counter = 1
    for dept in DEPARTMENTS:
        dept_id = dept["department_id"]
        dept_students = students_df[students_df["department"] == dept_id]["student_id"].tolist()
        dept_mentors = teachers_df[
            (teachers_df["department"] == dept_id) & (teachers_df["role"] == "mentor")
        ]["teacher_id"].tolist()

        for i, sid in enumerate(dept_students):
            mentor_id = dept_mentors[i % len(dept_mentors)]
            rows.append({
                "assignment_id": f"ASG{assignment_counter:04d}",
                "student_id": sid,
                "teacher_id": mentor_id,
                "academic_year": ACADEMIC_YEAR,
                "semester": CURRENT_SEMESTER,
                "assignment_type": "mentor",
            })
            assignment_counter += 1

    return pd.DataFrame(rows)


if __name__ == "__main__":
    teachers_df = generate_teachers()
    students_df = generate_students()
    assignments_df = generate_assignments(students_df, teachers_df)

    teachers_df.to_csv("../processed/teachers.csv", index=False)
    students_df.to_csv("../processed/students.csv", index=False)
    assignments_df.to_csv("../processed/assignments.csv", index=False)

    print(f"Teachers: {len(teachers_df)}")
    print(f"Students: {len(students_df)}")
    print(f"Assignments: {len(assignments_df)}")