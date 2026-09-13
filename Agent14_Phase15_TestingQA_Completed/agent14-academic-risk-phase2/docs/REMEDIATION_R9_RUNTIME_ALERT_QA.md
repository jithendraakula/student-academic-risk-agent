# Remediation R9 — Runtime Alert & QA Truth

## Goal

Make the runtime alert state and the QA layer agree on what an alert count means.

## Canonical meaning

- `RiskPrediction` is the source of risk and priority truth.
- `AlertIntervention` is the live actionable work-item projection.
- `open_alerts` counts active `AlertIntervention` work items.
- `open_alert_students` counts unique students represented by those active alerts.
- `alerts_interventions.csv` is seed/demo input and is **not** itself the live dashboard KPI.

## Verification gate

Run:

```powershell
python scripts/test_r9_runtime_alerts.py
```

The test creates a fresh runtime database, performs normal application startup/prewarming, validates that active alerts point to current canonical predictions, compares the dashboard metrics with the runtime database, and runs the warm/sync path twice to verify idempotency.

This specifically prevents a QA script from passing by only counting seed CSV rows.
