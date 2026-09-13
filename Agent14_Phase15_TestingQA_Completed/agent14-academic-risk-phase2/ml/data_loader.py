from __future__ import annotations

from pathlib import Path
import pandas as pd

from .config import DATA_DIR, HOLDOUT_COHORT

FILES = {
    "students": "students.csv",
    "assignments": "assignments.csv",
    "semester": "student_semester_features.csv",
    "course": "student_course_features.csv",
    "historical": "historical_outcomes.csv",
    "reference": "academic_reference_data.csv",
}


def load_processed_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    missing = [f for f in FILES.values() if not (data_dir / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing processed datasets: {', '.join(missing)}")
    return {k: pd.read_csv(data_dir / f) for k, f in FILES.items()}


def require_columns(frame: pd.DataFrame, required: list[str], dataset: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"{dataset} missing columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError(f"{dataset} is empty")


def build_historical_student_frame(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    semester = data["semester"].copy()
    outcomes = data["historical"].copy()
    require_columns(semester, ["student_id", "cohort", "semester", "checkpoint_week", "snapshot_type"], "semester")
    require_columns(outcomes, ["student_id", "cohort", "semester", "checkpoint_week"], "historical")
    history = semester.loc[semester["snapshot_type"].eq("historical")].copy()
    merged = history.merge(
        outcomes,
        on=["student_id", "cohort", "semester", "checkpoint_week"],
        how="inner",
        suffixes=("", "_outcome"),
        validate="one_to_one",
    )
    if merged.empty:
        raise ValueError("No historical student snapshots matched historical outcomes")
    return merged


def build_training_sets(data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    student = build_historical_student_frame(data)
    course = data["course"].loc[data["course"]["snapshot_type"].eq("historical")].copy()
    require_columns(course, ["student_id", "cohort", "semester", "course_id", "course_failed"], "historical course")

    student_targets = {
        "backlog": "new_backlog",
        "gpa_threshold": "gpa_below_threshold",
        "attendance_shortage": "attendance_shortage",
        "discontinuation": "discontinued",
    }
    sets = {
        "course_failure": {
            "frame": course,
            "target_column": "course_failed",
            "unit": "student_course",
        }
    }
    for name, target_column in student_targets.items():
        sets[name] = {
            "frame": student,
            "target_column": target_column,
            "unit": "student_semester",
        }
    return sets


def split_by_cohort(frame: pd.DataFrame, holdout_cohort: int = HOLDOUT_COHORT):
    if "cohort" not in frame.columns:
        raise ValueError("cohort column is required for time/cohort-aware split")
    train = frame.loc[frame["cohort"] != holdout_cohort].copy()
    test = frame.loc[frame["cohort"] == holdout_cohort].copy()
    if train.empty or test.empty:
        raise ValueError(f"Cohort holdout failed: train={len(train)}, test={len(test)}")
    return train, test
