# Professional remediation — Student Academic Risk Management

Implemented the ten audit recommendations in this revision.

1. **Alembic migrations** — `backend/alembic/` contains a real schema migration and startup bootstrapping/stamping path for fresh demo databases.
2. **Live updates** — authenticated Server-Sent Events are exposed at `/api/interventions/events`; dashboards subscribe while retaining a polling fallback.
3. **Stable case lifecycle** — `student_cases` is now the operational case record; risk predictions remain immutable snapshots.
4. **Structured completion metadata** — category, reason, notes, follow-up outcome and completion metadata are stored on the case; `case_events` records lifecycle transitions.
5. **Automated tests** — `backend/tests/` covers case creation, completion persistence and model/API contracts.
6. **Frontend resilience and confirmation** — a global React error boundary plus a structured case-completion dialog protects the workflow from accidental or opaque failures.
7. **Pagination/server filtering** — Mentor and Admin endpoints now paginate and filter server-side; intervention queue pagination is also supported.
8. **Constraints/indexing** — active cases use a unique partial index per student; alerts are linked to stable cases and indexed.
9. **Audit review** — Admin exposes a searchable, paginated audit log workflow.
10. **Metric separation** — model risk KPIs remain separate from operational case-completion KPIs.

## Run

Backend:
```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Frontend:
```powershell
cd frontend
npm install
npm run build
npm run dev
```

For production, set `DATABASE_URL` to PostgreSQL, configure `JWT_SECRET`, `ALLOWED_ORIGINS`, `TRUSTED_HOSTS`, and the notification/AI settings as required by the environment.
