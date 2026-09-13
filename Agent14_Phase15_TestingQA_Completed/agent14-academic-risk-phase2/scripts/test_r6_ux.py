from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend/src"
REQUIRED = [
    FRONTEND / "components/InstitutionalShell.tsx",
    FRONTEND / "components/Table.tsx",
    FRONTEND / "components/Card.tsx",
    FRONTEND / "components/WorkspaceIntro.tsx",
    FRONTEND / "pages/mentor/Dashboard.tsx",
    FRONTEND / "pages/hod/Dashboard.tsx",
    FRONTEND / "pages/dean/Dashboard.tsx",
    FRONTEND / "pages/admin/Dashboard.tsx",
    FRONTEND / "pages/auth/Login.tsx",
]
for path in REQUIRED:
    assert path.exists(), f"missing {path}"

shell = (FRONTEND / "components/InstitutionalShell.tsx").read_text()
table = (FRONTEND / "components/Table.tsx").read_text()
card = (FRONTEND / "components/Card.tsx").read_text()
workspace = (FRONTEND / "components/WorkspaceIntro.tsx").read_text()
mentor = (FRONTEND / "pages/mentor/Dashboard.tsx").read_text()
admin = (FRONTEND / "pages/admin/Dashboard.tsx").read_text()

assert 'id="main-content"' in shell
assert 'className="skip-link"' in shell
assert 'aria-controls="academic-action-center"' in shell
assert 'Escape' in shell and 'createPortal' in shell and 'z-[90]' in shell
assert 'overflow-x-auto' in shell
assert 'Scrollable data table' in table
assert 'min-w-[760px]' in table
assert 'min-w-0' in card
assert 'min-w-0' in workspace and 'max-w-3xl' in workspace
assert 'label="Open case work"' in mentor and 'loading={loading}' in mentor
assert 'loading ? "—" : students.length' in admin
assert 'lg:grid-cols-[minmax(0,1fr)_210px_170px_auto]' in mentor

# Ensure R6 did not add student-facing application routes.
app = (FRONTEND / "App.tsx").read_text()
assert 'path="/student"' not in app

print("R6 UX/scalability structural checks: PASS")
