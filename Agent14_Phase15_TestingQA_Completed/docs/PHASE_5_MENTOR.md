# Phase 5 — Mentor Workspace

## Goal
Turn the mentor role into the first complete operational workflow on top of the canonical risk/priority engine.

## Implemented
- Added a mentor workspace service based on `RiskPrediction` plus the `AlertIntervention` lifecycle projection.
- Added mentor summary endpoint with one canonical set of counts:
  - assigned students
  - critical students
  - high-risk students
  - students needing action
  - open alerts
  - new alerts
- Added assignment-scoped mentor student search/filter endpoint.
- Supported filters for student name/ID, risk type, severity, alert status, and needs-action.
- Added mentor student drill-down endpoint with the same scoped data contract.
- Mentor students are aggregated one row per student, preventing alert multiplicity from inflating student counts.
- Support Attention Risk remains visible to mentors while still restricted from Admin.
- Mentor dashboard now uses canonical counts rather than recalculating risk from alert rows.
- Added mentor queue filters and search.
- Mentor intervention workflow supports acknowledgement, action taken, follow-up, resolution, notes, and follow-up date.
- Kept the existing institutional visual language and Vignan University header treatment.

## Source of truth
```text
ML models
   ↓
RiskPrediction
   ↓
Priority + alert policy
   ↓
Mentor workspace aggregation
   ↓
Mentor intervention lifecycle
```

## Validation
Phase 1 data validation, ML smoke test, Python compilation, Phase 3 regression, Phase 4 regression, and Phase 5 mentor workflow/RBAC tests should all remain green.
