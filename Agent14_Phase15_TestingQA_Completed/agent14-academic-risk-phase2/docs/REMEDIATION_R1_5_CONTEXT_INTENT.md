# Remediation R1.5 — Context & Intent Intelligence

## Goal

Make faculty observations operationally meaningful without allowing free text or an LLM to invent quantitative risk.

## Design

`AcademicObservation.text + category -> context intent -> action pathway`

The classifier is deterministic and auditable (`rule_context_v1`). It uses grouped semantic cues and the observation category, then emits a structured intent that can drive workflow guidance and grounded AI context. The ML risk score remains authoritative and is not changed by this layer.

## Supported intents

- `health_recovery` — temporary health-related attendance context; supportive return/recovery path
- `transport_attendance` — practical transport/arrival constraint; attendance planning path
- `attendance_pattern` — repeated attendance pattern; target + follow-up path
- `assessment_support` — missed assessment attempts; catch-up/subject support path
- `family_support` — temporary family/personal responsibility; supportive recovery path
- `subject_academic_support` — subject-specific difficulty/support request; focused academic support
- `improvement_maintain` — evidence of positive change; maintain/reinforce support
- `general_support` — insufficient evidence for a specific context; human review before intervention choice

## Workflow use

The derived context is now exposed in the authorized student profile and supplied to the Mentor AI as structured context. Canonical alerts also use a relevant open observation to select a more context-appropriate suggested action when the observation meaning matches the risk type.

Examples:

- fever-related absence + attendance risk -> supportive return/recovery plan
- transport delay + attendance risk -> practical arrival/attendance planning
- missed assessment + course failure/GPA/backlog risk -> catch-up or focused academic support
- family responsibility + attendance/support risk -> supportive academic recovery + follow-up

## Safety boundary

This layer does not diagnose health conditions, change risk probabilities, or make punitive decisions. Support-oriented intents are support-only. The LLM may explain these structured signals but cannot replace the ML/risk engine.
