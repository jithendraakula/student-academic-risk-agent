# Agent 14 Synthetic Data

The repository contains deterministic synthetic demo/training data only.

```powershell
cd data/generators
python generate_all.py
cd ../..
python scripts/validate_phase1_data.py
```

The generated data is designed around an early-warning boundary: week-6 checkpoint features predict end-of-semester outcomes.

## Remediation R0 data contract

The active demo is CSE-only: 10 sections (CSE-A…CSE-J), 50 students per section, 500 students total, one 2024 cohort currently in semester 5. Five mentors each own two sections. Roll numbers are sequential from `241FA04001` to `241FA04500`.

`academic_observations.csv` contains human-readable mentor context. These observations are contextual evidence for faculty/AI explanations; they are not direct ML labels.


### Current academic timeline
The canonical demo cohort entered in 2024. Semesters 1-2 belong to 2024-25, semesters 3-4 to 2025-26, and semester 5 is current in 2026-27.
