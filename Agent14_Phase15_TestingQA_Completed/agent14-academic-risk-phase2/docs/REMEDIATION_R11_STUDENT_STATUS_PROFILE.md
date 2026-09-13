# Remediation R11 — Canonical Student Status & Profile Consistency

## Goal
Ensure the authorized faculty student-review page displays one coherent, backend-authoritative current status and exposes the academic evidence needed to understand that status without reimplementing risk logic in the frontend.

## Changes
- Canonical `student_summary()` now selects one primary prediction using actionable/elevated/visible priority and keeps risk score, priority, and risk level tied to that same prediction.
- Added `highest_risk_score` as an analytical field without using it to override the primary status.
- Student profile metrics now expose assignment completion, current semester, academic year, and checkpoint week.
- Student profile no longer hardcodes Semester 5 / academic cycle text.
- Course failure is represented in the main risk-evidence area using the highest-priority course-level prediction, while the full course table remains available.
- Mentor/HOD/Dean profile display continues to use backend `current_status`; no frontend risk-band calculation is used for status.
- What-If assignment completion now starts from the student's actual current value rather than `not available`.

## Safety / scope
- Students remain records only; no student application role or route is introduced.
- Support Attention remains role-restricted.
- ML remains the source of truth for quantitative risk.

## Verification
- `python scripts/test_r11_profile_consistency.py` — PASS
- R2 metrics — PASS
- R5 student profile regression — PASS
- R10 role workflow regression — PASS
- Phase 11 institutional AI regression — PASS
- Phase 15 fast QA — PASS
- Python compilation — PASS
- Fresh ZIP extraction/integrity — PASS

Known environment limitation: the full frontend production build cannot be executed in the offline runner because its npm dependency cache is incomplete.
