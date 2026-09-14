# Agent 14 — Remediation R0: Data & Domain Model Reset

## Goal

Replace the previous mixed-department demo dataset with a coherent CSE-only academic scenario and introduce human-readable academic observations without making text the ML risk calculator.

## Canonical demo structure

- Department: Computer Science and Engineering (DEPT_CSE)
- Active cohort: 2024
- Current academic year: 2026-27
- Current semester: 5
- Sections: CSE-A through CSE-J
- Students: 50 per section, 500 total
- Mentors: 5, exactly two sections / 100 students each
- HOD: 1, CSE scoped
- Dean: 1, institution scoped
- Student roll series: `241FA04001` through `241FA04500`

## Academic meaning

The active student population is one coherent CSE cohort. Historical semester snapshots (semesters 1–4) are retained for model training, while semester 5 is the current application snapshot.

Each student has one active mentor assignment. The mentor-to-section mapping is:

| Mentor | Sections |
|---|---|
| T001 | CSE-A, CSE-B |
| T002 | CSE-C, CSE-D |
| T003 | CSE-E, CSE-F |
| T004 | CSE-G, CSE-H |
| T005 | CSE-I, CSE-J |

## Risk prevalence design

The data generator creates mostly stable students with a small at-risk pocket. The latent demo-state target is:

- 336 stable
- 80 watch/emerging
- 60 high
- 24 critical

This is intentionally below the user's practical upper bound of 10 critical students per 50-student section. Two sections contain a slightly larger critical pocket (4 each) to demonstrate that unusual sections can occur without turning the whole college into a crisis dashboard.

These are **data-generation states**, not hard-coded ML outputs. Final risk prevalence must be measured again after the ML recalibration phase.

## Textual academic observations

New dataset: `data/processed/academic_observations.csv`

Observation text captures mentor-readable context such as:

- illness/fever-related absence
- transport-related attendance issues
- missed assessment attempts
- short-term family responsibilities
- repeated late arrival
- subject-specific academic difficulty
- positive improvement after mentor follow-up

Each observation also has a controlled category, source role, follow-up flag, and status so it remains reportable without forcing the actual explanation into a rigid label.

The observations are contextual evidence. They do **not** directly become ML labels or probabilities.

## Model boundary change

Because the active population is one cohort, the model training pipeline now uses a temporal semester split for this demo dataset:

- Train: historical semesters 1–3
- Holdout: historical semester 4
- Predict current: semester 5

This prevents the system from pretending that one active cohort is three different cohorts. A later ML remediation phase will further calibrate these models and review prevalence, discrimination, and thresholds.

## Seed alerts

`alerts_interventions.csv` contains a modest starter set of 72 historical/current work items so the intervention UI has examples. Canonical RiskPrediction/alert synchronization remains the authoritative runtime path after ML recalibration.

## Important safety boundary

Students are records only. The application is for mentors, HOD, Dean, and verified authorities. There is no student-facing application role.

Support Attention / discontinuation-related signals remain support-only and must never be used for admission, scholarship, placement, grading, discipline, or exclusion.
