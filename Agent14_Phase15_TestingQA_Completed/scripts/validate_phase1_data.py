from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
ERR: list[str] = []


def req(df, cols, name):
    missing = set(cols) - set(df.columns)
    if missing:
        ERR.append(f"{name} missing {sorted(missing)}")
    if df.empty:
        ERR.append(f"{name} is empty")


def unique(df, cols, name):
    if not df.empty and df.duplicated(cols).any():
        ERR.append(f"{name} has duplicate keys: {cols}")


def load(name):
    p = DATA / name
    if not p.exists():
        ERR.append(f"missing {name}")
        return pd.DataFrame()
    return pd.read_csv(p)


def main():
    st = load("students.csv")
    te = load("teachers.csv")
    assignments = load("assignments.csv")
    sem = load("student_semester_features.csv")
    co = load("student_course_features.csv")
    ho = load("historical_outcomes.csv")
    ref = load("academic_reference_data.csv")
    obs = load("academic_observations.csv")
    alerts = load("alerts_interventions.csv")

    req(st, ["student_id", "roll_number", "student_name", "department", "section", "batch", "current_semester"], "students")
    req(te, ["teacher_id", "teacher_name", "role", "department", "email"], "teachers")
    req(assignments, ["assignment_id", "student_id", "teacher_id", "semester", "assignment_type"], "assignments")
    req(sem, ["student_id", "cohort", "semester", "checkpoint_week", "snapshot_type", "current_gpa", "current_attendance_percentage", "projected_final_attendance"], "semester")
    req(co, ["student_id", "cohort", "semester", "snapshot_type", "course_id", "course_failed"], "course")
    req(ho, ["student_id", "cohort", "semester", "checkpoint_week", "course_failed", "new_backlog", "gpa_below_threshold", "attendance_shortage", "discontinued"], "outcomes")
    req(ref, ["department_id", "semester", "course_id", "attendance_threshold", "gpa_threshold"], "reference")
    req(obs, ["observation_id", "student_id", "observed_on", "category", "observation_text", "source_role", "follow_up_required", "status"], "observations")
    req(alerts, ["student_id", "risk_type", "alert_status"], "alerts")

    if not st.empty:
        unique(st, ["student_id"], "students")
        unique(st, ["roll_number"], "roll numbers")
        if len(st) != 500:
            ERR.append(f"expected 500 students, got {len(st)}")
        if set(st.department) != {"DEPT_CSE"}:
            ERR.append(f"unexpected departments: {sorted(st.department.unique().tolist())}")
        if set(st.section) != {f"CSE-{x}" for x in "ABCDEFGHIJ"}:
            ERR.append("expected CSE-A through CSE-J sections")
        if not st.groupby("section").size().eq(50).all():
            ERR.append("every section must contain exactly 50 students")
        rolls = st.sort_values("student_id")["roll_number"].astype(str).tolist()
        expected_rolls = [f"241FA04{i:03d}" for i in range(1, 501)]
        if rolls != expected_rolls:
            ERR.append("roll numbers are not the required sequential 241FA04xxx series")
        if not st.current_semester.eq(5).all():
            ERR.append("current semester must be 5 for all active demo students")
        if not st.batch.astype(str).eq("2024").all():
            ERR.append("active demo batch must be 2024")

    if not te.empty:
        unique(te, ["teacher_id"], "teachers")
        unique(te, ["email"], "teacher emails")
        if len(te) != 7:
            ERR.append(f"expected 7 academic authority records, got {len(te)}")
        if set(te.role) != {"mentor", "hod", "dean"}:
            ERR.append("unexpected teacher roles")
        if (te.role.eq("mentor").sum(), te.role.eq("hod").sum(), te.role.eq("dean").sum()) != (5, 1, 1):
            ERR.append("expected 5 mentors, 1 CSE HOD, 1 Dean")
        if set(te.loc[te.role.eq("mentor"), "department"]) != {"DEPT_CSE"}:
            ERR.append("all mentors must be CSE mentors")

    if not assignments.empty:
        unique(assignments, ["assignment_id"], "assignments")
        unique(assignments, ["student_id"], "active mentor assignments")
        if len(assignments) != len(st):
            ERR.append("not exactly one active mentor assignment per student")
        mentor_ids = set(te.loc[te.role.eq("mentor"), "teacher_id"])
        if not set(assignments.teacher_id).issubset(mentor_ids):
            ERR.append("non-mentor present in mentor assignments")
        merged = assignments.merge(st[["student_id", "section"]], on="student_id", validate="one_to_one")
        section_per_mentor = merged.groupby("teacher_id")["section"].nunique()
        if not section_per_mentor.eq(2).all():
            ERR.append("each mentor must cover exactly two sections")
        sizes = merged.groupby("teacher_id").size()
        if not sizes.eq(100).all():
            ERR.append("each mentor must have exactly 100 assigned students")

    if not sem.empty:
        unique(sem, ["student_id", "semester", "checkpoint_week"], "semester checkpoints")
        hist = sem[sem.snapshot_type.eq("historical")]
        cur = sem[sem.snapshot_type.eq("current")]
        if len(cur) != len(st):
            ERR.append("current snapshot is not one per student")
        if len(hist) != len(st) * 4:
            ERR.append("expected four historical semester snapshots per student")
        if set(cur.semester) != {5} or set(hist.semester) != {1, 2, 3, 4}:
            ERR.append("semester snapshots must be historical 1-4 and current 5")
        for c, lo, hi in [("current_gpa", 0, 10), ("current_attendance_percentage", 0, 100), ("projected_final_attendance", 0, 100), ("recent_engagement_score", 0, 1)]:
            if c in sem and not sem[c].between(lo, hi).all():
                ERR.append(f"{c} outside range")

    if not co.empty:
        unique(co, ["student_id", "semester", "course_id"], "course snapshots")
        current_course = co[co.snapshot_type.eq("current")]
        historical_course = co[co.snapshot_type.eq("historical")]
        if len(current_course) != len(st) * 5 or len(historical_course) != len(st) * 4 * 5:
            ERR.append("course snapshot counts do not match 5 courses across 5 semesters")
        if not co.loc[co.snapshot_type.eq("current"), "course_failed"].isna().all():
            ERR.append("current course_failed must be null")

    if not ho.empty:
        unique(ho, ["student_id", "semester", "checkpoint_week"], "outcomes")
        if len(ho) != len(st) * 4:
            ERR.append("historical outcomes should contain one outcome per student per historical semester")
        for c in ["course_failed", "new_backlog", "gpa_below_threshold", "attendance_shortage", "discontinued"]:
            rate = float(ho[c].mean())
            lower = 0.002 if c == "discontinued" else 0.005
            if not (lower <= rate <= 0.60):
                ERR.append(f"{c} class rate {rate:.3f} outside expected range")
        h = sem[sem.snapshot_type.eq("historical")].copy().sort_values(["student_id", "semester"])
        o = ho.sort_values(["student_id", "semester"])
        # Prevent simplistic label leakage from a single threshold feature.
        checks = [
            ("gpa", "gpa_below_threshold", "current_gpa"),
            ("attendance", "attendance_shortage", "projected_final_attendance"),
            ("backlog", "new_backlog", "current_backlog_count"),
        ]
        for label, target, feature in checks:
            threshold = 7 if label == "gpa" else 75 if label == "attendance" else 0
            direct = h[feature].lt(threshold).astype(int) if label != "backlog" else h[feature].gt(threshold).astype(int)
            if direct.to_numpy().shape == o[target].to_numpy().shape and np.array_equal(direct.to_numpy(), o[target].to_numpy()):
                ERR.append(f"direct target leakage copy detected for {label}")

    if not obs.empty:
        unique(obs, ["observation_id"], "observations")
        unique(obs, ["observation_id", "student_id"], "observation/student keys")
        if len(obs) < 100:
            ERR.append("expected contextual observations for a meaningful subset of students")
        if not obs.observation_text.astype(str).str.strip().ne("").all():
            ERR.append("observation text cannot be empty")
        if not obs.student_id.isin(st.student_id).all():
            ERR.append("observations reference unknown students")
        expected_categories = {"attendance", "academic_performance", "assessment", "support", "health_related", "improvement"}
        if not set(obs.category).issubset(expected_categories):
            ERR.append("unexpected observation category")

    if not alerts.empty and not alerts.student_id.isin(st.student_id).all():
        ERR.append("alerts reference unknown students")

    if ERR:
        print("PHASE 1 / R0 DATA VALIDATION FAILED")
        print("\n".join("ERROR: " + e for e in ERR))
        return 1

    print("PHASE 1 / R0 DATA VALIDATION PASSED")
    print(
        f"students={len(st)} teachers={len(te)} assignments={len(assignments)} "
        f"semester_snapshots={len(sem)} course_snapshots={len(co)} historical_outcomes={len(ho)} "
        f"reference_rows={len(ref)} observations={len(obs)} alerts={len(alerts)}"
    )
    print(f"sections={sorted(st.section.unique().tolist())}; mentor_load={assignments.merge(st[['student_id','section']], on='student_id').groupby('teacher_id').size().to_dict()}")
    print(ho[["course_failed", "new_backlog", "gpa_below_threshold", "attendance_shortage", "discontinued"]].mean().round(3).to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
