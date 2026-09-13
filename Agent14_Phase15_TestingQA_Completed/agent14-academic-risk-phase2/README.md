# Agent 14 — Student Academic Risk Agent

Early-warning academic risk intelligence platform. See `docs/` for the PRD,
architecture, and the resumable project state checkpoint.

## Quick Start

### Frontend
```
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Backend
```
cd backend
python3 -m venv venv
. venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Demo accounts (any non-empty password):
- mentor1@vignan.ac.in / mentor2@vignan.ac.in
- hod.cse@vignan.ac.in
- dean@vignan.ac.in
- admin@vignan.ac.in


## Current implementation phase

Phase 10 — Mentor AI Copilot is complete. See `docs/PROJECT_STATE_CHECKPOINT.md`.


## Phase 9 — What-If Simulator
Mentor/HOD/Dean can simulate attendance, GPA, backlog, assignment, and course-performance changes without modifying canonical data. See `docs/PHASE_9_WHAT_IF.md`.


## Phase 10 — Mentor AI Copilot
The mentor student profile includes an intent-based AI Copilot for current-risk explanation, intervention planning, and What-If explanation. Configure the provider in `backend/.env`:

```env
AI_PROVIDER=gemini
AI_API_KEY=your_provider_key
AI_MODEL=gemini-3.8-flash
AI_TIMEOUT_SECONDS=25
```

`xai` is also supported with `AI_MODEL=grok-4.6`. The LLM is grounded in canonical `RiskPrediction` and priority-engine outputs; it does not calculate risk. See `docs/PHASE_10_MENTOR_AI.md`.


## Phase 12 — Notifications
Staff notifications are available through `/api/notifications`. In-app delivery is durable and idempotent; SMTP email is optional and configured only on the backend. See `docs/PHASE_12_NOTIFICATIONS.md` and `backend/.env.example`.
