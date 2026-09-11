# Agent 14 - Team Handoff

## Project

Student Academic Risk Agent: an early-warning and intervention platform for academic, attendance, backlog, GPA, course-failure, and support-attention risks.

Current status: Phases 0-11 complete. Phase 12 testing and deployment work remains.

## Local Requirements

- Windows or equivalent development environment
- Python 3.13 recommended
- Node.js and npm
- No API keys required for local development
- No external database required for local development

## Project Structure

```text
agent14-academic-risk-phase2/
  backend/       FastAPI API, SQLAlchemy models, SQLite database
  frontend/      React + TypeScript + Vite application
  ml/            Training, saved models, metrics, predictor
  data/          Synthetic source generators and processed CSV datasets
  docs/          Project documentation and checkpoints
```

## Setup

From the project directory:

```powershell
cd agent14-academic-risk-phase2
```

### Backend

The backend virtual environment already contains the compatible ML dependencies.

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## Demo Accounts

All demo accounts use the password:

```text
demo
```

| Role   | Email                |
| ------ | -------------------- |
| Mentor | mentor1@vignan.ac.in |
| Mentor | mentor2@vignan.ac.in |
| HOD    | hod.cse@vignan.ac.in |
| Dean   | dean@vignan.ac.in    |
| Admin  | admin@vignan.ac.in   |

The backend stores hashed demo passwords in the local database.

## Role Workspaces

```text
Mentor: http://127.0.0.1:5173/mentor
HOD:    http://127.0.0.1:5173/hod
Dean:   http://127.0.0.1:5173/dean
Admin:  http://127.0.0.1:5173/admin
```

## ML Training

Train and run ML artifacts with the backend virtual environment. Training and inference must use the same environment because joblib stores scikit-learn preprocessing objects.

```powershell
cd agent14-academic-risk-phase2
backend\venv\Scripts\python.exe -m ml.train_all
backend\venv\Scripts\python.exe -m ml.smoke_test
```

Saved models are in `ml/models/` and metrics are in `ml/metrics/`.

## Current Data and Database

The local database is:

```text
backend\agent14.db
```

It is SQLite and is seeded from `data/processed/` during backend startup.

Current demo data:

```text
60 students
9 teachers
60 assignments
300 course features
60 semester features
120 historical outcomes
26 alerts
5 users
```

Current Admin configuration:

```text
GPA threshold: 7.5
Attendance threshold: 80%
```

Do not commit real passwords, JWT secrets, API keys, or production database URLs.

## Main API Routes

```text
POST /api/auth/login
GET  /api/health

GET  /api/mentor/watchlist
GET  /api/mentor/alerts
POST /api/mentor/alerts/{alert_id}/acknowledge

GET  /api/hod/mentor-comparison
GET  /api/hod/mentors/{mentor_id}/students
GET  /api/hod/students

GET  /api/dean/department-comparison
GET  /api/dean/risk-heatmap
GET  /api/dean/departments/{department}/students

GET  /api/admin/students
GET  /api/admin/teachers
GET  /api/admin/config
PUT  /api/admin/config

GET   /api/predictions/student/{student_id}
PATCH /api/interventions/{alert_id}
```

## Access Rules

- Mentors can access only assigned students and their own alerts/interventions.
- HODs can access only students and mentors in their department.
- Deans can access institution-wide analytics and authorized student drill-downs.
- Admins can access records and system configuration.
- Support-attention/discontinuation risk is hidden from Admin responses and is support-only.
- Support-attention risk must never be used for admissions, scholarships, placements, or punishment.

## Validation Already Completed

- Frontend production build passed.
- Backend compilation and route registration passed.
- ML model reload and smoke test passed.
- Database row-count and processed-data integrity checks passed.
- Mentor, HOD, Dean, and Admin role-isolation API tests passed.
- Browser workflows passed for all role dashboards.
- Mobile mentor viewport check passed without horizontal overflow.
- Admin threshold changes persisted and appeared in student risk profiles.

## Phase 12 Work Remaining

1. Add formal automated test files for API role isolation and workflows.
2. Add production PostgreSQL configuration and migrations.
3. Add deployment configuration for backend and frontend.
4. Configure production CORS and environment variables.
5. Replace demo credentials and JWT secret.
6. Deploy frontend and backend.
7. Run final hosted smoke tests.

## Deployment Requirements Later

External services are not needed yet. They become necessary during deployment:

```text
Frontend hosting: Vercel, Netlify, or Cloudflare Pages
Backend hosting: Render, Railway, or equivalent
Database: Neon, Supabase PostgreSQL, or equivalent
```

Required deployment environment variables will be similar to:

```text
DATABASE_URL=<production PostgreSQL connection string>
JWT_SECRET=<long random production secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
VITE_API_BASE_URL=<deployed backend API URL>/api
```

Obtain `DATABASE_URL` from the selected PostgreSQL provider. Generate `JWT_SECRET` locally or in the hosting provider's secret manager. Set `VITE_API_BASE_URL` to the public backend URL after the backend is deployed.

Never place production values in source files or commit them to Git.
