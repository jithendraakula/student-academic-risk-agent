from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .config import ATTENDANCE_THRESHOLD, DATA_DIR, GPA_THRESHOLD
except ImportError:
    from config import ATTENDANCE_THRESHOLD, DATA_DIR, GPA_THRESHOLD


def load_processed_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    files = {
        "students": "students.csv",
        "assignments": "assignments.csv",
        "semester": "student_semester_features.csv",
        "course": "student_course_features.csv",
        "historical": "historical_outcomes.csv",
        "reference": "academic_reference_data.csv",
    }
    missing = [name for name, filename in files.items() if not (data_dir / filename).exists()]
    if missing:
        raise FileNotFoundError(f"Missing processed datasets: {', '.join(missing)}")
    return {name: pd.read_csv(data_dir / filename) for name, filename in files.items()}


def require_columns(frame: pd.DataFrame, required: list[str], dataset: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"{dataset} is missing required columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError(f"{dataset} has no rows")


def build_student_training_frame(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = data["semester"].copy()
    require_columns(frame, ["student_id", "current_gpa", "current_attendance_percentage"], "semester features")
    historical = data["historical"].groupby("student_id", as_index=False).agg(
        historical_backlog_label=("new_backlog", "max"),
        historical_discontinued=("discontinued", "max"),
    )
    frame = frame.merge(historical, on="student_id", how="left")
    frame["backlog_target"] = frame["current_backlog_count"].fillna(0).gt(0).astype(int)
    frame["gpa_target"] = frame["current_gpa"].lt(GPA_THRESHOLD).astype(int)
    frame["attendance_target"] = frame["projected_final_attendance"].lt(ATTENDANCE_THRESHOLD).astype(int)
    # No active student is marked discontinued in the synthetic history. This is a support-only proxy,
    # derived from observable warning signals and never intended for punitive or eligibility decisions.
    frame["discontinuation_target"] = (
        frame["prolonged_absence_flag"].astype(bool)
        | frame["fee_status"].eq("overdue")
        | frame["engagement_decline_flag"].astype(bool)
        | frame["repeated_backlog_flag"].astype(bool)
    ).astype(int)
    return frame


def build_training_sets(data: dict[str, pd.DataFrame]) -> dict[str, tuple[pd.DataFrame, pd.Series, list[str], str]]:
    student = build_student_training_frame(data)
    course = data["course"].copy()
    require_columns(course, ["course_failed", "student_id", "course_id"], "course features")
    return {
        "course_failure": (course, course.pop("course_failed"), list(course.columns), "course_failed"),
        "backlog": (student, student.pop("backlog_target"), list(student.columns), "current_backlog_count > 0"),
        "gpa_threshold": (student, student.pop("gpa_target"), list(student.columns), f"current_gpa < {GPA_THRESHOLD}"),
        "attendance_shortage": (student, student.pop("attendance_target"), list(student.columns), f"projected_final_attendance < {ATTENDANCE_THRESHOLD}"),
        "discontinuation": (student, student.pop("discontinuation_target"), list(student.columns), "support-only synthetic warning proxy"),
    }


def print_target_distributions(training_sets: dict[str, tuple[pd.DataFrame, pd.Series, list[str], str]]) -> None:
    for name, (_, target, _, description) in training_sets.items():
        counts = target.value_counts().to_dict()
        if len(counts) < 2:
            raise ValueError(f"{name} target '{description}' has one class only: {counts}")
        print(f"{name}: {counts}")
