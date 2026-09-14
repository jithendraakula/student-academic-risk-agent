from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.api import auth, mentor, hod, dean, admin, predictions
from app.api import interventions, what_if, mentor_ai, institutional_ai, notifications
from app.core.config import ALLOWED_ORIGINS, ENABLE_DOCS, ENVIRONMENT, MAX_REQUEST_BYTES, TRUSTED_HOSTS
from app.db.session import init_db, engine

app = FastAPI(
    title="Agent 14 — Student Academic Risk Agent API",
    version="0.3.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
if ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except (TypeError, ValueError):
            return Response("Invalid Content-Length", status_code=400, headers={"X-Request-ID": request_id})
        if declared_length < 0:
            return Response("Invalid Content-Length", status_code=400, headers={"X-Request-ID": request_id})
        if declared_length > MAX_REQUEST_BYTES:
            return Response("Request body too large", status_code=413, headers={"X-Request-ID": request_id})
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/auth") else response.headers.get("Cache-Control", "private, no-cache")
    response.headers["X-Response-Time-ms"] = str(round((time.perf_counter() - started) * 1000, 2))
    return response


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(mentor.router, prefix="/api/mentor", tags=["mentor"])
app.include_router(hod.router, prefix="/api/hod", tags=["hod"])
app.include_router(dean.router, prefix="/api/dean", tags=["dean"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(interventions.router, prefix="/api/interventions", tags=["interventions"])
app.include_router(what_if.router, prefix="/api/what-if", tags=["what-if"])
app.include_router(mentor_ai.router, prefix="/api/mentor/ai", tags=["mentor-ai"])
app.include_router(institutional_ai.router, prefix="/api/institutional-ai", tags=["institutional-ai"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "service": "agent14-backend", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"status": "degraded", "service": "agent14-backend", "database": "unavailable"}) from exc
