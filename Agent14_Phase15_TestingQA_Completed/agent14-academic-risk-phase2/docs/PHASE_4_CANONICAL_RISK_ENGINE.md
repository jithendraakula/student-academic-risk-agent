# Phase 4 — Canonical Risk & Priority Engine

## Goal
Make `RiskPrediction` the single source of truth for current academic risk and priority, then project actionable records into the alert/intervention lifecycle.

## Implemented
- Formalized five canonical risk keys:
  - `course_failure`
  - `backlog`
  - `gpa_threshold`
  - `attendance_shortage`
  - `discontinuation` (UI label: **Support Attention Risk**)
- Added legacy risk-name normalization so old demo rows such as `attendance`, `gpa`, and `support_attention` map to canonical keys.
- Centralized the alert policy:
  - priority `>= 60` creates an alert;
  - `CRITICAL` risk is an alert override even when priority is below 60.
- Kept risk and priority separate:
  - risk score comes from the ML probability;
  - priority uses confidence, intervenability, and urgency.
- Added canonical alert synchronization from current `RiskPrediction` snapshots.
- Added course-specific alert support through the existing JSON `data.course_id` field, avoiding an unnecessary schema break.
- Preserved intervention lifecycle states (`NEW`, `ACKNOWLEDGED`, `ACTION_TAKEN`, `FOLLOW_UP`, `RESOLVED`) while refreshing risk/priority metadata from prediction snapshots.
- Automatically closes stale/superseded alert projections and marks them as historical.
- Mentor watchlist, HOD mentor comparison, HOD student drill-down, and Dean department analytics now use the same canonical risk/priority definitions.
- Dean risk heatmap uses current `RiskPrediction` records and one shared heatmap risk threshold.
- Support Attention Risk remains role-restricted and hidden from Admin API output.

## Source-of-truth rule
```text
ML models
   ↓
RiskPrediction  ← canonical risk + confidence + priority
   ↓
AlertIntervention  ← actionable lifecycle projection
   ↓
Mentor / HOD / Dean dashboards
```

`AlertIntervention` is no longer allowed to independently define risk or priority for dashboards.

## Validation
- Phase 1 data validation: PASS
- ML smoke test: PASS
- Python compilation: PASS
- Phase 4 API/RBAC/persistence regression test: PASS
- Canonical risk-name normalization: PASS
- Alert policy determinism: PASS
- Mentor isolation and HOD department isolation: PASS
- Intervention lifecycle update over canonical alert: PASS

## Limitation carried forward
Frontend production build was not re-run successfully in the offline build runner because the available `node_modules` installation is incomplete and external npm package installation is unavailable. Phase 4 did not change frontend source files.
