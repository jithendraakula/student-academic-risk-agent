# Startup database fix

The backend previously could fail on startup with:

`sqlite3.OperationalError: no such table: student_cases`

Cause: a database could already contain `students` and an `alembic_version` row stamped at the migration head while the case tables had never actually been created. The startup code then called `backfill_student_cases()` before those tables existed.

## Fix

`backend/app/db/session.py` now:

1. Runs migrations for normal upgrade paths.
2. Performs an additive `_ensure_case_schema()` reconciliation before any case backfill.
3. Creates missing `student_cases` and `case_events` tables when necessary.
4. Adds a missing `alerts_interventions.case_id` column and indexes without deleting data.
5. Re-runs `Base.metadata.create_all()` as a safe additive fallback.
6. Only then calls `backfill_student_cases()`.

This supports both fresh databases and older/stamped SQLite databases.

## Recommended local run

From `backend`:

```powershell
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Do not delete an existing database just to fix this startup problem; the reconciliation is designed to preserve the existing data.
