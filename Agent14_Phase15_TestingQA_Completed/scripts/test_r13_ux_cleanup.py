"""Static/pre-deployment checks for R13 frontend UX and scalability cleanup."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"

required = [
    SRC / "services" / "api.ts",
    SRC / "context" / "AuthContext.tsx",
    SRC / "components" / "InstitutionalShell.tsx",
    SRC / "components" / "Table.tsx",
    SRC / "pages" / "admin" / "Dashboard.tsx",
]
for path in required:
    assert path.exists(), f"Missing required file: {path}"

api = (SRC / "services" / "api.ts").read_text()
assert "timeout: 15000" in api
assert "api.interceptors.response.use" in api
assert "status === 401" in api
assert "session_expired" in api
assert "agent14_token" in api and "agent14_user" in api

ctx = (SRC / "context" / "AuthContext.tsx").read_text()
assert "try {" in ctx and "JSON.parse(raw) as AuthUser" in ctx
assert "sessionStorage.removeItem(\"agent14_user\")" in ctx

admin = (SRC / "pages" / "admin" / "Dashboard.tsx").read_text()
assert "PAGE_SIZE = 50" in admin
assert "Showing {start}–{end} of {totalRows}" in admin
assert "aria-pressed" in admin
assert "Search name, ID, department or role" in admin

css = (SRC / "index.css").read_text()
assert "prefers-reduced-motion" in css
assert "min-width: 320px" in css

# These were confirmed unused and removed in R13.
for stale in [
    SRC / "components" / "PageHeader.tsx",
    SRC / "components" / "RiskGauge.tsx",
    SRC / "components" / "StatusDot.tsx",
    SRC / "components" / "TopHeader.tsx",
]:
    assert not stale.exists(), f"Stale unused component remains: {stale.name}"

for stale_ref in ["assets/hero", "assets/react", "assets/vite", "PageHeader", "RiskGauge", "StatusDot", "TopHeader"]:
    matches = []
    for path in SRC.rglob("*.ts*"):
        if stale_ref in path.read_text(errors="ignore"):
            matches.append(path)
    assert not matches, f"Stale reference {stale_ref!r}: {matches}"

# No secret material should be present in frontend source.
for path in SRC.rglob("*.ts*"):
    text = path.read_text(errors="ignore")
    assert "AIza" not in text, f"Possible Gemini key material in {path}"
    assert "xai-" not in text.lower(), f"Possible xAI key material in {path}"

print("R13 UX cleanup gate: PASS")
print("R13 frontend auth/session, responsive, pagination, cleanup and secret-safety checks passed.")
