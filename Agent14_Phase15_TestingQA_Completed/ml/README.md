# Agent 14 ML — R1 Risk Calibration

Agent 14 trains five calibrated ML risk models using checkpoint-week academic features and historical end-of-semester outcomes.

## Active demo boundary
- Cohort: 2024 CSE
- Historical training semesters: 1, 2, 3
- Temporal holdout: semester 4
- Current application snapshot: semester 5
- Checkpoint: week 6

## Models
- Course Failure Risk
- Backlog Accumulation Risk
- GPA Threshold Risk
- Attendance Shortage Risk
- Support Attention Risk

## Calibration
Each model uses a Random Forest wrapped in 3-fold sigmoid probability calibration. This materially improves the relationship between predicted probabilities and the observed holdout prevalence for low-prevalence risks. Decision thresholds are selected only from a training-only validation split.

## Product risk bands
- LOW: < 20%
- MODERATE: 20–39.9%
- HIGH: 40–59.9%
- CRITICAL: >= 60%

These bands are product severity bands, not the training decision threshold. Alerts are still created by the canonical priority engine.

## Run
```powershell
python data/generators/generate_all.py
python -m ml.train_all
python scripts/test_r1_ml.py
python -m ml.smoke_test
```
