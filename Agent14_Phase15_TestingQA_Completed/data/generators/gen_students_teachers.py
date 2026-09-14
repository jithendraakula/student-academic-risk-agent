"""Compatibility wrapper for canonical Agent 14 CSE demo generation."""
from generate_all import generate_students_and_teachers

if __name__ == "__main__":
    students, teachers, assignments, _ = generate_students_and_teachers()
    students.to_csv("../processed/students.csv", index=False)
    teachers.to_csv("../processed/teachers.csv", index=False)
    assignments.to_csv("../processed/assignments.csv", index=False)
    print(f"Teachers: {len(teachers)}")
    print(f"Students: {len(students)}")
    print(f"Assignments: {len(assignments)}")
