# Remediation R1 — ML Rebuild & Risk Calibration

## Goal
R1 rebuilds the risk models against the R0 CSE dataset, reduces probability over-confidence, and checks that the current 500-student population does not look like an institution-wide crisis.

## Data boundary
- 500 active CSE students
- 10 sections × 50 students
- Current semester: 5
- Historical training semesters: 1–3
- Temporal holdout: semester 4
- Checkpoint: week 6

## Outcome design
Historical outcomes are generated from latent academic conditions plus observable metrics. They are stochastic rather than direct threshold copies. The intended demo prevalence is low enough to create a small actionable queue while retaining enough positive cases for meaningful model evaluation.

Observed R1 historical rates:
- Course failure: 4.2%
- New backlog: 8.1%
- GPA below threshold: 4.4%
- Attendance shortage: 5.8%
- Support/discontinuation outcome: 0.4%

## Model design
Each risk model is a Random Forest with 3-fold sigmoid probability calibration. The calibration layer reduces the material over-prediction seen in the raw tree probabilities. Threshold selection remains confined to a training-only validation split.

## Product-facing risk bands
- LOW: < 20%
- MODERATE: 20–39.9%
- HIGH: 40–59.9%
- CRITICAL: >= 60%

These severity bands are separate from the stored decision threshold and from the canonical alert priority threshold.

## R1 operational acceptance
For the 500-student current population, the calibrated worst-risk distribution is small enough for mentor review and respects the user-defined section limit:
- HIGH/CRITICAL students: 34/500
- CRITICAL students: 16/500
- Maximum CRITICAL students in any section: 4

No section approaches the requested maximum of 10 critical students.

## Model acceptance snapshot
The held-out semester AUC/Brier metrics are stored per model in `ml/metrics/`. Course-failure is intentionally the weakest of the five models and is retained as a baseline-quality signal rather than being hidden. The stronger student-level models show useful temporal discrimination, especially GPA and attendance.

## Run
```powershell
python data/generators/generate_all.py
python -m ml.train_all
python scripts/test_r1_ml.py
python -m ml.smoke_test
```
