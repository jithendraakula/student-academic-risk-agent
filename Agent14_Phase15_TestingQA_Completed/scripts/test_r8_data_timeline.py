"""R8 academic timeline and data-domain integrity gate."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
EXPECTED_YEARS = {1: "2024-25", 2: "2024-25", 3: "2025-26", 4: "2025-26", 5: "2026-27"}


def main() -> int:
    students = pd.read_csv(DATA / "students.csv")
    assignments = pd.read_csv(DATA / "assignments.csv")
    semester = pd.read_csv(DATA / "student_semester_features.csv")
    course = pd.read_csv(DATA / "student_course_features.csv")
    outcomes = pd.read_csv(DATA / "historical_outcomes.csv")

    errors: list[str] = []

    # Active cohort timeline.
    if set(students["academic_year"]) != {"2026-27"}:
        errors.append("active students are not all in academic year 2026-27")
    if set(students["current_semester"]) != {5}:
        errors.append("active students are not all in current semester 5")
    if set(assignments["academic_year"]) != {"2026-27"}:
        errors.append("current mentor assignments are not in academic year 2026-27")
    if set(assignments["semester"]) != {5}:
        errors.append("current mentor assignments are not in semester 5")

    # Academic year mapping follows the standard two-semesters-per-academic-year rule.
    for semester_no, expected_year in EXPECTED_YEARS.items():
        sem_years = set(semester.loc[semester["semester"].eq(semester_no), "academic_year"])
        course_years = set(course.loc[course["semester"].eq(semester_no), "academic_year"])
        if sem_years != {expected_year}:
            errors.append(f"semester {semester_no} feature year is {sorted(sem_years)}; expected {expected_year}")
        if course_years != {expected_year}:
            errors.append(f"semester {semester_no} course year is {sorted(course_years)}; expected {expected_year}")
    for semester_no in range(1, 5):
        out_years = set(outcomes.loc[outcomes["semester"].eq(semester_no), "academic_year"])
        if out_years != {EXPECTED_YEARS[semester_no]}:
            errors.append(f"historical outcome year mismatch for semester {semester_no}: {sorted(out_years)}")

    # No future academic year relative to current semester 5.
    valid_semester_pairs = set(EXPECTED_YEARS.items())
    observed_pairs = set(zip(semester["semester"], semester["academic_year"]))
    if not observed_pairs.issubset(valid_semester_pairs):
        errors.append("observed semester/year pairs contain an invalid/future mapping")

    # One complete chronological snapshot sequence per student.
    counts = semester.groupby("student_id")["semester"].agg(list)
    if not counts.apply(lambda x: x == [1, 2, 3, 4, 5]).all():
        errors.append("every student must have ordered semesters 1-5 exactly once")

    # Current snapshot must be the latest semester and current year.
    current = semester.loc[semester["snapshot_type"].eq("current")]
    if not current.semester.eq(5).all() or not current.academic_year.eq("2026-27").all():
        errors.append("current snapshots do not consistently represent semester 5 / 2026-27")

    historical = semester.loc[semester["snapshot_type"].eq("historical")]
    if not historical.semester.isin([1, 2, 3, 4]).all():
        errors.append("historical snapshots contain non-historical semester numbers")
    if historical.academic_year.isin(["2027-28", "2028-29"]).any():
        errors.append("historical snapshots contain known future academic years")

    # R8 also preserves the established CSE-only domain.
    if set(semester["department"]) != {"DEPT_CSE"} or set(course["course_id"].astype(str).str[:3]) != {"CSE"}:
        errors.append("academic records are no longer restricted to the CSE demo domain")

    if errors:
        print("R8 DATA TIMELINE TEST FAILED")
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1

    print("R8 DATA TIMELINE TEST PASSED")
    print("Academic year mapping:", EXPECTED_YEARS)
    print("Current snapshot: semester=5 academic_year=2026-27 students=", len(current))
    print("Historical semesters=1-4 students=", len(historical) // 4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
