from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "frontend" / "src"
CSS = (FRONT / "index.css").read_text(encoding="utf-8")

checks = []
def check(name, ok):
    checks.append((name, bool(ok)))

check("global overflow is clipped without removing inner table scroll", "body { overflow-x: clip; }" in CSS and ".ui-table-shell .overflow-x-auto" in CSS)
check("shared action group exists", ".ui-action-group" in CSS and ".ui-button svg" in CSS)
check("section headings collapse safely on mobile", "@media (max-width: 767px)" in CSS and ".ui-section-heading { display: grid" in CSS)
check("intermediate filter grid is defined", ".u8-filter-grid" in CSS and "max-width: 1279px" in CSS)
check("card content is bounded", "u8-no-overflow" in (FRONT / "components" / "Card.tsx").read_text(encoding="utf-8"))
check("shared table wrapper is used", "ui-table-shell" in (FRONT / "components" / "Table.tsx").read_text(encoding="utf-8"))
check("header has bounded regions", all(k in (FRONT / "components" / "InstitutionalShell.tsx").read_text(encoding="utf-8") for k in ["institutional-header-inner", "institutional-header-brand", "institutional-header-title", "institutional-header-tools"]))
check("mentor filters use responsive class", "u8-filter-grid" in (FRONT / "pages" / "mentor" / "Dashboard.tsx").read_text(encoding="utf-8"))
check("admin controls use responsive class", "u8-filter-grid" in (FRONT / "pages" / "admin" / "Dashboard.tsx").read_text(encoding="utf-8"))
check("student course table has shared scroll shell", "ui-table-shell" in (FRONT / "pages" / "mentor" / "StudentProfile.tsx").read_text(encoding="utf-8"))
check("Vignan palette remains intact", "--institution-navy: #18345f" in CSS and "--institution-blue: #2767bf" in CSS)
check("reduced motion is preserved", "prefers-reduced-motion: reduce" in CSS)

failed = [name for name, ok in checks if not ok]
print(f"U8 responsive UX gate: {len(checks)-len(failed)}/{len(checks)} passed")
for name, ok in checks:
    print(("PASS" if ok else "FAIL") + " - " + name)
if failed:
    raise SystemExit(1)
