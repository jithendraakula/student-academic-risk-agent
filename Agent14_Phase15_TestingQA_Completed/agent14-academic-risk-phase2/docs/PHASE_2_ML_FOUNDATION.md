# Phase 2 / R1 — ML Foundation and Risk Calibration

Agent 14 uses five ML risk models for the early-warning workflow: Course Failure, Backlog Accumulation, GPA Threshold, Attendance Shortage, and Support Attention.

## R1 temporal boundary
The active demo is a single 2024 CSE cohort with five semester snapshots available at checkpoint week 6. Historical semesters 1–3 are used for model training, semester 4 is a held-out temporal evaluation set, and semester 5 is the current application snapshot. Current-semester outcomes are never used for training.

## Models and probability calibration
Each model is a Random Forest wrapped in 3-fold sigmoid probability calibration. Calibration is used because raw tree probabilities were materially over-confident for the lower-prevalence risks. The stored decision threshold is selected only from a training-only validation slice after calibration.

Stored evaluation metadata includes:
- Accuracy
- Balanced accuracy
- Precision
- Recall
- F1
- ROC-AUC
- Brier score
- Holdout positive rate
- Holdout mean predicted probability
- Selected decision threshold

## Risk bands
Calibrated probabilities are mapped to product-facing risk levels:
- 0–19.9%: LOW
- 20–39.9%: MODERATE
- 40–59.9%: HIGH
- 60–100%: CRITICAL

The critical band is intentionally conservative so the mentor queue remains small enough for real faculty follow-up.

## R1 acceptance philosophy
The demo dataset is intentionally mostly stable, with a small high/critical pocket. R1 acceptance therefore checks both model quality and operational prevalence. The current 500-student population is expected to keep unique students in the HIGH/CRITICAL band well below a crisis-level share, with no section permitted to exceed 10 critical students.

## Run
From the project root:

```powershell
python data/generators/generate_all.py
python -m ml.train_all
python scripts/test_r1_ml.py
python -m ml.smoke_test
```

The artifacts are written to `ml/models/` and `ml/metrics/`.
