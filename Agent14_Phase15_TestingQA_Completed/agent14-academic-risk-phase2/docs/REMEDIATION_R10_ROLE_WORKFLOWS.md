# Remediation R10 — Role Workflow Corrections

## Purpose
Correct role-specific workflow mismatches found during the pre-deployment audit without changing the underlying ML, canonical metric, alert, intervention, or notification semantics.

## Product rules preserved
- Students remain records only; the application is for mentors, HOD, Dean and other verified authorities.
- Mentor AI is mentor-only.
- HOD/Dean use their authorized institutional AI workspace.
- Backend RBAC remains authoritative.
- Risk/priority status shown in the profile comes from the canonical backend summary.

## Changes
1. HOD mentor drill-down sections are returned by the API from the selected mentor's actual student assignments. The UI no longer hardcodes A/B.
2. HOD risk filtering uses the canonical `support_attention` key.
3. Student profile receives a canonical `current_status` object from the backend and no longer re-creates overall risk level from frontend thresholds.
4. Mentor AI controls render only for mentor users. HOD and Dean users get role-appropriate guidance instead of a control that would return 403.

## Verification
- `python scripts/test_r10_role_workflows.py` — PASS
- `python scripts/test_r7_final_qa.py` — PASS
- `python scripts/test_phase15_qa.py` — PASS
- `python scripts/test_phase11_api.py` — PASS
- Phase 3/4/5/6/8/9/10/12/14 regressions — PASS
- Python compilation — PASS

The real frontend production build remains environment-dependent until the target machine installs the complete npm dependency tree.
