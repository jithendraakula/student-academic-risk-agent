"""Static contract gate for Remediation R4 notification UX/backend metadata."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
service = (ROOT / "backend/app/services/notifications.py").read_text(encoding="utf-8")
shell = (ROOT / "frontend/src/components/InstitutionalShell.tsx").read_text(encoding="utf-8")

required_backend = [
    '"category": category',
    '"student_id": alert.student_id',
    '"risk_label": risk_label',
    '"risk_level": level or None',
    '"priority_score": priority',
    '"action_required": action_required',
]
for token in required_backend:
    assert token in service, f"Missing backend notification field: {token}"

required_frontend = [
    "Academic action center",
    "Action required",
    "Follow-up",
    "max-h-[calc(100vh-92px)]",
    "Review case",
    'navigate(`/mentor/student/${item.student_id}`)',
]
for token in required_frontend:
    assert token in shell, f"Missing notification UX contract: {token}"

assert "Notification delivery is additive" in shell
assert 'role !== "admin" ? <NotificationBell /> : null' in shell
print("R4 notification contract gate: PASS")
