# Remediation R15 — Deployment Readiness

## Purpose

This phase is a deployment-readiness gate. It does not deploy the application. It verifies that the cumulative Agent 14 project has explicit production configuration requirements, a supported PostgreSQL driver, frontend API configuration, clean secrets handling, and reproducible startup instructions.

## Production requirements

Backend:

```text
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@<HOST>:5432/postgres
JWT_SECRET=<long random secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=https://<your-vercel-domain>.vercel.app
TRUSTED_HOSTS=<exact backend host(s)>
ENABLE_DOCS=false
AI_PROVIDER=xai
XAI_API_KEY=<your Grok API key>
```

Frontend:

```text
VITE_API_BASE_URL=https://<backend-host>/api
```

The backend supports PostgreSQL through `psycopg[binary]`. SQLite remains suitable for local development/testing only.

## Startup smoke test

Backend:

```powershell
cd backend
python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm ci
npm run build
npm run preview
```

Before a production frontend build, configure `VITE_API_BASE_URL`.

## Readiness checklist

- Production refuses the default JWT secret.
- Production refuses SQLite as the database backend.
- Production requires explicit CORS origins and trusted hosts.
- Production disables API docs by default.
- Frontend production builds require an explicit API base URL.
- `.env` and runtime artifacts are ignored by Git.
- No real API keys or SMTP credentials belong in the repository or ZIP.
- Real Grok and SMTP delivery still require target-environment credentials.
- `XAI_API_KEY` is read as the existing generic `AI_API_KEY` compatibility alias; do not commit either key.
- Full frontend production build must be executed in a Node environment with dependencies installed.

## Deployment sequence for Phase 16

1. Provision PostgreSQL.
2. Configure backend production environment variables.
3. Install backend dependencies.
4. Start FastAPI with a production ASGI process.
5. Run `/api/health` and verify database connectivity.
6. Build frontend with `VITE_API_BASE_URL` pointing to the deployed backend.
7. Serve the frontend over HTTPS.
8. Verify Mentor/HOD/Dean/Admin workflows and role boundaries.
9. Configure external AI/SMTP only when approved credentials and privacy requirements are satisfied.

## Render Docker deployment

The repository includes a `render.yaml` blueprint with two Docker web services:

- `agent14-backend`: FastAPI/Uvicorn, health check `/api/health`
- `agent14-frontend`: Vite build served by Nginx, health check `/health`

Deploy the backend first. In the backend Render service, set:

```text
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@<SUPABASE_HOST>:5432/postgres
JWT_SECRET=<generated-or-long-random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=https://<frontend-service>.onrender.com
TRUSTED_HOSTS=<backend-service>.onrender.com
ENABLE_DOCS=false
AI_PROVIDER=xai
XAI_API_KEY=<rotated-xai-key>
```

After the backend service has a public URL, set the frontend service build
variable to the complete API prefix:

```text
VITE_API_BASE_URL=https://<backend-service>.onrender.com/api
```

The Supabase URL, publishable key, and JWKS URL are not required by this
backend because it authenticates through the application's JWT login flow.
The Supabase secret key must never be placed in the frontend or committed to
the repository. Rotate any credentials that were shared outside the secret
manager before deployment.
