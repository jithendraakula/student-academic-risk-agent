import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

try:
    from .config import METRICS_DIR, MODEL_DIR, SEED, TEST_SIZE, MODEL_NAMES
    from .evaluate import evaluate_model, timestamp
    from .feature_sets import select_features
    from .preprocessing import make_preprocessor
except ImportError:
    from config import METRICS_DIR, MODEL_DIR, SEED, TEST_SIZE, MODEL_NAMES
    from evaluate import evaluate_model, timestamp
    from feature_sets import select_features
    from preprocessing import make_preprocessor


def train_one(name, frame, target, target_description):
    feature_columns = select_features(frame, name)
    if not feature_columns:
        raise ValueError(f"No features remain for {name}")
    x = frame[feature_columns].copy()
    y = target.astype(int)
    if y.nunique() < 2:
        raise ValueError(f"{name} target must contain both classes")
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, random_state=SEED, stratify=y,
    )
    preprocessor = make_preprocessor(x, feature_columns)
    estimator = RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=2,
        class_weight="balanced", random_state=SEED, n_jobs=-1,
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
    pipeline.fit(x_train, y_train)
    metrics = evaluate_model(pipeline, x_test, y_test)
    transformed = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    metadata = {
        "model_key": name, "model": "RandomForestClassifier", "target": target_description,
        "feature_columns": feature_columns, "transformed_features": transformed,
        "train_samples": int(len(x_train)), "test_samples": int(len(x_test)),
        "positive_class_count": int(y.sum()), "negative_class_count": int((y == 0).sum()),
        "feature_count": len(feature_columns), "trained_at": timestamp(), **metrics,
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_DIR / MODEL_NAMES[name])
    with (METRICS_DIR / f"{name}_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    return pipeline, metadata
