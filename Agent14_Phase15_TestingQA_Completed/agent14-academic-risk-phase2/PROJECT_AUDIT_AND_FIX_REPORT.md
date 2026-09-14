# Student Academic Risk Management – Audit & Fix Report

## Implemented fixes

### 1. Student Queue risk identification
Every student row now exposes a `risk_breakdown` generated from the current canonical risk predictions. The queue can therefore show multiple risks for the same student instead of only the primary risk.

Example:
- Attendance Shortage Risk · CRITICAL
- GPA Threshold Risk · HIGH
- Backlog Accumulation Risk · MODERATE

For course-failure predictions, affected course IDs are also included when available.

### 2. Risk filtering
The Mentor risk-level filter now treats the legacy `MEDIUM` value as `MODERATE`, matching the UI. Risk-type filtering now also recognizes actionable risk types, not only elevated risk types.

### 3. Mark as Complete runtime bug
`complete_student_case()` was calling `sync_canonical_alerts()` without importing it. This produced a server-side `NameError` at runtime. The missing import is fixed.

### 4. Database persistence
Completion remains server/database authoritative. The workflow resolves all open interventions for the selected student's current case and creates/updates the completion marker and intervention history.

### 5. New-risk reactivation
A completed case is not treated as permanently closed. If a newer canonical prediction snapshot is generated after the recorded completion time, the corresponding alert is eligible to reopen.

### 6. Dashboard workflow metrics
Mentor, HOD, Dean and Admin dashboards expose persisted completion information. Open case counts are derived from active work and therefore decrease after completion; completed-case counts increase.

Risk classification counts (Critical/High/etc.) remain model metrics and do **not** decrease merely because an intervention was completed. This is intentional: completing mentor work does not change the student's underlying academic risk prediction.

### 7. Admin refresh
Admin dashboard now refreshes on the shared case-work event and on the same periodic refresh cadence used by the other oversight dashboards.

## Verified

- Backend Python compilation: PASS
- Seeded database workflow: PASS
- Risk breakdown generation: PASS
- Mark-case-complete persistence: PASS
- Open-case count decreases after completion: PASS
- Completed-case count increases after completion: PASS
- Repeated workspace reload preserves completion state: PASS
- HOD mentor auto-scroll remains present: PASS

The seeded test used the project's processed data and confirmed `students.csv` contains 500 student records.

## Environment limitation

The uploaded project did not contain frontend `node_modules`. The environment could not download npm/pip dependencies because external package access was unavailable. Therefore a full production frontend build could not be executed here. Type checking currently stops at the missing `vite/client` type package in this environment.

## Remaining improvements recommended

1. Add a real database migration system (Alembic) instead of relying on startup schema creation and ad-hoc ALTER TABLE logic.
2. Replace 15-second polling with a WebSocket/SSE update channel for truly live dashboard synchronization.
3. Add a dedicated `case_id`/case table so a student case has a stable lifecycle independent of individual risk alerts.
4. Record structured completion metadata such as action category, mentor notes, completion reason and follow-up outcome.
5. Add automated API integration tests for login, queue filtering, completion, profile reload and dashboard KPI consistency.
6. Add frontend error-boundary handling and a standard toast/confirmation pattern for destructive or irreversible workflow actions.
7. Add pagination/server-side filtering for larger student cohorts.
8. Add explicit database uniqueness/index constraints for completion markers and current case state.
9. Add an audit-log screen/filtering workflow for HOD/Admin review.
10. Keep model risk metrics separate from operational case metrics, as implemented in this revision.
