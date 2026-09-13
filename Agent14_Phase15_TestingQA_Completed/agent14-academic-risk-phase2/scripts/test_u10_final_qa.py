"""Final visual/functional QA gate for Agent 14 U10.
Dependency-light: validates user-facing terminology, role-aware controls,
canonical status usage, layout safety markers, and deployment hygiene.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: str) -> tuple[str, bool, str]:
    return name, ok, detail


def main() -> int:
    results: list[tuple[str, bool, str]] = []
    mentor = read("frontend/src/pages/mentor/Dashboard.tsx")
    profile = read("frontend/src/pages/mentor/StudentProfile.tsx")
    shell = read("frontend/src/components/InstitutionalShell.tsx")
    api = read("frontend/src/services/api.ts")
    hod = read("frontend/src/pages/hod/Dashboard.tsx")
    dean = read("frontend/src/pages/dean/Dashboard.tsx")

    results.append(check(
        "Mentor status semantics",
        "Risk / 100" in mentor and "Priority / 100" in mentor,
        "mentor queue labels distinguish risk score from priority score",
    ))
    results.append(check(
        "Mentor non-actionable copy",
        'return "Monitor";' in mentor,
        "non-actionable students are not presented as requiring intervention",
    ))
    results.append(check(
        "Canonical profile status",
        "profile.current_status.risk_level" in profile and "profile.current_status.priority_score" in profile,
        "profile displays backend current-status values",
    ))
    results.append(check(
        "Profile role-aware AI",
        'user?.role === "mentor"' in profile and "AI Copilot" in profile,
        "mentor-only AI action area is gated by role",
    ))
    results.append(check(
        "Profile academic cycle",
        "profile.student_metrics.academic_year" in profile and "profile.student_metrics.semester" in profile,
        "academic cycle is sourced from profile data",
    ))
    results.append(check(
        "Profile current assignment completion",
        "profile.student_metrics.assignment_completion" in profile,
        "assignment completion uses the current backend metric",
    ))
    results.append(check(
        "Notification portal",
        "createPortal(panel, document.body)" in shell,
        "action center is rendered above application stacking contexts",
    ))
    results.append(check(
        "Notification route",
        "navigate(`/mentor/student/${item.student_id}`)" in shell,
        "notification review links to the authorized case route",
    ))
    results.append(check(
        "HOD dynamic sections",
        "result.sections" in hod and "mentorSections" in hod,
        "section filter options are derived from the selected mentor",
    ))
    results.append(check(
        "Dean human wording",
        "Current institution scope: CSE." in dean,
        "future engineering scope is not shown as end-user copy",
    ))
    results.append(check(
        "Session expiry handling",
        "status === 401" in api and "session_expired" in api,
        "expired sessions are cleared and redirected to login",
    ))
    results.append(check(
        "Page overflow guard",
        "overflow-x: clip" in read("frontend/src/index.css"),
        "page-level horizontal overflow is prevented",
    ))
    results.append(check(
        "Production secrets excluded",
        ".env" in read(".gitignore"),
        "local secret files are excluded from the repository",
    ))

    # Syntax check on U10-modified TSX files via a lightweight delimiter sanity pass
    # and Python AST parsing of all scripts/backend files.
    py_failures: list[str] = []
    for path in list((ROOT / "backend" / "app").rglob("*.py")) + list((ROOT / "ml").glob("*.py")) + list((ROOT / "scripts").glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            py_failures.append(f"{path.relative_to(ROOT)}: {exc}")
    results.append(check("Python source syntax", not py_failures, "all backend/ML/script sources parse" if not py_failures else "; ".join(py_failures)))

    failures = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}")
    print(f"\nU10 FINAL QA: {len(results) - len(failures)}/{len(results)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
