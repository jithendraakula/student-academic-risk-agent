# U5 — Notification & Action Center

The notification experience is a faculty action center. It distinguishes action-required, follow-up, escalation, and informational items; uses live alert context, roll number, section, risk, and priority; and keeps notification read state separate from case/intervention state.

Backend additions:
- `POST /api/notifications/read-all`
- notification summaries expose action/follow-up/escalation counts
- notification items include roll number, section, department, evidence, and recommended action when available
- alert context observation text is carried into the notification projection

UI rules:
- notification center is portaled to the document body so it cannot be trapped by page stacking contexts
- Escape and the explicit close/backdrop controls dismiss it
- unread and category semantics remain separate from alert resolution
