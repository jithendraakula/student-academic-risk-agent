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

Demo accounts (demo password: `demo`):
- mentor.one.cse@vignan.ac.in / mentor.two.cse@vignan.ac.in / mentor.three.cse@vignan.ac.in / mentor.four.cse@vignan.ac.in / mentor.five.cse@vignan.ac.in
- hod.cse@vignan.ac.in
- dean@vignan.ac.in
- admin@vignan.ac.in


## Current implementation phase

Remediation R15 — Deployment Readiness Test is complete; the project is deployment-ready pending real environment/credential verification. Phase 16 — Deployment remains pending. See `docs/PROJECT_STATE_CHECKPOINT.md` and `docs/REMEDIATION_R15_DEPLOYMENT_READINESS.md`.


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

## Remediation R0 — Data & Domain Reset
The active demo is now a CSE-only institutional scenario: 10 sections (CSE-A through CSE-J), 50 students per section, 500 active students, one 2024 batch in semester 5, five mentors with two sections each, one CSE HOD, and one Dean. Student roll numbers run sequentially from `241FA04001` through `241FA04500`.

The data also includes `academic_observations.csv`, which captures human-readable academic context such as attendance/health-related absence, transport issues, missed assessments, subject difficulty, and improvement notes. These observations are contextual evidence and are not ML labels or probability calculators.

For the demo's one-cohort structure, the ML training compatibility boundary is temporal: semesters 1–3 train, semester 4 is held out, and semester 5 is the current prediction snapshot. Deeper ML recalibration is the next remediation phase.


## Remediation R1 — ML Rebuild & Risk Calibration
The five risk models were rebuilt against the R1 CSE dataset and wrapped in 3-fold sigmoid probability calibration. Product severity bands are LOW <20%, MODERATE 20–39.9%, HIGH 40–59.9%, CRITICAL >=60%. The calibrated current population produces a small actionable high/critical pocket rather than an institution-wide crisis. See `docs/REMEDIATION_R1_ML_CALIBRATION.md`.


## Current academic timeline

The demo uses a 2024-entry CSE cohort in semester 5 (academic year 2026-27). Semester 1-2 map to 2024-25, semester 3-4 map to 2025-26, and semester 5 maps to 2026-27. See `scripts/test_r8_data_timeline.py`.
