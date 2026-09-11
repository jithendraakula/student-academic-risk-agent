"""
Generates Dataset 7: Historical Outcomes.

Produces 2 prior semesters per student with binary outcome labels,
loosely correlated with the current-semester archetype (a student who
is "critical" now likely had rockier history too) so the eventual ML
models have learnable signal rather than pure noise.
"""

import pandas as pd
from config import RNG


ARCHETYPE_BASE_RATE = {
    "critical_multi_risk": {"fail": 0.55, "backlog": 0.5, "gpa": 0.5, "attendance": 0.5, "discontinue": 0.12},
    "attendance_only": {"fail": 0.15, "backlog": 0.1, "gpa": 0.1, "attendance": 0.55, "discontinue": 0.05},
    "discontinuation_watch": {"fail": 0.1, "backlog": 0.05, "gpa": 0.1, "attendance": 0.1, "discontinue": 0.2},
    "normal": {"fail": 0.08, "backlog": 0.05, "gpa": 0.08, "attendance": 0.08, "discontinue": 0.02},
}


def generate_historical_outcomes(semester_df: pd.DataFrame):
    rows = []
    for _, s in semester_df.iterrows():
        rates = ARCHETYPE_BASE_RATE[s["_archetype"]]
        for sem_offset in [1, 2]:  # semesters 4 and 3 (prior to current semester 5)
            rows.append({
                "student_id": s["student_id"],
                "cohort": s["cohort"],
                "academic_year": "2024-25" if sem_offset == 1 else "2023-24",
                "semester": int(s["semester"]) - sem_offset,
                "course_failed": bool(RNG.random() < rates["fail"]),
                "new_backlog": bool(RNG.random() < rates["backlog"]),
                "gpa_below_threshold": bool(RNG.random() < rates["gpa"]),
                "attendance_shortage": bool(RNG.random() < rates["attendance"]),
                "discontinued": False,  # nobody in the active roster has actually discontinued
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    semester_df = pd.read_csv("../processed/student_semester_features.csv")
    df = generate_historical_outcomes(semester_df)
    df.to_csv("../processed/historical_outcomes.csv", index=False)
    print(f"Historical outcome rows: {len(df)}")