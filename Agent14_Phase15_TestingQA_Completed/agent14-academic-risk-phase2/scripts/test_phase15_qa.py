"""Phase 15 fast QA gate for Agent 14.

Use this command from the project root:
    python scripts/test_phase15_qa.py

For cumulative endpoint regressions, use:
    python scripts/test_phase15_qa.py --full

The default gate is dependency-light and does not require pytest or a frontend
node_modules directory. The full mode runs each existing regression script with
an isolated SQLite file so tests do not contaminate one another.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
SCRIPTS = ROOT / "scripts"
REPORT_DIR = ROOT / "test_artifacts"
REPORT_DIR.mkdir(exist_ok=True)


def run_cmd(label: str, argv: list[str], timeout: int = 90) -> dict:
    started = time.time()
    try:
        proc = subprocess.run(
            argv,
            cwd=ROOT,
            env=os.environ.copy(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return {
            "label": label,
            "passed": proc.returncode == 0,
            "returncode": proc.returncode,
            "duration_s": round(time.time() - started, 2),
            "output": proc.stdout[-5000:],
        }
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return {
            "label": label,
            "passed": False,
            "returncode": None,
            "duration_s": round(time.time() - started, 2),
            "output": output + f"\nTIMEOUT after {timeout}s",
        }


def check_python_sources() -> dict:
    failures = []
    files = list((BACKEND / "app").rglob("*.py")) + list((ROOT / "ml").glob("*.py")) + list(SCRIPTS.glob("*.py"))
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
    return {"label": "Python AST syntax", "passed": not failures, "details": failures or [f"parsed {len(files)} Python files"]}


def check_data_contract() -> dict:
    import pandas as pd
    data = ROOT / "data" / "processed"
    expected = {
        "students.csv": (500, {"student_id", "department", "section", "current_semester"}),
        "teachers.csv": (7, {"teacher_id", "role", "department", "email"}),
        "assignments.csv": (500, {"assignment_id", "student_id", "teacher_id", "semester"}),
        "student_semester_features.csv": (2500, {"student_id", "semester", "checkpoint_week", "snapshot_type", "current_gpa"}),
        "student_course_features.csv": (12500, {"student_id", "semester", "course_id", "snapshot_type"}),
        "historical_outcomes.csv": (2000, {"student_id", "semester", "checkpoint_week", "course_failed", "discontinued"}),
        "academic_reference_data.csv": (25, {"department_id", "semester", "course_id", "attendance_threshold", "gpa_threshold"}),
        "academic_observations.csv": (100, {"observation_id", "student_id", "category", "observation_text", "source_role"}),
        "alerts_interventions.csv": (72, {"student_id", "risk_type", "alert_status"}),
    }
    errors = []
    for name, (rows, cols) in expected.items():
        p = data / name
        if not p.exists():
            errors.append(f"missing {name}")
            continue
        df = pd.read_csv(p)
        missing = cols - set(df.columns)
        if missing:
            errors.append(f"{name} missing columns {sorted(missing)}")
        if name == "academic_observations.csv":
            if len(df) < rows:
                errors.append(f"{name}: expected at least {rows}, got {len(df)}")
        elif len(df) != rows:
            errors.append(f"{name}: expected {rows}, got {len(df)}")
    return {"label": "Processed data contract", "passed": not errors, "details": errors or ["all expected datasets/counts validated"]}


def check_canonical_policy() -> dict:
    sys.path.insert(0, str(BACKEND))
    from app.services.risk_engine import RISK_TYPES, PriorityInputs, calculate_priority, normalize_risk_type, should_create_alert  # type: ignore
    errors = []
    expected_types = ("course_failure", "backlog", "gpa_threshold", "attendance_shortage", "discontinuation")
    if tuple(RISK_TYPES.keys()) != expected_types:
        errors.append("canonical risk ordering/types changed unexpectedly")
    for raw, expected in {
        "attendance": "attendance_shortage",
        "gpa": "gpa_threshold",
        "support_attention": "discontinuation",
        "course": "course_failure",
    }.items():
        if normalize_risk_type(raw) != expected:
            errors.append(f"alias {raw} != {expected}")
    if calculate_priority(PriorityInputs(90, "HIGH", 90, 90)) <= 60:
        errors.append("high-risk/high-actionability scenario did not reach alert threshold")
    if not should_create_alert(40, "CRITICAL", 10):
        errors.append("critical override failed")
    if should_create_alert(20, "LOW", 20):
        errors.append("low priority incorrectly created alert")
    return {"label": "Canonical risk/priority policy", "passed": not errors, "details": errors or ["risk aliases, priority calculation, and alert threshold verified"]}



def check_context_intelligence() -> dict:
    sys.path.insert(0, str(BACKEND))
    from app.services.context_intelligence import INTENTS, classify_observation  # type: ignore
    checks = [
        ("health_related", "Absent for three consecutive days due to fever; mentor requested a check-in after return.", "health_recovery"),
        ("attendance", "Recent first-hour attendance was affected by recurring transport delays; mentor is reviewing a practical attendance plan.", "transport_attendance"),
        ("attendance", "Repeated late arrival to first-hour classes observed over the last two weeks; attendance recovery target discussed.", "attendance_pattern"),
        ("assessment", "Missed one internal assessment and two quiz attempts; subject support is being considered before the next checkpoint.", "assessment_support"),
        ("support", "Student reported a short-term family responsibility affecting attendance and study time; mentor scheduled a follow-up.", "family_support"),
        ("academic_performance", "Student is finding Database Management Systems difficult and has requested additional problem-solving support.", "subject_academic_support"),
        ("improvement", "Attendance and assignment completion improved after the previous mentor follow-up.", "improvement_maintain"),
    ]
    errors = []
    for category, text, expected in checks:
        result = classify_observation(category, text)
        if result["intent"] != expected:
            errors.append(f"{expected}: got {result['intent']}")
        if not result["recommended_action"]:
            errors.append(f"{expected}: missing recommended action")
    if not all(intent.support_only == (intent.key in {"health_recovery", "family_support"}) for intent in INTENTS.values()):
        errors.append("support-only intent metadata inconsistent")
    return {"label": "Context/intent intelligence", "passed": not errors, "details": errors or ["context intents and action pathways verified"]}

def check_frontend_contract() -> dict:
    errors = []
    pkg = FRONTEND / "package.json"
    if not pkg.exists():
        errors.append("frontend/package.json missing")
    else:
        manifest = json.loads(pkg.read_text(encoding="utf-8"))
        deps = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
        for key in ("react", "react-dom", "react-router-dom", "axios", "zustand", "recharts", "vite", "typescript"):
            if key not in deps:
                errors.append(f"frontend dependency missing: {key}")
    for asset in [
        FRONTEND / "public" / "branding" / "vignan-brand.png",
        FRONTEND / "public" / "branding" / "accreditation-badges.png",
    ]:
        if not asset.exists() or asset.stat().st_size < 1000:
            errors.append(f"branding asset missing/too small: {asset.relative_to(ROOT)}")
    source_files = list((FRONTEND / "src").rglob("*.tsx")) + list((FRONTEND / "src").rglob("*.ts"))
    joined = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in source_files)
    for marker in ("mentor", "hod", "dean", "notifications", "what-if", "ai"):
        if marker not in joined.lower():
            errors.append(f"frontend source missing workflow marker: {marker}")
    for pat in (r"AIza[0-9A-Za-z_-]{20,}", r"xai-[A-Za-z0-9_-]{20,}", r"sk-[A-Za-z0-9_-]{20,}"):
        if re.search(pat, joined):
            errors.append(f"possible API secret found in frontend source: {pat}")
    return {"label": "Frontend contract/security", "passed": not errors, "details": errors or [f"checked {len(source_files)} TS/TSX files and branding assets"]}


def clean_test_dbs() -> None:
    for path in BACKEND.glob("phase*_test.db"):
        path.unlink(missing_ok=True)


def full_regressions() -> list[dict]:
    scripts = [(3, 45), (4, 45), (5, 45), (6, 45), (7, 45), (8, 60), (9, 60), (10, 60), (11, 120), (12, 60), (14, 60)]
    results = []
    for phase, timeout in scripts:
        clean_test_dbs()
        script = SCRIPTS / ("test_phase14_security.py" if phase == 14 else f"test_phase{phase}_api.py")
        results.append(run_cmd(f"Phase {phase} regression", [sys.executable, str(script)], timeout=timeout))
    clean_test_dbs()
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="also run cumulative endpoint regression scripts")
    args = parser.parse_args()

    results = [check_python_sources(), check_data_contract(), check_canonical_policy(), check_frontend_contract()]
    results.append(run_cmd("Phase 1 validator", [sys.executable, "scripts/validate_phase1_data.py"], timeout=30))
    results.append(run_cmd("ML smoke test", [sys.executable, "-m", "ml.smoke_test"], timeout=45))
    if args.full:
        results.extend(full_regressions())

    clean_test_dbs()
    summary = {
        "suite": "Agent 14 Phase 15 cumulative QA",
        "mode": "full" if args.full else "fast",
        "passed": all(r["passed"] for r in results),
        "results": results,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    report = REPORT_DIR / "phase15_report.json"
    report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"suite_passed": summary["passed"], "failed": [r["label"] for r in results if not r["passed"]], "report": str(report.relative_to(ROOT))}, indent=2))
    if summary["passed"]:
        print("PHASE 15 FAST QA PASSED" if not args.full else "PHASE 15 FULL QA PASSED")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
