# Agent 14 — Project State Checkpoint

## Current Phase
**Remediation R2 — Canonical Metrics & Count Semantics (COMPLETE)**

Deployment is intentionally paused while the remediation roadmap is completed.

## Completed in Phase 1 — Data Foundation
- Original Phase 1 dataset is superseded by Remediation R0.
- Current active demo: CSE only, 500 students across CSE-A through CSE-J (50/section), batch 2024, semester 5.
- Five mentors, each responsible for exactly two sections / 100 students; one CSE HOD; one Dean.
- Longitudinal semester checkpoints: 2,500 rows (semesters 1–4 historical, semester 5 current).
- Course checkpoint data: 12,500 rows (five courses per semester).
- Historical end-of-semester outcomes: 2,000 rows.
- Academic reference data: 25 rows.
- Contextual academic observations: 123 rows.
- Current seed alert/intervention demo records: 72 rows.
- Roll numbers: 241FA04001 through 241FA04500.
- Phase 1 validator checks schema, keys, references, chronology, ranges, class balance, and leakage-copy conditions.

## Completed in Phase 2 — ML Foundation
- Historical checkpoint snapshots are joined to same-semester outcomes by student + cohort + semester + checkpoint.
- After the one-cohort R0 reset, the active training boundary is temporal: semesters 1–3 train, semester 4 is held out, semester 5 is current prediction input.
- Five calibrated Random Forest models are persisted in `ml/models/`.
- Metrics/metadata persisted in `ml/metrics/`.
- Training-only threshold optimization added for F1.
- Predictor contract returns probability, score, severity, confidence, decision threshold, and top model factors.
- Backend current-course lookup is restricted to the student's latest/current semester.

## Completed in Phase 3 — Backend Foundation
- Centralized runtime configuration under `backend/app/core/config.py`.
- Centralized JWT/password primitives under `backend/app/core/security.py`.
- Shared FastAPI authentication and role dependencies under `backend/app/core/dependencies.py`.
- Mentor student access is assignment-scoped.
- HOD student access is department-scoped.
- Dean/Admin access is controlled by role policy.
- Support/discontinuation risk remains hidden from Admin API output.
- Added canonical `risk_predictions` database table with risk, confidence, model version, intervenability, and priority fields.
- Added centralized current-risk aggregation service used by HOD/Dean analytics.
- Added batched current-risk generation so dashboards do not make hundreds of one-student model calls.
- Prediction API remains compatible with the existing frontend while adding priority/intervenability/model-version data.
- `/api/health` now checks database connectivity.
- CORS origins are configurable through environment variables.

## Phase 3 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- FastAPI API tests (using a test-only auth stub because `python-jose`/`passlib` packages are unavailable in the offline runner): PASS.
- Mentor assigned-student access isolation: PASS.
- HOD department isolation: PASS.
- Admin role protection: PASS.
- Current prediction persistence: PASS.
- ZIP integrity/extraction: PASS.
- Frontend production build: NOT VERIFIED in this runner because the available `node_modules` installation is incomplete (`vite/client` and `node` type definitions missing) and external npm package installation is unavailable. The frontend source itself was not changed in Phase 3.

## Completed in Phase 4 — Canonical Risk & Priority Engine
- Formalized five canonical risk keys and legacy-name normalization.
- Centralized the alert decision policy (priority threshold + critical override).
- Kept ML risk and intervention priority as separate, explainable concepts.
- Made `RiskPrediction` the single source of truth for current dashboard risk/priority.
- Added canonical alert projection and lifecycle synchronization.
- Updated Mentor, HOD, and Dean analytics to use consistent current-risk definitions.
- Added course-specific alert context without breaking the existing database schema.
- Preserved support/discontinuation role restrictions.

## Phase 4 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 API/RBAC/persistence regression test: PASS.
- Canonical alert policy and legacy risk-name normalization: PASS.

## Completed in Phase 5 — Mentor Workspace
- Added a mentor workspace service that consumes canonical `RiskPrediction` records and alert lifecycle projections.
- Added `/api/mentor/summary` for canonical mentor counts.
- Added `/api/mentor/students` with search, risk-type, severity, alert-status, and needs-action filters.
- Added `/api/mentor/students/{student_id}` with assignment-scoped drill-down.
- Mentor queue now shows one row per student, preventing multiple alerts from inflating student counts.
- Mentor dashboard cards use backend-provided canonical counts instead of recalculating them from alert rows.
- Mentor intervention UI supports acknowledgement, action taken, follow-up, resolution, notes, and follow-up dates.
- Support Attention Risk is available to mentors while remaining restricted from Admin.

## Phase 5 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 regression test: PASS.
- Phase 5 Mentor workspace/RBAC regression test: PASS.
- Frontend production build: NOT VERIFIED in this runner because `node_modules` is incomplete (`vite/client` and `node` typings are unavailable); external npm installation is unavailable.

## Completed in Phase 6 — HOD Workspace
- Added a department-level HOD summary built from canonical current risk predictions.
- Added department risk overview cards with one affected-student count per canonical risk type.
- Added mentor comparison with assigned students, critical/high-risk students, action queue, open/new alerts, support load, and action rate.
- Preserved the principle that support load measures intervention demand, not teacher performance.
- Added mentor drill-down filters for student search, section, risk type, and needs-action state.
- Kept mentor drill-down strictly restricted to mentors inside the HOD's department.
- Department student rows now include canonical risk, priority, risk level, primary risk, and needs-action state.
- HOD can see Support Attention Risk while Admin remains restricted.
- HOD dashboard data remain backed by `RiskPrediction` and canonical alert lifecycle projections.

## Phase 6 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 regression test: PASS.
- Phase 5 Mentor regression test: PASS.
- Phase 6 HOD/RBAC/aggregation regression test: PASS.
- ZIP integrity/extraction: PASS.
- Frontend production build: NOT VERIFIED in this runner because the environment's `node_modules` is incomplete and external npm installation is unavailable.

## Completed in Phase 7 — Dean Workspace
- Added an institution-level Dean summary using the canonical RiskPrediction/current-risk aggregation layer.
- Added institution-wide risk distribution across all five canonical risk types, including Support Attention for authorized Dean users.
- Added a Dean priority queue for the highest-priority students needing action.
- Expanded department comparison with needs-action counts, active/new alert load, support-attention counts, and per-risk affected-student counts.
- Added department drill-down rows with canonical risk, priority, risk level, primary risk, and needs-action state.
- Kept the institutional heatmap based on unique affected students at the shared heatmap threshold, preventing course-level rows from inflating student percentages.
- Dean views remain college-wide while role restrictions continue to be enforced by FastAPI role dependencies.
- Frontend Dean workspace now presents the institution summary, priority queue, risk mix, heatmap, department comparison, and authorized drill-down as one consistent workflow.

## Phase 7 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 regression test: PASS.
- Phase 5 Mentor regression test: PASS.
- Phase 6 HOD regression test: PASS.
- Phase 7 Dean/RBAC/canonical aggregation regression test: PASS.
- ZIP integrity/extraction: PASS.
- Frontend production build: NOT VERIFIED in this runner because the environment's `node_modules` is incomplete and external npm installation is unavailable.

## Completed in Phase 8 — Interventions
- Added an intervention audit trail through `InterventionRecord` status-transition records.
- Formalized intervention lifecycle transitions instead of permitting arbitrary status changes.
- Required notes for recorded actions/resolution and a future follow-up date for active `FOLLOW_UP` items.
- Added role-scoped intervention summary and intervention queue endpoints for Mentor, HOD, and Dean.
- Mentor acknowledgement now records an auditable intervention transition.
- Added overdue follow-up and resolution metrics to HOD/Dean oversight.
- Preserved `RiskPrediction` as the sole risk/priority source; intervention history does not recalculate risk.

## Phase 8 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 regression: PASS.
- Phase 5 Mentor regression: PASS.
- Phase 6 HOD regression: PASS.
- Phase 7 Dean regression: PASS.
- Phase 8 intervention lifecycle/RBAC/history regression: PASS.
- ZIP integrity/extraction: PASS.
- Frontend production build: NOT VERIFIED in this runner because the environment's `node_modules` is incomplete and external npm installation is unavailable.

## Completed in Phase 9 — What-If Simulator
- Added non-persistent What-If simulation for attendance, GPA, backlog, assignment completion, and course-level performance changes.
- Simulations re-run existing ML models and the canonical priority engine without modifying Student, RiskPrediction, alerts, or intervention history.
- Added What-If regression coverage including a non-persistence check and role-scoped access.

## Phase 9 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Phase 4 regression: PASS.
- Phase 5 Mentor regression: PASS.
- Phase 6 HOD regression: PASS.
- Phase 7 Dean regression: PASS.
- Phase 8 intervention regression: PASS.
- Phase 9 What-If/RBAC/non-persistence regression: PASS.
- ZIP integrity/extraction: PASS.
- Frontend production build: NOT VERIFIED in this runner because the environment's `node_modules` is incomplete and external npm installation is unavailable.

## Completed in Phase 10 — Mentor AI Copilot
- Added server-side LLM integration with configurable Gemini or xAI/Grok providers.
- Added intent-based Mentor Copilot actions: risk summary, intervention plan, and What-If explanation.
- AI receives structured canonical risk/priority evidence and is explicitly prohibited from calculating or inventing risk values.
- API keys remain backend-only through environment configuration; frontend never receives provider credentials.
- Added grounded response parsing and provider error handling; missing configuration returns a clear 503 instead of a fake response.
- Integrated Mentor Copilot controls into the mentor student profile.
- Added an AI-provider HTTP contract test and full Mentor AI endpoint/RBAC regression test with a deterministic test provider stub.
- Support Attention/discontinuation remains support-only and role-restricted.

## Phase 10 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 regression: PASS.
- Phase 5 Mentor regression: PASS.
- Phase 6 HOD regression: PASS.
- Phase 8 intervention regression: PASS.
- Phase 9 What-If regression: PASS.
- Phase 10 Mentor AI/RBAC/non-fabrication regression: PASS.
- AI HTTP provider contract test: PASS.
- ZIP integrity/extraction: PASS.
- Phase 7 regression was not re-run to completion in this final pass because its pre-existing broad aggregation test exceeds the offline runner time budget; Phase 7 source remains unchanged by Phase 10.
- Frontend production build: NOT VERIFIED in this runner because the environment's `node_modules` is incomplete and external npm installation is unavailable.

## Completed in Phase 11 — HOD / Dean AI Analyst
- Added a grounded institutional AI analyst for HOD and Dean workflows.
- HOD analyst is department-scoped and can explain department status, mentor workload, and intervention coverage.
- Dean analyst is institution-scoped and can explain executive status, risk concentration, intervention coverage, and the canonical priority queue.
- Institutional AI consumes canonical `RiskPrediction + canonical priority engine` outputs; the LLM cannot calculate, invent, overwrite, or create new risk statistics.
- Dean priority context intentionally omits student names from the LLM payload; student-level access remains in the authorized application drill-down.
- Support Attention/discontinuation remains a support-only signal and is explicitly excluded from punitive or high-stakes recommendations.
- Added a shared frontend AI panel to HOD and Dean dashboards.
- Provider configuration reuses the Phase 10 server-side AI settings.
- Added Phase 11 regression coverage for both roles, RBAC, canonical context, non-mutation after warm-up, JSON parsing, and missing-provider behavior.

## Phase 11 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 4 canonical-risk regression: PASS.
- Phase 5 Mentor regression: PASS.
- Phase 6 HOD regression: PASS.
- Phase 7 Dean regression: PASS (fresh standalone run).
- Phase 8 intervention regression: PASS.
- Phase 9 What-If regression: PASS.
- Phase 10 Mentor AI/RBAC/non-fabrication regression: PASS.
- Phase 11 HOD/Dean AI/RBAC/scoping regression: PASS.
- ZIP integrity/extraction: PASS.
- Live Gemini/xAI provider call: NOT RUN because no production API key was available in the build environment.
- Frontend production build: NOT VERIFIED in this runner because the environment's `node_modules` is incomplete and external npm installation is unavailable.

## Next Phase
**Phase 16 — Deployment** after the R15 deployment-readiness gate.

The remediation series R0–R15 is complete. Real-environment credential and frontend-build verification remain deployment-environment tasks.

## Remediation R0 — Data & Domain Model Reset
- Replaced the mixed-department demo with a CSE-only 500-student active cohort.
- Added 10 sections, five two-section mentors, one CSE HOD, and one Dean.
- Standardized sequential 241FA04xxx roll numbers.
- Added contextual `academic_observations.csv` and the `AcademicObservation` domain model.
- Updated database seeding and demo credentials for the five CSE mentors.
- Switched the compatibility ML split to temporal semesters for the one-cohort domain.
- Updated phase regression scripts so their assumptions match the CSE-only domain.

## Remediation R0 Validation
- R0 data/domain test: PASS.
- R0 / Phase 1 data validator: PASS.
- Database seed test: PASS.
- Python compilation: PASS.
- ML compatibility smoke test: PASS.
- Phase 15 fast QA gate: PASS.
- Standalone Phase 3, 4, 5, 6, 7, 8, 9, 10, 12, and 14 regressions: PASS.
- Phase 11 later rerun was not completed within the offline runner budget; it was previously verified in its own phase.
- Frontend production build and live external provider/SMTP delivery remain environment/provider dependent and are not claimed as verified.

## Phase 13 — UI/UX

Completed: institutional visual system, Vignan branding assets from supplied reference, shared responsive shell, role navigation, notification bell, redesigned login, common cards/tables, workspace intro sections and AI analyst presentation. Backend APIs and risk logic were intentionally left unchanged.


## Completed in Phase 14 — Security
- Hardened JWTs with explicit access-token claims, server-side session registry, persisted logout revocation, and live role validation.
- Removed plaintext password fallback and enforced password-change policy.
- Added login failure throttling and temporary lockout controls.
- Added security audit logging and Admin audit-log access.
- Added production CORS/trusted-host/JWT configuration guardrails and optional production docs disablement.
- Added request-size limits and security response headers including CSP, frame protection, no-sniff, permissions policy, request IDs, and auth no-store.
- Frontend logout now requests server-side revocation and clears sessionStorage.
- Preserved all Mentor/HOD/Dean/Admin RBAC and Support Attention restrictions.

## Phase 14 Validation
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 3 regression: PASS.
- Phase 4 regression: PASS.
- Phase 5 Mentor regression: PASS.
- Phase 6 HOD regression: PASS.
- Phase 7 Dean regression: PASS.
- Phase 8 intervention regression: PASS.
- Phase 9 What-If regression: PASS.
- Phase 10 Mentor AI regression: PASS.
- Phase 11 HOD/Dean AI regression: PASS.
- Phase 12 Notifications regression: PASS.
- Phase 14 Security/RBAC/session/audit regression: PASS.
- Frontend TypeScript/TSX syntax remains expected to parse; full production build is not verified in this offline runner because `node_modules` is intentionally absent/incomplete.


## Completed in Phase 15 — Testing & QA
- Added a dependency-light cumulative QA gate at `scripts/test_phase15_qa.py`.
- Added deterministic checks for Python syntax, processed-data schema/counts, canonical risk aliases/priority policy, frontend package/branding/workflow contract, and frontend secret leakage.
- Added an optional `--full` mode that runs the existing phase regression scripts with an isolated SQLite database per phase.
- Added `test_artifacts/phase15_report.json` as the latest machine-readable QA report.
- Preserved the principle that tests are only marked PASS when actually executed; environment/provider limitations are called out separately.

## Phase 15 Validation
- Fast QA gate: PASS.
- Phase 1 data validator: PASS.
- ML smoke test: PASS.
- Python AST syntax check: PASS (72 Python files parsed).
- Processed data contract: PASS (500 students, 7 authority records, 500 assignments, 2,500 semester snapshots, 12,500 course snapshots, 2,000 historical outcomes, 25 reference rows, 145 observations, 72 alert/intervention rows).
- Canonical risk/priority policy checks: PASS.
- Frontend contract/branding/secret scan: PASS (29 TS/TSX files checked).
- Phase 3, 4, 5, 6, 7, 8, 9, 10, 12, and 14 endpoint/security regressions: PASS in standalone fresh-database runs during Phase 15 work.
- Phase 11 institutional AI regression: previously PASS in its Phase 11 verification; a Phase 15 rerun exceeded this offline runner's time budget because it materializes the full canonical current-risk store. It is therefore **not re-marked as a Phase 15 rerun PASS**.
- Frontend production build: NOT VERIFIED in this offline runner because `node_modules` is incomplete/unavailable for installation.
- Live Gemini/xAI and SMTP delivery: NOT RUN because no production credentials were supplied.


## Remediation R1
R1 rebuilt and calibrated all five ML models against the new 500-student CSE dataset. Current risk prevalence and per-section critical limits were validated. Next remediation phase: R2 — Canonical Metrics & Count Semantics.


## Remediation R1 — ML Rebuild & Risk Calibration
- Rebuilt all five risk models against the R0 CSE-only dataset.
- Added 3-fold sigmoid probability calibration to reduce raw Random Forest over-confidence.
- Changed product-facing risk bands to LOW <20%, MODERATE 20–39.9%, HIGH 40–59.9%, CRITICAL >=60%.
- Added Brier score and holdout probability/prevalence metadata to model metrics.
- Added `scripts/test_r1_ml.py` for outcome-rate, calibration, model-quality, and current-population prevalence checks.

## Remediation R1 Validation
- R0 / Phase 1 data validator: PASS.
- R1 ML calibration gate: PASS.
- ML smoke test: PASS.
- Python compilation: PASS.
- Phase 3 regression: PASS.
- Phase 4 regression: PASS.
- Phase 5 regression: PASS.
- Phase 6 regression: PASS.
- Phase 7 regression: PASS.
- Phase 8 regression: PASS.
- Phase 9 regression: PASS.
- Phase 10 regression: PASS.
- Phase 11 regression: PASS (one scope assertion was corrected for the CSE-only institution context, then rerun successfully).
- Phase 12 regression: PASS.
- Phase 14 regression: PASS.
- Phase 15 fast QA: PASS.
- Frontend production build: NOT VERIFIED in the offline runner.
- Live Gemini/xAI and SMTP delivery: NOT RUN without production credentials.
## Remediation R1.5 — Context & Intent Intelligence

Completed. Human-written academic observations are now interpreted into auditable context intents and action pathways using `rule_context_v1`. Authorized student profiles expose contextual evidence, Mentor AI receives the structured context, and canonical alerts can use a matching open observation to select a context-appropriate suggested action. Quantitative ML risk remains authoritative and is not changed by this layer.

Verification: R1.5 context classifier, alert-context routing, profile integration, fast QA, frontend TS/TSX syntax parsing, Phase 4/5/6/8/10/12/14 regressions, ML smoke test, and data validation passed. Phase 11 later rerun exceeded the environment time budget and is not claimed as a new pass.

Next remediation: R2 — Canonical Metrics & Count Semantics.



R2 documentation: `docs/REMEDIATION_R2_CANONICAL_METRICS.md`

## Remediation R2 — Canonical Metrics & Count Semantics

Completed. Centralized dashboard KPI semantics across Mentor, HOD, and Dean. Unique student counts are separated from risk exposure and alert work-item counts. Elevated risk is defined as risk score >= 40 (HIGH/CRITICAL). Risk distribution counts students once per risk type; multiple course-failure rows do not inflate student-level risk signals. Added open-alert student counts, multiple-risk counts, actionable signal counts, and metric semantics metadata to the shared response contract. Updated dashboard copy to explain the distinctions.

Verification: R2 metric semantics, risk distribution, alert-vs-student distinction, cross-metric invariants, R1 data/ML validation, R1.5 integration, Phase 3/4/5/6/7/8/9/10/11/12/14 regressions, Phase 15 fast QA, Python compilation all passed. Frontend TypeScript build remains NOT VERIFIED because the offline runner lacks the Vite type dependency cache.

Next remediation: R3 — Backend Performance & Data Loading.


## Current remediation status
- R0 Data & Domain Reset: COMPLETE
- R1 ML Rebuild & Risk Calibration: COMPLETE
- R1.5 Context & Intent Intelligence: COMPLETE
- R2 Canonical Metrics & Count Semantics: COMPLETE
- R3 Backend Performance & Data Loading: COMPLETE
- R4 Notification Experience: COMPLETE
- R5 Student Academic Profile: COMPLETE
- Next: R6 Cross-Role UX & Responsive Scalability


## Remediation R3 — Backend Performance & Data Loading
- Current-risk prediction snapshots are warmed at application startup so ordinary dashboard/profile reads use the persisted canonical snapshot.
- Ordinary GET paths remain read-oriented; explicit synchronization remains a deliberate operation.
- Student profile reads use persisted current predictions instead of recalculating ML on every visit.
- Mentor dashboard loading uses skeleton state rather than rendering zero-valued KPIs while data is still loading.

## Remediation R4 — Notification Experience
- Notification center was redesigned as an Academic Action Center with action-required, follow-up, escalation, and information categories.
- Notifications expose risk/priority/student context without conflating notification read state with alert resolution.
- Responsive/viewport-aware behavior and outside/Escape dismissal were added.

## Remediation R5 — Student Academic Profile
- Student profile was reorganized as a faculty case-review workspace with clear status, risk evidence, interventions, What-If, AI, and context-history sections.
- Loading, empty/error states, wrapping, and action-context presentation were improved.

## Remediation R6 — Cross-Role UX & Responsive Scalability
- Shared institutional shell, role navigation, notification behavior, tables, cards, filters, loading states, and responsive layout safeguards were hardened across Mentor, HOD, Dean, and Admin.
- No student-facing application route was introduced.

## Remediation R7 — Final Integration QA
- Added `scripts/test_r7_final_qa.py` as a dependency-light final integration gate covering CSE domain structure, sequential roll numbers, mentor/HOD/Dean boundaries, metric-vs-alert semantics, contextual data, loading/responsive safeguards, and frontend secret safety.
- Final standalone regression pass completed for R0/R1/R1.5/R2/R3/R4/R5/R6 and the Phase 3–12/14 endpoint/security suites.
- R7 final integration gate: PASS.
- Fresh extraction and ZIP integrity: PASS.
- Frontend production build remains NOT VERIFIED in this offline runner because the full npm dependency cache is unavailable. Live external AI/SMTP delivery remains NOT RUN without provider credentials.

## Current Remediation Status
- R0 Data & Domain Reset: COMPLETE
- R1 ML Rebuild & Risk Calibration: COMPLETE
- R1.5 Context & Intent Intelligence: COMPLETE
- R2 Canonical Metrics & Count Semantics: COMPLETE
- R3 Backend Performance & Data Loading: COMPLETE
- R4 Notification Experience: COMPLETE
- R5 Student Academic Profile: COMPLETE
- R6 Cross-Role UX & Responsive Scalability: COMPLETE
- R7 Final Integration QA: COMPLETE
- R8 Academic Timeline Integrity: COMPLETE
- R9 Runtime Alert & QA Truth: COMPLETE
- R10 Role Workflow Corrections: COMPLETE
- R11 Canonical Student Status & Profile Consistency: COMPLETE
- R12 What-If + Context Intelligence Refinement: COMPLETE
- R13 Production UX & Scalability Cleanup: COMPLETE
- R14 Security & Privacy Final Gate: COMPLETE
- R15 Deployment Readiness: COMPLETE
- Next: Phase 16 — Deployment


## R8 — Academic Timeline Integrity
The 2024-entry CSE cohort now uses a standard two-semester academic-year mapping: semesters 1-2 in 2024-25, semesters 3-4 in 2025-26, and semester 5 current in 2026-27. Dataset manifest version is `agent14-cse-2026-r8`. See `docs/REMEDIATION_R8_ACADEMIC_TIMELINE.md`.


## Completed in Remediation R11 — Canonical Student Status & Profile Consistency
- Unified student current status around one canonical primary `RiskPrediction` so risk score, priority, risk level, and primary risk describe the same underlying prediction.
- Added `highest_risk_score` separately for analysis without allowing it to overwrite the primary status.
- Added assignment-completion, semester, academic-year, and checkpoint metadata to the student profile metrics.
- Removed the student profile's hardcoded semester label and prevented frontend status logic from recomputing risk bands.
- Surfaced the highest-priority course-failure signal in the main risk evidence section while retaining full course-level detail below.
- Added R11 profile consistency regression coverage.

## R11 Validation
- R11 profile consistency regression: PASS.
- R2 canonical metrics regression: PASS.
- R5 student profile regression: PASS.
- R10 role workflow regression: PASS.
- Phase 11 HOD/Dean AI regression: PASS.
- Phase 15 fast QA: PASS.
- Python compilation: PASS.
- Fresh ZIP extraction/integrity: PASS.
- Frontend production build remains NOT VERIFIED in this offline runner because the npm dependency cache is incomplete.

## U2-U4 UX correction status
U2 Institutional Design System, U3 Mentor Dashboard Workflow, and U4 Student Academic Case Workflow have been implemented together as a cumulative UX correction increment. The remaining notification, What-If, HOD/Dean, and final visual QA work remains pending.

## U5–U7 Faculty UX Increment (current)
- U5: notification action center now uses live academic context, faculty-readable evidence/recommended action, read-all, and portal-based stacking isolation.
- U6: What-If is a guided one-factor scenario with recommended targets and explicit current-vs-simulated comparison; AI remains optional.
- U7: HOD/Dean workflow terminology and mentor section scope are consistent with the faculty-only product model.
- Cumulative U5–U7 verification completed after fixing stale test assumptions and one alert-context date regression.
