from __future__ import annotations
import json
from .config import HOLDOUT_SEMESTER, MODEL_NAMES, MODEL_DIR
from .data_loader import load_processed_data, build_training_sets, split_by_temporal_semester
from .predictor import predict_all_risks


def main():
    data = load_processed_data()
    sets = build_training_sets(data)
    for name, spec in sets.items():
        train, test = split_by_temporal_semester(spec["frame"])
        assert len(train) > 0 and len(test) > 0
        assert set(train["semester"]).isdisjoint(set(test["semester"]))
        assert max(train["semester"]) < HOLDOUT_SEMESTER
        assert set(test["semester"]) == {HOLDOUT_SEMESTER}
        assert train[spec["target_column"]].nunique() == 2
        assert test[spec["target_column"]].nunique() == 2
        assert (MODEL_DIR / MODEL_NAMES[name]).exists(), f"missing {name} model"
    s = data["semester"].loc[data["semester"].snapshot_type.eq("current")].sort_values(["student_id", "semester"]).iloc[0].to_dict()
    c = data["course"].loc[(data["course"].student_id.eq(s["student_id"])) & (data["course"].semester.eq(s["semester"]))].drop(columns=["course_failed"]).to_dict("records")
    result = predict_all_risks(s, c)
    assert len(result["risks"]["course_failure"]) == 5
    assert all("risk_score" in x for x in result["risks"]["course_failure"])
    print(json.dumps(result, indent=2, default=str))
    print("ML SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
