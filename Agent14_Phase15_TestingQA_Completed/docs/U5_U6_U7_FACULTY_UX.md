# U5–U7 Faculty UX Increment

## U5 — Notification & Action Center

Notifications are a faculty action center, not a generic feed. Items distinguish action required, follow-up, escalation and information. Notification rows include roll number, section, risk, priority, evidence and recommended action when available. The action center is rendered through a document-body portal to avoid page stacking-context collisions. A read-all action changes notification read state only; it never resolves an alert or intervention.

## U6 — What-If + AI Decision Support

What-If is a guided one-factor simulator. It starts from the current academic value, provides a recommended target, and compares current versus simulated risk and priority. No scenario is persisted. Assignment completion is independent of assessment participation. Course simulations change one selected course factor only. AI is optional and explains an already-calculated simulation rather than calculating risk.

## U7 — HOD / Dean Workflow Consistency

HOD and Dean workspaces use the same faculty-facing semantics as Mentor. HOD mentor rows show actual assigned sections and readable primary risk labels; open case work is presented as work items. Dean labels and case-review language are consistent, and institutional AI remains after operational review sections.

## Verification note

During cumulative regression, two stale static checks were updated because U5 deliberately changed the notification height contract and removed an unnecessary pointerdown implementation detail in favor of a portal/backdrop dismissal pattern. One real regression was caught in alert synchronization when observation dates were treated as date objects even though the model stores them as strings; this was corrected and the runtime alert projection test passed again.
