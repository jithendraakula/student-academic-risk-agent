# Remediation R4 — Notification Experience

## Goal
Turn the notification system into an understandable academic action center without changing the Phase 12 delivery semantics.

## UX rules
- Notifications are role-scoped and available only to Mentor/HOD/Dean.
- The center distinguishes Action required, Follow-up, Escalation, and Information.
- Risk notifications show the risk label, level, priority, student context, and a concise action message.
- A notification is a work prompt, not a student count.
- Long content is constrained inside a scrollable, viewport-aware panel.
- Action-required items provide a direct review path to the related student case.
- Read state is explicit; marking a notification read does not resolve an alert.
- Mobile and desktop layouts must avoid clipping/overlap.

## Backend contract additions
`GET /api/notifications` now returns optional contextual fields:
- `category`
- `student_id`
- `student_name`
- `risk_type`
- `risk_label`
- `risk_level`
- `priority_score`
- `alert_status`
- `action_required`

Existing `id`, `alert_id`, `kind`, `title`, `message`, `status`, `is_read`, and `created_at` fields remain compatible.

## Verification
- Python compilation
- Notification response contract inspection
- Existing Phase 12 notification regression
- Existing RBAC/security regressions
- Fresh ZIP extraction and integrity
