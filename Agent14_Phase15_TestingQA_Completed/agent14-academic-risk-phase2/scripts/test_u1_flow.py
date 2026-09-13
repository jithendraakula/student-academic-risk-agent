from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"

checks = []

def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))

workspace = (SRC / "components" / "WorkspaceIntro.tsx").read_text()
shell = (SRC / "components" / "InstitutionalShell.tsx").read_text()
mentor = (SRC / "pages" / "mentor" / "Dashboard.tsx").read_text()
hod = (SRC / "pages" / "hod" / "Dashboard.tsx").read_text()
dean = (SRC / "pages" / "dean" / "Dashboard.tsx").read_text()
app = (SRC / "App.tsx").read_text()

check("role flows declared", all(step in workspace for step in [
    "Review attention queue", "Open student case", "Record support action",
    "Review department status", "Compare mentor load", "Open student case",
    "Review institution", "Identify priority area", "Review authorized case",
    "Review configuration", "Review records", "Apply policy changes",
]))
check("technical workspace hero removed", "ML" not in workspace and "Priority" not in workspace and "Predict" not in workspace)
check("mentor attention summary precedes queue", mentor.index("Today at a glance") < mentor.index('id="mentor-queue"'))
check("mentor technical source text removed", "Source: {workspace?.risk_source" not in mentor)
check("mentor uses canonical support_attention filter", 'value="support_attention"' in mentor and 'value="discontinuation"' not in mentor)
check("HOD workflow order", hod.index("Mentor oversight") < hod.index("Student review") < hod.index("riskOverview.length"))
check("HOD AI follows operational sections", hod.index('<InstitutionalAIPanel role="hod" />') > hod.index("riskOverview.length"))
check("Dean workflow order", dean.index("Institutional priority") < dean.index("Department oversight") < dean.index("Authorized case review") < dean.index("Risk mix"))
check("Dean AI follows operational sections", dean.index('<InstitutionalAIPanel role="dean" />') > dean.index("Risk concentration"))
check("navigation says Student case", ">Student case</span>" in shell)
check("students remain non-users", 'allow={[' in app and 'path="/mentor/student/:studentId"' in app and 'allow={["mentor", "hod", "dean"]}' in app)
check("no student application route", not re.search(r'path="/student(?:/|\\")', app))
check("U1 documentation present", (ROOT / "docs" / "REMEDIATION_U1_INFORMATION_ARCHITECTURE.md").exists())

failed = [item for item in checks if not item[1]]
print("U1 INFORMATION ARCHITECTURE GATE")
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'} - {name}{(': ' + detail) if detail else ''}")
if failed:
    raise SystemExit(f"U1 gate failed: {len(failed)} check(s)")
print(f"U1 GATE PASSED ({len(checks)} checks)")
