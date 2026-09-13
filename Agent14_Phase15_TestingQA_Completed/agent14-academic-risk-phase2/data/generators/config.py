"""
Shared configuration for synthetic data generation.
Keeping the scope small (2 departments, 1 semester snapshot) so the
hackathon demo stays fast and every number is traceable back here.
"""

import numpy as np

SEED = 42
RNG = np.random.default_rng(SEED)

ACADEMIC_YEAR = "2025-26"
CURRENT_SEMESTER = 5
CHECKPOINT_WEEK = 10

DEPARTMENTS = [
    {"department_id": "DEPT_CSE", "department_name": "Computer Science and Engineering"},
    {"department_id": "DEPT_ECE", "department_name": "Electronics and Communication Engineering"},
]

BATCHES = ["2023"]
SECTIONS = ["A", "B"]

STUDENTS_PER_SECTION = 15  # 2 depts * 2 sections * 15 = 60 students total (keeps demo fast)

MENTORS_PER_DEPARTMENT = 3  # each mentor gets ~10 students

# Courses per department for the current semester (Dataset 8 / 5)
COURSES = {
    "DEPT_CSE": [
        {"course_id": "CSE501", "course_name": "Operating Systems", "credits": 4, "passing_marks": 40},
        {"course_id": "CSE502", "course_name": "Database Management Systems", "credits": 4, "passing_marks": 40},
        {"course_id": "CSE503", "course_name": "Design and Analysis of Algorithms", "credits": 3, "passing_marks": 40},
        {"course_id": "CSE504", "course_name": "Computer Networks", "credits": 3, "passing_marks": 40},
        {"course_id": "CSE505", "course_name": "Software Engineering", "credits": 3, "passing_marks": 40},
    ],
    "DEPT_ECE": [
        {"course_id": "ECE501", "course_name": "Digital Signal Processing", "credits": 4, "passing_marks": 40},
        {"course_id": "ECE502", "course_name": "VLSI Design", "credits": 4, "passing_marks": 40},
        {"course_id": "ECE503", "course_name": "Microprocessors", "credits": 3, "passing_marks": 40},
        {"course_id": "ECE504", "course_name": "Control Systems", "credits": 3, "passing_marks": 40},
        {"course_id": "ECE505", "course_name": "Communication Systems", "credits": 3, "passing_marks": 40},
    ],
}

ATTENDANCE_THRESHOLD = 75.0
GPA_THRESHOLD = 7.0

# Demo-mode reliability: force specific student archetypes so the
# mentor/HOD/Dean demo always has a critical case to click into.
# Applied as index offsets within each mentor's student block.
ARCHETYPE_PLAN = {
    0: "critical_multi_risk",   # first student of every mentor -> critical, multiple risks high
    1: "attendance_only",       # second -> only attendance risk high, rest fine
    2: "discontinuation_watch", # third -> support-attention risk high, grades look ok (tests guardrail UI)
    # remaining students -> "normal" distribution
}