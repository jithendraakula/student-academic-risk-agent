# Agent 14 ML — Phase 2

Phase 2 trains five baseline Random Forest risk models using a strict temporal/cohort boundary.

## Training boundary
Historical **week-6 checkpoint features** are joined to **end-of-semester outcomes**. Cohort `2025` is held out for evaluation; cohorts `2023` and `2024` are used for training. No current-semester outcome is used for training.

## Models
- Course Failure Risk
- Backlog Accumulation Risk
- GPA Threshold Risk
- Attendance Shortage Risk
- Support Attention Risk

## Run
From the project root:

```powershell
python -m ml.train_all
python -m ml.smoke_test
```

Artifacts are written to `ml/models/` and metrics/metadata to `ml/metrics/`.

## Interpretation
The metrics are held-out cohort metrics, not training accuracy. The per-prediction `top_factors` are model-guided counterfactual feature contributions intended for explanation, not causal attribution.
