"""R1 ML quality, calibration, and operational prevalence gate."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
METRICS = ROOT / "ml" / "metrics"
sys.path.insert(0, str(ROOT))

EXPECTED = {
    "course_failure": {"min_auc": 0.60, "max_brier": 0.10},
    "backlog": {"min_auc": 0.68, "max_brier": 0.10},
    "gpa_threshold": {"min_auc": 0.75, "max_brier": 0.08},
    "attendance_shortage": {"min_auc": 0.80, "max_brier": 0.08},
    "discontinuation": {"min_auc": 0.90, "max_brier": 0.03},
}


def main() -> int:
    from ml.predictor import predict_student_batch

    errors: list[str] = []
    students = pd.read_csv(DATA / "students.csv")
    semester = pd.read_csv(DATA / "student_semester_features.csv")
    outcomes = pd.read_csv(DATA / "historical_outcomes.csv")
    manifest = json.loads((DATA / "dataset_manifest.json").read_text(encoding="utf-8"))

    if manifest.get("dataset_version") not in {"agent14-cse-2026-r1", "agent14-cse-2026-r8"}:
        errors.append("dataset version is not a supported R1/R8 dataset version")
    if len(students) != 500:
        errors.append(f"expected 500 students, got {len(students)}")

    outcome_rates = outcomes[["course_failed", "new_backlog", "gpa_below_threshold", "attendance_shortage", "discontinued"]].mean()
    rate_bounds = {
        "course_failed": (0.01, 0.08),
        "new_backlog": (0.02, 0.10),
        "gpa_below_threshold": (0.01, 0.06),
        "attendance_shortage": (0.01, 0.07),
        "discontinued": (0.002, 0.03),
    }
    for col, (lo, hi) in rate_bounds.items():
        rate = float(outcome_rates[col])
        if not (lo <= rate <= hi):
            errors.append(f"{col} outcome rate {rate:.3f} outside [{lo}, {hi}]")

    for name, rules in EXPECTED.items():
        meta = json.loads((METRICS / f"{name}_metrics.json").read_text(encoding="utf-8"))
        if meta["roc_auc"] < rules["min_auc"]:
            errors.append(f"{name} AUC {meta['roc_auc']:.3f} < {rules['min_auc']}")
        if meta["brier_score"] > rules["max_brier"]:
            errors.append(f"{name} Brier {meta['brier_score']:.3f} > {rules['max_brier']}")
        if abs(meta["holdout_mean_predicted_probability"] - meta["holdout_positive_rate"]) > 0.05:
            errors.append(f"{name} calibration gap > 0.05")

    current = semester.loc[semester["snapshot_type"].eq("current")].copy()
    results = predict_student_batch(current.to_dict("records"))
    rows = []
    for risk_type, values in results.items():
        d = pd.DataFrame(values)
        d["risk_type"] = risk_type
        d["student_id"] = current["student_id"].to_numpy()
        rows.append(d)
    risks = pd.concat(rows, ignore_index=True)
    rank_map = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
    risks["risk_rank"] = risks["risk_level"].map(rank_map)
    worst = risks.sort_values(["student_id", "risk_rank", "risk_score"], ascending=[True, False, False]).drop_duplicates("student_id")
    high_critical = int(worst["risk_rank"].ge(3).sum())
    critical = int(worst["risk_rank"].eq(4).sum())
    if high_critical > 75:
        errors.append(f"current HIGH/CRITICAL student population too large: {high_critical}/500")
    if critical == 0:
        errors.append("current demo has no critical students after calibration")

    section_view = worst[["student_id", "risk_level"]].merge(current[["student_id", "section"]], on="student_id")
    critical_per_section = section_view.assign(critical=section_view["risk_level"].eq("CRITICAL")).groupby("section")["critical"].sum()
    if int(critical_per_section.max()) > 10:
        errors.append(f"critical students exceed 10 in a section: {critical_per_section.to_dict()}")

    print("R1 OUTCOME RATES:", outcome_rates.round(3).to_dict())
    print("R1 CURRENT WORST-RISK COUNTS:", worst["risk_level"].value_counts().to_dict())
    print("R1 HIGH/CRITICAL STUDENTS:", high_critical)
    print("R1 CRITICAL STUDENTS:", critical)
    print("R1 CRITICAL BY SECTION:", critical_per_section.astype(int).to_dict())

    if errors:
        print("R1 ML CALIBRATION TEST FAILED")
        for error in errors:
            print("ERROR:", error)
        return 1
    print("R1 ML CALIBRATION TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
