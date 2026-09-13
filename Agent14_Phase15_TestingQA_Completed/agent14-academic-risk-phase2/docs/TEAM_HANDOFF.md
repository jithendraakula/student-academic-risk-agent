# Agent 14 — Team Handoff

## Current status

The project has completed **Remediation R1 — ML Rebuild & Risk Calibration**, after the original 15 implementation phases, and is now ready for Remediation R2. Deployment is intentionally paused until domain/data/UI/performance issues are resolved.

## Product scope

Agent 14 is an institutional academic early-warning and intervention application for verified academic authorities:

- Mentor / Class Teacher
- CSE HOD
- Dean
- System Admin for configuration/security only

Students are **not application users**. They exist as academic records for authorized staff to review.

## Current CSE demo domain

- CSE only
- 10 sections: CSE-A … CSE-J
- 50 students / section
- 500 active students total
- Batch: 2024
- Semester: 5
- Roll numbers: 241FA04001 … 241FA04500
- 5 mentors, exactly 2 sections / mentor
- 1 CSE HOD
- 1 Dean

## Current data contract

- 500 students
- 7 academic authority records in teachers.csv (5 mentors + 1 HOD + 1 Dean)
- 500 active mentor assignments
- 2,500 semester snapshots (4 historical + 1 current per student)
- 12,500 course snapshots (5 courses per semester)
- 2,000 historical outcomes
- 25 academic reference rows
- 123 contextual academic observations
- 72 seed alert/intervention records

## Risk philosophy

Risk, priority, and alert/workload are different concepts. Risk is the ML prediction. Priority combines risk with confidence/actionability/urgency. Alerts and interventions are operational work records.

The data reset intentionally keeps most students stable and introduces a small at-risk population. The R1 has completed model probability calibration, prevalence review, and operational risk-band acceptance.

## Textual context

`academic_observations.csv` provides human-readable mentor context. It is not the ML risk calculator. AI can use these observations as grounded context later.

## Run the data/domain validation

```powershell
python scripts/validate_phase1_data.py
```

## Regenerate canonical demo data

```powershell
cd data\generators
python generate_all.py
```

## R1 model calibration note

Because this remediation reset uses one active cohort, the ML pipeline uses a temporal training split (semesters 1–3 train, semester 4 holdout, semester 5 current prediction). R1 has completed probability calibration and threshold/prevalence review; the next remediation phase is R2 — Canonical Metrics & Count Semantics.


R2 rule: dashboard metrics must distinguish unique students, elevated risk signals, and alert work items. See `docs/REMEDIATION_R2_CANONICAL_METRICS.md`.


## Academic timeline (R8)
The active 2024-entry CSE cohort is in semester 5 for academic year 2026-27. Historical semesters map as 1-2 = 2024-25 and 3-4 = 2025-26.
