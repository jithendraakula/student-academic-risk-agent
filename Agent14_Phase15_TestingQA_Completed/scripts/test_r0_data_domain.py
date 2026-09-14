"""Focused Remediation R0 data/domain regression gate."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"


def main():
    st = pd.read_csv(DATA / "students.csv")
    te = pd.read_csv(DATA / "teachers.csv")
    ass = pd.read_csv(DATA / "assignments.csv")
    obs = pd.read_csv(DATA / "academic_observations.csv")

    assert len(st) == 500
    assert set(st["department"]) == {"DEPT_CSE"}
    assert set(st["section"]) == {f"CSE-{x}" for x in "ABCDEFGHIJ"}
    assert st.groupby("section").size().eq(50).all()
    assert st.sort_values("student_id")["roll_number"].tolist() == [f"241FA04{i:03d}" for i in range(1, 501)]

    assert len(te) == 7
    assert te.role.eq("mentor").sum() == 5
    assert te.role.eq("hod").sum() == 1
    assert te.role.eq("dean").sum() == 1
    assert set(te.loc[te.role.eq("mentor"), "department"]) == {"DEPT_CSE"}

    joined = ass.merge(st[["student_id", "section"]], on="student_id", validate="one_to_one")
    assert len(ass) == 500
    assert joined.groupby("teacher_id").size().eq(100).all()
    assert joined.groupby("teacher_id")["section"].nunique().eq(2).all()
    assert joined.student_id.nunique() == 500

    assert len(obs) >= 100
    assert obs.observation_text.astype(str).str.strip().ne("").all()
    assert obs.student_id.isin(st.student_id).all()
    assert "fever" in " ".join(obs.observation_text.astype(str)).lower()

    current = pd.read_csv(DATA / "student_semester_features.csv")
    historical = pd.read_csv(DATA / "historical_outcomes.csv")
    course = pd.read_csv(DATA / "student_course_features.csv")
    assert len(current[current.snapshot_type.eq("current")]) == 500
    assert len(current[current.snapshot_type.eq("historical")]) == 2000
    assert len(historical) == 2000
    assert len(course) == 12500

    print("R0 DATA/DOMAIN TEST PASSED")
    print("CSE students=500 sections=10 mentors=5 observations=", len(obs))


if __name__ == "__main__":
    main()
