from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"
checks = []

def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))

css = (SRC / "index.css").read_text()
ui = (SRC / "components" / "AcademicUI.tsx").read_text()
shell = (SRC / "components" / "InstitutionalShell.tsx").read_text()
mentor = (SRC / "pages" / "mentor" / "Dashboard.tsx").read_text()
profile = (SRC / "pages" / "mentor" / "StudentProfile.tsx").read_text()
mentor_api = (SRC / "features" / "mentor" / "api.ts").read_text()

check("institutional palette tokens defined", all(token in css for token in ["--institution-navy", "--institution-blue", "--institution-blue-soft", "--institution-canvas"]))
check("shared UI primitives exist", all(name in ui for name in ["SectionHeading", "StatusChip", "ActionButton", "MetricCard", "KeyValue"]))
check("shared control sizing exists", "--institution-control-height" in css and ".ui-button" in css and ".ui-control" in css)
check("academic cycle is explicit", "2026–27 · Semester 5" in shell)
check("mentor queue uses canonical row risk level", "scoreToLevel" not in mentor and "riskLevelLabel(row.risk_level)" in mentor)
check("mentor uses roll number", "row.roll_number ?? row.student_id" in mentor)
check("mentor action is gated by needs_action", "row.needs_action && row.primary_alert" in mentor)
check("mentor labels open work as work", 'label="Open case work"' in mentor)
check("mentor loading skeleton avoids fake zeros", "MetricCard" in mentor and "loading={loading}" in mentor)
check("profile uses roll number", "profile.student.roll_number ?? profile.student.student_id" in profile)
check("profile uses backend current status", "profile.current_status.risk_score" in profile and "riskTone" not in profile)
check("profile no duplicated five-card warning grid", 'label="Active observations"' not in profile)
check("profile has actual evidence fallback", "evidenceFor(" in profile and "No factor supplied" not in profile)
check("profile distinguishes probability and score", "Risk\"" in profile and "Probability" in profile)
check("profile has active work wording", "Active support actions" in profile)
check("profile gives explicit follow-up state", 'item.follow_up_date || "Not scheduled"' in profile)
check("profile separates course review", "Course failure risk by subject" in profile)
check("profile AI unavailable state is explicit", "The numerical estimate above is independent of the AI provider" in profile)
check("roll number supported by API type", "roll_number?: string | null" in mentor_api)
check("student model has roll number", "roll_number" in (ROOT / "backend" / "app" / "models" / "domain.py").read_text())
check("seed backfills roll numbers", "_ensure_student_roll_number_column" in (ROOT / "backend" / "app" / "db" / "session.py").read_text())

failed=[row for row in checks if not row[1]]
print("U2-U4 DESIGN / MENTOR / STUDENT CASE GATE")
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'} - {name}{(': '+detail) if detail else ''}")
if failed:
    raise SystemExit(f"U2-U4 gate failed: {len(failed)} check(s)")
print(f"U2-U4 GATE PASSED ({len(checks)} checks)")
