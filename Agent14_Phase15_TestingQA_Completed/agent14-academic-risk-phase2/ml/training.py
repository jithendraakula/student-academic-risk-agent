from __future__ import annotations
import json
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
)
from .config import METRICS_DIR, MODEL_DIR, MODEL_NAMES, SEED, LABELS
from .evaluate import timestamp
from .feature_sets import select_features
from .preprocessing import make_preprocessor


def _best_f1_threshold(probabilities, y_true) -> float:
    candidates = np.linspace(0.10, 0.90, 81)
    y = np.asarray(y_true, dtype=int)
    best = (0.5, -1.0)
    for t in candidates:
        pred = (probabilities >= t).astype(int)
        tp = ((pred == 1) & (y == 1)).sum()
        fp = ((pred == 1) & (y == 0)).sum()
        fn = ((pred == 0) & (y == 1)).sum()
        pr = tp / max(1, tp + fp)
        re = tp / max(1, tp + fn)
        f1 = 2 * pr * re / max(1e-12, pr + re)
        if f1 > best[1]:
            best = (float(t), float(f1))
    return best[0]


def _base_pipeline(x_train, features):
    pre = make_preprocessor(x_train, features)
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=7,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=SEED,
        n_jobs=-1,
    )
    return Pipeline([("preprocessor", pre), ("model", model)])


def _fit_calibrated(x_train, y_train, features):
    base = _base_pipeline(x_train, features)
    return CalibratedClassifierCV(
        estimator=base,
        method="sigmoid",
        cv=3,
        n_jobs=1,
    ).fit(x_train, y_train)


def _factor_pipeline(calibrated_pipeline):
    classifiers = getattr(calibrated_pipeline, "calibrated_classifiers_", [])
    if classifiers:
        estimator = getattr(classifiers[0], "estimator", None)
        if estimator is not None and hasattr(estimator, "named_steps"):
            return estimator
    if hasattr(calibrated_pipeline, "named_steps"):
        return calibrated_pipeline
    raise TypeError("Unable to locate fitted base pipeline for feature importance")


def train_one(name, frame, target_column, train_frame, test_frame):
    features = select_features(frame, name)
    x_train = train_frame[features].copy()
    x_test = test_frame[features].copy()
    y_train = train_frame[target_column].astype(int)
    y_test = test_frame[target_column].astype(int)
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError(f"{name}: train/test must both contain two classes")

    # Use a training-only validation slice to select the alert/decision threshold.
    internal_x, val_x, internal_y, val_y = train_test_split(
        x_train,
        y_train,
        test_size=0.20,
        stratify=y_train,
        random_state=SEED,
    )
    threshold_model = _fit_calibrated(internal_x, internal_y, features)
    val_probabilities = threshold_model.predict_proba(val_x)[:, 1]
    threshold = _best_f1_threshold(val_probabilities, val_y)

    # Final probability model is refit on the complete temporal training set.
    pipeline = _fit_calibrated(x_train, y_train, features)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    pred = (probabilities >= threshold).astype(int)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(y_test, probabilities)), 4),
        "holdout_positive_rate": round(float(y_test.mean()), 4),
        "holdout_mean_predicted_probability": round(float(probabilities.mean()), 4),
    }

    factor_pipeline = _factor_pipeline(pipeline)
    transformed = factor_pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    importances = factor_pipeline.named_steps["model"].feature_importances_
    metadata = {
        "model_key": name,
        "model": "Calibrated RandomForestClassifier",
        "base_model": "RandomForestClassifier",
        "calibration_method": "sigmoid",
        "calibration_cv": 3,
        "target": LABELS[name],
        "target_column": target_column,
        "train_semesters": [int(x) for x in sorted(train_frame.semester.unique())],
        "held_out_semester": int(test_frame.semester.iloc[0]),
        "train_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
        "positive_train": int(y_train.sum()),
        "negative_train": int((y_train == 0).sum()),
        "positive_test": int(y_test.sum()),
        "negative_test": int((y_test == 0).sum()),
        "feature_columns": features,
        "transformed_feature_count": len(transformed),
        "decision_threshold": threshold,
        "threshold_selection": "20% training-only validation split optimized for F1 after probability calibration",
        "top_global_features": [
            {"feature": f, "importance": round(float(i), 6)}
            for f, i in sorted(zip(transformed, importances), key=lambda z: z[1], reverse=True)[:10]
        ],
        "trained_at": timestamp(),
        **metrics,
    }
    MODEL_DIR.mkdir(exist_ok=True)
    METRICS_DIR.mkdir(exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "decision_threshold": threshold,
            "metadata": metadata,
        },
        MODEL_DIR / MODEL_NAMES[name],
    )
    (METRICS_DIR / f"{name}_metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
