# Phase 2 — ML Risk Prediction Engine

## Status
**Complete.**

## Training contract
Five baseline Random Forest classifiers are trained from historical week-6 checkpoint data. Cohort **2025** is held out entirely for evaluation; cohorts **2023 and 2024** are training cohorts. Current-semester outcome fields are never used for training.

### Models
- Course Failure Risk — student + course
- Backlog Accumulation Risk — student + semester
- GPA Threshold Risk — student + semester
- Attendance Shortage Risk — student + semester
- Support Attention Risk — student + semester

### Evaluation
The classification threshold is selected using 3-fold out-of-fold predictions from the **training cohorts only**, optimizing F1. Final metrics are then computed once on the held-out 2025 cohort. The stored metrics include accuracy, balanced accuracy, precision, recall, F1, ROC-AUC, and the selected threshold.

### Explainability
Model artifacts store global feature importance metadata. The predictor converts the most important model features into faculty-friendly labels and returns them as `top_factors`. These are model-guided factors, not causal explanations.

## Commands
From the project root:

```powershell
python -m ml.train_all
python -m ml.smoke_test
python scripts/validate_phase1_data.py
```

## Expected model behavior
Metrics are held-out metrics and should not be expected to be perfect. Extremely high performance should trigger a leakage review.
