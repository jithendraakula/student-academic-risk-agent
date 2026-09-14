# Phase 11 — HOD / Dean AI Analyst

## Goal
Extend the grounded AI architecture from the mentor level to department and institutional decision support.

## Architecture
`Canonical RiskPrediction + Priority Engine -> scoped HOD/Dean metrics -> grounded LLM -> explanation/recommendations`

The LLM is not the source of truth for counts, percentages, risk, priority, rankings, or intervention state.

## HOD analyst
Scope: the HOD's own department.

Supported intents:
- `executive_summary`
- `mentor_workload`
- `intervention_coverage`

Context includes the canonical department summary, risk distribution, and mentor workload comparison.

## Dean analyst
Scope: institution-wide.

Supported intents:
- `executive_summary`
- `risk_analysis`
- `intervention_coverage`
- `priority_review`

The Dean risk analysis includes department comparison and risk heatmap. The priority review uses the canonical priority queue; student names are intentionally omitted from the AI context.

## Guardrails
- Only HOD and Dean roles can access the institutional analyst.
- HOD context is department-scoped.
- Dean context is institution-scoped.
- Support Attention / discontinuation remains support-only.
- No punitive, admission, scholarship, placement, grading, disciplinary, or exclusion recommendations.
- The AI cannot claim that an intervention has already happened.
- No fallback/fabricated AI answer is returned when the provider is unavailable.

## API
`POST /api/institutional-ai/analyze`

Example request:
```json
{"intent":"executive_summary","focus":"attendance recovery"}
```

## Provider
Uses the same `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, and timeout configuration already established in Phase 10.
