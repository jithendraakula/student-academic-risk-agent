"""Canonical synthetic demo-data configuration for Agent 14.

The demo models one CSE academic cohort so the institutional hierarchy is easy to
explain: 10 sections x 50 students, with one mentor responsible for two sections.
Historical academic snapshots are retained for ML training; the current application
population is the 500-student 2024 CSE cohort.
"""
from pathlib import Path
import numpy as np

SEED = 2026
RNG = np.random.default_rng(SEED)

DEPARTMENT_ID = "DEPT_CSE"
DEPARTMENT_NAME = "Computer Science and Engineering"
PROGRAM = "B.Tech"
BATCH = 2024
ACADEMIC_YEAR = "2026-27"
CURRENT_SEMESTER = 5
CHECKPOINT_WEEK = 6
ATTENDANCE_THRESHOLD = 75.0
GPA_THRESHOLD = 7.0

SECTIONS = [f"CSE-{letter}" for letter in "ABCDEFGHIJ"]
STUDENTS_PER_SECTION = 50
MENTOR_IDS = [f"T{i:03d}" for i in range(1, 6)]

# A small, deliberately asymmetric pattern makes the demo look realistic without
# turning every section into a crisis. Two sections have a slightly larger critical
# pocket; the other sections are healthier.
CRITICAL_PER_SECTION = {section: (4 if section in {"CSE-F", "CSE-J"} else 2) for section in SECTIONS}
HIGH_PER_SECTION = {section: 4 for section in SECTIONS}
WATCH_PER_SECTION = {section: 6 for section in SECTIONS}

# Five current courses. Historical semesters use a consistent CSE curriculum so the
# feature schema stays stable and the UI has familiar subjects.
COURSES = {
    1: [
        ("CSE101", "Programming Fundamentals", 4),
        ("CSE102", "Engineering Mathematics I", 4),
        ("CSE103", "Engineering Physics", 3),
        ("CSE104", "Engineering Drawing", 3),
        ("CSE105", "Communication Skills", 3),
    ],
    2: [
        ("CSE201", "Data Structures", 4),
        ("CSE202", "Engineering Mathematics II", 4),
        ("CSE203", "Digital Logic Design", 3),
        ("CSE204", "Object Oriented Programming", 3),
        ("CSE205", "Environmental Science", 3),
    ],
    3: [
        ("CSE301", "Database Systems", 4),
        ("CSE302", "Computer Organization", 4),
        ("CSE303", "Discrete Mathematics", 3),
        ("CSE304", "Operating Systems Fundamentals", 3),
        ("CSE305", "Web Technologies", 3),
    ],
    4: [
        ("CSE401", "Design and Analysis of Algorithms", 4),
        ("CSE402", "Computer Networks", 4),
        ("CSE403", "Theory of Computation", 3),
        ("CSE404", "Software Engineering", 3),
        ("CSE405", "Probability and Statistics", 3),
    ],
    5: [
        ("CSE501", "Operating Systems", 4),
        ("CSE502", "Database Management Systems", 4),
        ("CSE503", "Design and Analysis of Algorithms", 3),
        ("CSE504", "Computer Networks", 3),
        ("CSE505", "Software Engineering", 3),
    ],
}

OUT = Path(__file__).resolve().parents[1] / "processed"
