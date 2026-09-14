# Remediation R3 — Backend Performance & Data Loading

## Goal

Remove unnecessary ML/database work from normal dashboard and student-profile GET requests and provide honest loading states while the initial data snapshot is being prepared.

## Design

1. Current risk predictions are warmed once at application startup through `warm_current_risk_store()`.
2. Ordinary alert reads are read-only. `get_active_alerts(..., synchronize=False)` no longer runs ML or alert synchronization.
3. Synchronization remains opt-in for flows that intentionally refresh predictions.
4. Student profile reads reuse the persisted `RiskPrediction` snapshot and only refresh on a true cache miss.
5. Frontend KPI cards use skeleton/loading states instead of displaying misleading zero values during the initial request.
6. Existing security response timing (`X-Response-Time-ms`) remains available for deployment diagnostics.

## Read-path contract

`GET /api/mentor/summary`, HOD summary/comparison, Dean summary/comparison, notification/alert reads, and student profile reads should not regenerate ML predictions when the canonical current snapshot already exists.

## Fallback

If startup warming fails, lazy prediction generation remains available on a true cache miss. The failure is not hidden from the actual service test; this fallback is intentionally defensive.

## Verification

- R3 performance contract test
- Python compilation
- Existing R0/R1/R1.5/R2 data and ML tests
- Existing Phase 3–15 regressions that run within the environment budget
- Frontend TS/TSX parsing
- Fresh ZIP extraction/integrity

## Known environment limit

A full production Vite build requires the project's npm dependency cache, which is not available in the offline runner.
