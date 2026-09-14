from pathlib import Path

SEED = 2026
CHECKPOINT_WEEK = 6
CURRENT_COHORT = 2024
HISTORICAL_TRAIN_SEMESTERS = (1, 2, 3)
HOLDOUT_SEMESTER = 4
CURRENT_PREDICTION_SEMESTER = 5
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
# Probability bands are deliberately conservative for this early-warning workflow.
# A critical prediction requires at least a 60% calibrated probability; this keeps the
# critical queue small while still surfacing the most actionable cases in the demo.
RISK_LEVELS = ((0.20, "LOW"), (0.40, "MODERATE"), (0.60, "HIGH"), (1.01, "CRITICAL"))


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
