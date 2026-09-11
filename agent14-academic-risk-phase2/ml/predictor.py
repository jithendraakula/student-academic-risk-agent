from pathlib import Path

import joblib
import pandas as pd

try:
    from .config import MODEL_DIR, MODEL_NAMES, confidence_level, risk_level
    from .feature_sets import FEATURE_EXPLANATIONS
except ImportError:
    from config import MODEL_DIR, MODEL_NAMES, confidence_level, risk_level
    from feature_sets import FEATURE_EXPLANATIONS


def _factor_label(feature: str) -> str:
    raw = _raw_feature(feature)
    for key, label in FEATURE_EXPLANATIONS.items():
        if raw.startswith(key):
            return label
    return raw.replace("_", " ").capitalize()


def _raw_feature(feature: str) -> str:
    return feature.split("__", 1)[-1]


def _feature_value(feature: str, row: dict):
    raw = _raw_feature(feature)
    if raw in row:
        return row[raw]
    # Encoded categorical features end with the category value; recover the
    # source column by matching the longest row key prefix.
    candidates = [key for key in row if raw.startswith(f"{key}_")]
    if candidates:
        return row[max(candidates, key=len)]
    return None


def _predict(model_key: str, row: dict) -> dict:
    pipeline = joblib.load(MODEL_DIR / MODEL_NAMES[model_key])
    frame = pd.DataFrame([row])
    probability = float(pipeline.predict_proba(frame)[:, 1][0])
    estimator = pipeline.named_steps["model"]
    transformed = pipeline.named_steps["preprocessor"].get_feature_names_out()
    importances = getattr(estimator, "feature_importances_", [0] * len(transformed))
    top = sorted(zip(transformed, importances), key=lambda item: item[1], reverse=True)[:3]
    factors = [{"feature": _factor_label(feature), "value": _feature_value(feature, row), "importance": round(float(value), 4)} for feature, value in top]
    return {
        "risk_probability": round(probability, 4), "risk_level": risk_level(probability),
        "confidence": confidence_level(probability), "top_factors": factors,
    }


def predict_all_risks(student_data: dict, course_records: list[dict] | None = None) -> dict:
    result = {"student_id": student_data.get("student_id"), "risks": {}}
    courses = course_records or []
    result["risks"]["course_failure"] = [
        {"course_id": course.get("course_id"), "course_name": course.get("course_name"), **_predict("course_failure", {**student_data, **course})}
        for course in courses
    ]
    for key in ("backlog", "gpa_threshold", "attendance_shortage", "discontinuation"):
        result["risks"][key] = _predict(key, student_data)
    return result
