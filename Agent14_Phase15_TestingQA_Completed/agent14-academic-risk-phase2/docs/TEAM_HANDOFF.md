# Agent 14 — Team Handoff

## Project
Student Academic Risk Agent: an early-warning and intervention platform for academic, attendance, backlog, GPA, course-failure, and support-attention risks.

## Current status
Phases 0–14 are complete. The next task is Phase 15 — Testing.

## Local Requirements
- Windows or equivalent development environment
- Python 3.13
- Node.js and npm
- No production API keys are required for the current local demo

## Project Structure
```text
agent14-academic-risk-phase2/
  backend/       FastAPI API, SQLAlchemy models, SQLite database
  frontend/      React + TypeScript + Vite application
  ml/            Training, saved models, metrics, predictor
  data/          Synthetic generators and processed CSV datasets
  docs/          PRD/checkpoints/handoffs
  scripts/       Validation and test helpers
```

## Backend
From the project directory:
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
If no virtual environment exists in your local working copy:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Backend: `http://127.0.0.1:8000`
Swagger: `http://127.0.0.1:8000/docs`
Health: `http://127.0.0.1:8000/api/health`

## Frontend
```powershell
cd frontend
npm install
npm run dev
```
Frontend: `http://localhost:5173`

## Demo Accounts
Password: `demo`

| Role | Email |
|---|---|
| Mentor | mentor1@vignan.ac.in |
| Mentor | mentor2@vignan.ac.in |
| HOD | hod.cse@vignan.ac.in |
| Dean | dean@vignan.ac.in |
| Admin | admin@vignan.ac.in |

## Data / ML
The Phase 1 processed data contains 360 students, 1,800 semester snapshots, 9,000 course snapshots, 1,440 historical outcomes, and current demo alerts. Phase 2 trains all five models with the 2025 cohort held out.

## Backend Architecture
```text
Request
  ↓
FastAPI router
  ↓
Authentication / RBAC
  ↓
Service layer
  ↓
SQLAlchemy models
  ↓
ML predictor / canonical risk records
```

Phase 3 adds `backend/app/core/` for configuration/security/dependencies and `backend/app/services/aggregation.py` for shared current-risk aggregates.

## Access Rules
- Mentors: only assigned students.
- HODs: only students in their department.
- Deans: institution-wide authorized analytics.
- Admins: administration/system scope; support/discontinuation risk is not exposed in their prediction response.
- Discontinuation/support-attention predictions are support-only and must never influence admissions, scholarships, placements, or punishment.

## Testing
```powershell
python scripts/validate_phase1_data.py
python -m ml.smoke_test
```
A Phase 3 API/RBAC test script is documented in `scripts/` and requires the normal backend dependencies.

## Phase 5 Mentor handoff
- `backend/app/services/mentor.py` is the mentor workspace aggregation/filter layer.
- `/api/mentor/summary` exposes canonical mentor counts.
- `/api/mentor/students` returns one row per assigned student with optional filters.
- `/api/mentor/students/{student_id}` is assignment-scoped.
- Mentor interventions continue through `/api/mentor/alerts/{alert_id}/acknowledge` and `/api/interventions/{alert_id}`.
- The mentor dashboard consumes the student-level canonical workspace rather than counting raw alerts.

## Phase 6 HOD handoff
- `backend/app/services/hod.py` is the department/HOD aggregation layer.
- `/api/hod/summary` exposes canonical department headline metrics.
- `/api/hod/risk-overview` exposes affected-student counts by canonical risk type.
- `/api/hod/mentor-comparison` compares mentors using department-scoped student summaries and canonical active alerts.
- `/api/hod/mentors/{mentor_id}/students` is department-scoped and supports search, section, risk-type, and needs-action filters.
- `/api/hod/students` returns department students with canonical risk/priority context.

## Phase 10 Mentor AI handoff
- `backend/app/services/ai.py` is the grounded LLM service.
- Supported provider values: `gemini` and `xai`.
- Backend environment variables: `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, `AI_TIMEOUT_SECONDS`.
- `/api/mentor/ai/copilot/{student_id}` is mentor-only.
- Intents: `risk_summary`, `intervention_plan`, `what_if_explanation`.
- Provider keys are server-side only; never put an LLM key in frontend `.env` or source control.
- The LLM is an explanation/recommendation layer. It must never calculate or overwrite canonical risk/priority.
- What-If explanations use the existing non-persistent simulator first.
- Regression: `python scripts/test_phase10_api.py`.

## Phase 11 HOD / Dean AI handoff
- `backend/app/services/institutional_ai.py` is the grounded institutional AI service.
- `backend/app/api/institutional_ai.py` exposes `POST /api/institutional-ai/analyze`.
- Only HOD and Dean roles can access the endpoint; HOD context is department-scoped and Dean context is institution-scoped.
- HOD intents: `executive_summary`, `mentor_workload`, `intervention_coverage`.
- Dean intents: `executive_summary`, `risk_analysis`, `intervention_coverage`, `priority_review`.
- The LLM receives canonical metrics from `RiskPrediction + canonical priority engine`; it is not allowed to create risk/priority statistics.
- Provider settings reuse `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`, `AI_TIMEOUT_SECONDS` from Phase 10.
- Frontend: `frontend/src/components/InstitutionalAIPanel.tsx` is embedded in both HOD and Dean dashboards.
- Regression: `python scripts/test_phase11_api.py`.

## Phase 14 Security handoff
- Authentication is centralized in `backend/app/core/security.py` and `backend/app/core/dependencies.py`.
- Login creates a server-side `AuthSession`; logout and password change revoke sessions.
- Failed logins are throttled and accounts can be temporarily locked.
- `AuditLog` records security-sensitive actions; Admin can read `/api/admin/audit-logs`.
- Production requires explicit `JWT_SECRET`, `ALLOWED_ORIGINS`, and `TRUSTED_HOSTS`; production JWT lifetime is capped at 60 minutes.
- API request bodies are limited to 2 MiB by default.
- Production docs can be disabled with `ENABLE_DOCS=false`.
- Frontend stores the access token in `sessionStorage`, not `localStorage`; logout calls the backend revocation endpoint.
- Do not add API keys or passwords to frontend source, `.env` committed to Git, or audit payloads.

## Next Phase
Phase 15 — Testing.


## Phase 9 — What-If Simulator
- Endpoint: `POST /api/what-if/student/{student_id}`
- Roles: mentor, HOD, dean
- Scenarios: attendance, GPA, backlog count, assignment completion, selected course performance
- Non-persistent: never writes student records, RiskPrediction, alerts, or intervention history
- Frontend entry: student profile → What-If Simulator
- Regression: `python scripts/test_phase9_api.py`

## Phase 12
Notifications: `/api/notifications` provides in-app inbox/summary/read/sync. SMTP email is optional and configured in `backend/.env.example`.

## Phase 13 UI/UX
The frontend now uses `components/InstitutionalShell.tsx` as the common institutional shell. Branding files live in `frontend/public/branding/`. Phase 13 is frontend-only; continue to preserve backend scope and canonical risk behavior.
