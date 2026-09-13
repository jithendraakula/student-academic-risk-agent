from __future__ import annotations
import json
from .config import METRICS_DIR, HISTORICAL_TRAIN_SEMESTERS, HOLDOUT_SEMESTER, CURRENT_PREDICTION_SEMESTER
from .data_loader import load_processed_data, build_training_sets, split_by_temporal_semester
from .training import train_one


def main():
    data = load_processed_data()
    sets = build_training_sets(data)
    summary = {}
    for name, spec in sets.items():
        frame = spec["frame"]
        target_col = spec["target_column"]
        train_df, test_df = split_by_temporal_semester(frame)
        meta = train_one(name, frame, target_col, train_frame=train_df, test_frame=test_df)
        summary[name] = {k: meta[k] for k in ("model", "target_column", "train_samples", "test_samples", "accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc", "decision_threshold")}
        print(f"{name}: train={len(train_df)} test={len(test_df)} f1={meta['f1']:.3f} auc={meta['roc_auc']}")
    METRICS_DIR.mkdir(exist_ok=True)
    (METRICS_DIR / "model_summary.json").write_text(json.dumps({
        "split_strategy": "temporal_semester",
        "train_semesters": list(HISTORICAL_TRAIN_SEMESTERS),
        "held_out_semester": HOLDOUT_SEMESTER,
        "current_prediction_semester": CURRENT_PREDICTION_SEMESTER,
        "models": summary,
    }, indent=2), encoding="utf-8")
    print("All five models trained and saved.")

if __name__ == "__main__":
    main()
