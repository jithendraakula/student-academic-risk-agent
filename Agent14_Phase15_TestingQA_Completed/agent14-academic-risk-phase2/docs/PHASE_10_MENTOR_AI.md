# Phase 10 — Mentor AI Copilot

## Purpose

The Mentor AI Copilot is an LLM explanation and recommendation layer over the canonical Agent 14 risk system. It does **not** calculate risk probability, severity, or priority.

## Architecture

`Student academic data → ML models → RiskPrediction → canonical Priority Engine → structured AI context → Gemini/Grok → grounded explanation + recommendations`

The backend keeps the provider API key server-side. The frontend calls `/api/mentor/ai/copilot/{student_id}` and never receives the provider key.

## Provider configuration

Backend `.env` values:

```env
AI_PROVIDER=gemini
AI_API_KEY=your_provider_key
AI_MODEL=gemini-3.8-flash
AI_TIMEOUT_SECONDS=25
```

Supported providers in this phase:

- `gemini` — Gemini OpenAI-compatible REST endpoint.
- `xai` — xAI/Grok OpenAI-compatible chat-completions endpoint.

The implementation uses Python's standard-library HTTP client, so the core backend does not require an additional LLM SDK.

## Intent model

This is **not** a free-form student chatbot. The mentor selects an intent:

- `risk_summary` — explain the current risk evidence.
- `intervention_plan` — recommend supportive mentor actions.
- `what_if_explanation` — explain a previously calculated What-If scenario.

An optional short `focus` can guide the explanation, but the structured risk context remains authoritative.

## Grounding rules

The system prompt instructs the model to use only supplied evidence. Risk scores, probabilities, levels, confidence, priority scores, and top factors are passed from the ML/canonical pipeline.

The model is prohibited from inventing risk numbers, diagnoses, contacts, or actions it claims have already happened.

Support Attention / discontinuation risk is explicitly restricted to support purposes and must never be used for admission, scholarship, placement, grading, discipline, or exclusion decisions.

## What-If integration

The What-If engine runs first and stays non-persistent. The AI can then explain the resulting baseline-versus-simulated changes. The simulation result is sent as structured context; the LLM cannot write it back to the database.

## Running

1. Copy `backend/.env.example` to `backend/.env`.
2. Set `AI_PROVIDER`, `AI_API_KEY`, and optionally `AI_MODEL`.
3. Install backend requirements.
4. Start FastAPI.
5. Log in as a mentor and open a student profile.
6. Use the Mentor AI Copilot buttons.

Without a configured provider key, the endpoint returns a clear `503` configuration response rather than silently using a fake/local answer.
