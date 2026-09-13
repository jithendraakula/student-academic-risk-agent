from pathlib import Path

SEED = 42
CHECKPOINT_WEEK = 6
HOLDOUT_COHORT = 2025
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
MODEL_DIR = Path(__file__).resolve().parent / "models"
METRICS_DIR = Path(__file__).resolve().parent / "metrics"
MODEL_NAMES = {
    "course_failure": "course_failure_model.joblib",
    "backlog": "backlog_model.joblib",
    "gpa_threshold": "gpa_risk_model.joblib",
    "attendance_shortage": "attendance_risk_model.joblib",
    "discontinuation": "discontinuation_model.joblib",
}
LABELS = {
    "course_failure": "End-of-semester course failure",
    "backlog": "End-of-semester new backlog",
    "gpa_threshold": "End-of-semester GPA below configured threshold",
    "attendance_shortage": "End-of-semester attendance below configured threshold",
    "discontinuation": "End-of-semester support/discontinuation outcome",
}
RISK_LEVELS = ((0.25, "LOW"), (0.50, "MODERATE"), (0.75, "HIGH"), (1.01, "CRITICAL"))


def risk_level(probability: float) -> str:
    for upper, label in RISK_LEVELS:
        if probability < upper:
            return label
    return "CRITICAL"


def confidence_level(probability: float, sample_size: int | None = None) -> str:
    distance = abs(probability - 0.5)
    if distance >= 0.30 and (sample_size is None or sample_size >= 100):
        return "HIGH"
    if distance >= 0.15:
        return "MEDIUM"
    return "LOW"
