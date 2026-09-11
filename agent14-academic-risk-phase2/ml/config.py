from pathlib import Path

SEED = 42
TEST_SIZE = 0.2
ATTENDANCE_THRESHOLD = 75.0
GPA_THRESHOLD = 7.0
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data" / "processed"
MODEL_DIR = Path(__file__).resolve().parent / "models"
METRICS_DIR = Path(__file__).resolve().parent / "metrics"
MODEL_NAMES = {
    "course_failure": "course_failure_model.joblib",
    "backlog": "backlog_model.joblib",
    "gpa_threshold": "gpa_risk_model.joblib",
    "attendance_shortage": "attendance_risk_model.joblib",
    "discontinuation": "discontinuation_model.joblib",
}
SEVERITY_BANDS = ((0.25, "LOW"), (0.50, "MODERATE"), (0.75, "HIGH"), (1.01, "CRITICAL"))


def risk_level(probability: float) -> str:
    for upper_bound, label in SEVERITY_BANDS:
        if probability < upper_bound:
            return label
    return "CRITICAL"


def confidence_level(probability: float) -> str:
    distance = abs(probability - 0.5)
    if distance >= 0.25:
        return "HIGH"
    if distance >= 0.15:
        return "MEDIUM"
    return "LOW"
