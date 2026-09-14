# Agent 14 — Remediation R2: Canonical Metrics & Count Semantics

## Purpose
R2 removes ambiguity between unique student counts, elevated risk exposure, risk signals, and alert/intervention workload.

## Canonical definitions
- **Monitored students:** unique students in the viewer's authorized scope.
- **Elevated-risk students:** unique students with at least one risk score >= 40 (HIGH or CRITICAL).
- **High-risk students:** unique students with at least one HIGH or CRITICAL risk.
- **Critical students:** unique students with at least one CRITICAL risk.
- **Needs action:** unique students with at least one risk signal satisfying the canonical alert policy.
- **Risk signal:** one student + risk-type combination at elevated risk. Multiple course-failure courses still count as one course-failure student signal for dashboard KPIs.
- **Actionable risk signal:** one student + risk-type combination satisfying the canonical alert policy.
- **Open alerts:** active `AlertIntervention` work items. These are not student counts; one student may have several open alerts.
- **Open alert students:** unique students represented by open alert work items.

## Dashboard communication
Mentor, HOD, and Dean surfaces now explicitly distinguish:
1. Student population metrics.
2. Risk exposure metrics.
3. Alert/workload metrics.

Risk distribution cards count unique students once per risk type. A student can appear in more than one risk type, so cross-risk totals are not expected to equal the monitored-student total.

## Canonical source
The `RiskPrediction` store remains the source of risk/priority truth. `AlertIntervention` remains the actionable work-item projection.

## Thresholds
- Elevated risk: `40` risk score.
- Critical risk: `60` risk score / CRITICAL band.
- Alert priority threshold: `60`.
- Critical override: enabled.

## Regression coverage
`python scripts/test_r2_metrics.py` verifies duplicate course failures are deduplicated at student-risk-type level, LOW predictions do not appear as affected risk, alerts remain distinct from unique-student counts, and cross-metric invariants hold.
