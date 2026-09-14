# Phase 8 — Interventions

## Goal
Turn canonical risk alerts into a traceable mentor-led intervention workflow without changing the risk calculation itself.

## What was added
- `InterventionRecord` stores every intervention status transition as an audit history.
- Status transitions are validated rather than allowing arbitrary edits.
- Action, follow-up, and resolution records require meaningful notes.
- `FOLLOW_UP` requires a future follow-up date.
- Active intervention queue supports status and overdue filtering.
- Role-scoped intervention summary/queue endpoints are available to Mentor, HOD, and Dean.
- Mentor acknowledgement now writes to the same intervention history as other actions.
- HOD/Dean intervention summaries expose resolved and overdue follow-up counts.
- Existing `AlertIntervention` remains the active lifecycle projection of canonical `RiskPrediction` rows.

## Workflow
`NEW → ACKNOWLEDGED → ACTION_TAKEN → FOLLOW_UP → RESOLVED`

A `FOLLOW_UP` item can move to another follow-up/action or resolve. A resolved intervention cannot be silently changed back to an active state; a future reopen policy can be added as a deliberate product decision.

## Guardrails
- Only mentors can mutate intervention records.
- HOD and Dean can review interventions inside their access scope.
- Admin is not granted intervention access through these workflow endpoints.
- Support Attention remains support-only and is not a punitive academic ranking.

## Source of truth
Risk/priority values continue to come from `RiskPrediction`. Intervention records describe what staff did in response; they do not recalculate risk.
