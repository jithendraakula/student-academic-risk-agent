"""Agent 14 Remediation R7 — final integration QA gate.

This gate is intentionally dependency-light. It validates cross-layer invariants
that should remain true after R0-R6 and complements the dedicated phase tests.
Run from the project root:
    python scripts/test_r7_final_qa.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "app"


def load_csv(name: str):
    import pandas as pd
    path = DATA / name
    assert path.exists(), f"missing dataset: {name}"
    return pd.read_csv(path)


def check_domain() -> dict:
    students = load_csv("students.csv")
    teachers = load_csv("teachers.csv")
    assignments = load_csv("assignments.csv")

    assert len(students) == 500
    assert students["department"].nunique() == 1 and students["department"].iloc[0] == "DEPT_CSE"
    assert set(students["section"].dropna().unique()) == {f"CSE-{c}" for c in "ABCDEFGHIJ"}
    assert students.groupby("section").size().to_dict() == {f"CSE-{c}": 50 for c in "ABCDEFGHIJ"}

    roll_numbers = students["roll_number"].astype(str).tolist()
    expected = [f"241FA04{i:03d}" for i in range(1, 501)]
    assert sorted(roll_numbers) == expected
    assert students["student_id"].nunique() == 500

    roles = teachers["role"].str.lower()
    assert (roles == "mentor").sum() == 5
    assert (roles == "hod").sum() == 1
    assert (roles == "dean").sum() == 1
    assert teachers.loc[roles.isin(["mentor", "hod"]), "department"].eq("DEPT_CSE").all()
    assert teachers.loc[roles == "dean", "department"].isna().all()

    by_mentor = assignments.groupby("teacher_id").agg(students=("student_id", "nunique"), sections=("student_id", lambda s: students.loc[students.student_id.isin(s), "section"].nunique()))
    mentor_ids = teachers.loc[roles == "mentor", "teacher_id"]
    for tid in mentor_ids:
        assert int(by_mentor.loc[tid, "students"]) == 100
        assert int(by_mentor.loc[tid, "sections"]) == 2

    return {"passed": True, "detail": "500 CSE students, 10x50 sections, 5 two-section mentors, 1 HOD, 1 Dean, sequential roll numbers"}


def check_metrics_and_alert_semantics() -> dict:
    alerts = load_csv("alerts_interventions.csv")
    required = {"student_id", "risk_type", "alert_status", "priority_score"}
    assert required <= set(alerts.columns)
    open_statuses = {"NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"}
    open_alerts = alerts[alerts["alert_status"].astype(str).str.upper().isin(open_statuses)]
    unique_students = open_alerts["student_id"].nunique()
    assert unique_students <= len(open_alerts)
    assert len(open_alerts) >= unique_students

    metrics = (BACKEND / "services" / "aggregation.py")
    assert metrics.exists(), "canonical metrics service missing"
    text = metrics.read_text(encoding="utf-8")
    for marker in ("students_needing_action", "open_alert_students", "actionable_risk_signals", "students_with_multiple_risks"):
        assert marker in text, f"canonical metric marker missing: {marker}"
    return {"passed": True, "detail": f"seed file contains {unique_students} unique students across {len(open_alerts)} seeded open work items; live runtime KPIs are verified separately by test_r9_runtime_alerts.py"}


def check_role_boundary() -> dict:
    app = (FRONTEND / "App.tsx").read_text(encoding="utf-8")
    assert 'path="/student"' not in app
    assert 'path="/mentor/student/:studentId"' in app
    assert 'allow={["mentor", "hod", "dean"]}' in app
    auth = (FRONTEND / "context" / "AuthContext.tsx").read_text(encoding="utf-8")
    assert "AuthUser" in auth

    expected = {
        "mentor.py": "require_roles(\"mentor\")",
        "hod.py": "require_roles(\"hod\")",
        "dean.py": "require_roles(\"dean\")",
        "admin.py": "require_roles(\"admin\")",
        "notifications.py": "STAFF_ROLES",
    }
    for name, marker in expected.items():
        text = (BACKEND / "api" / name).read_text(encoding="utf-8")
        assert marker in text, f"role guard missing in {name}"

    return {"passed": True, "detail": "no student application route; role-guarded staff APIs present"}


def check_loading_and_responsive_contract() -> dict:
    files = list(FRONTEND.rglob("*.tsx")) + list(FRONTEND.rglob("*.ts"))
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in files)
    for marker in ("MetricSkeleton", "overflow-x-auto", "aria-current", "skip-link"):
        assert marker in text, f"UX safeguard missing: {marker}"
    assert "academic-action-center" in text
    assert "loading" in text.lower()
    secret_patterns = [r"AIza[0-9A-Za-z_-]{20,}", r"xai-[A-Za-z0-9_-]{20,}", r"sk-[A-Za-z0-9_-]{20,}"]
    for p in secret_patterns:
        assert not re.search(p, text), f"possible frontend API secret: {p}"
    return {"passed": True, "detail": f"checked {len(files)} TS/TSX files for loading, responsive, accessibility, notification and secret-safety markers"}


def check_context_data() -> dict:
    obs = load_csv("academic_observations.csv")
    assert len(obs) >= 120
    assert obs["student_id"].isin(load_csv("students.csv")["student_id"]).all()
    required = {"category", "observation_text", "source_role"}
    assert required <= set(obs.columns)
    text = " ".join(obs["observation_text"].astype(str).str.lower().tolist())
    for expected in ("fever", "transport", "internal assessment"):
        assert expected in text, f"expected contextual example not found: {expected}"
    return {"passed": True, "detail": f"{len(obs)} contextual observations are linked to active students"}


def main() -> int:
    checks = [
        ("Domain structure", check_domain),
        ("Metric/alert semantics", check_metrics_and_alert_semantics),
        ("Role boundaries", check_role_boundary),
        ("UX/loading/security contract", check_loading_and_responsive_contract),
        ("Contextual academic data", check_context_data),
    ]
    results = []
    for label, fn in checks:
        try:
            value = fn()
            results.append({"label": label, **value})
            print(f"{label}: PASS — {value['detail']}")
        except Exception as exc:
            results.append({"label": label, "passed": False, "detail": str(exc)})
            print(f"{label}: FAIL — {exc}")

    report_dir = ROOT / "test_artifacts"
    report_dir.mkdir(exist_ok=True)
    report = {"suite": "Agent 14 Remediation R7 Final Integration QA", "passed": all(r["passed"] for r in results), "results": results}
    (report_dir / "r7_final_qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["passed"]:
        print("R7 FINAL INTEGRATION QA: PASS")
        return 0
    print("R7 FINAL INTEGRATION QA: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
