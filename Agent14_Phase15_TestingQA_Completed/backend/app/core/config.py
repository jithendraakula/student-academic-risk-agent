"""Central application configuration for Agent 14."""
from __future__ import annotations
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'agent14.db'}")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
JWT_SECRET = os.getenv("JWT_SECRET", "changeme-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()]
TRUSTED_HOSTS = [x.strip() for x in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", str(2 * 1024 * 1024)))
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false" if ENVIRONMENT == "production" else "true").lower() == "true"
if ENVIRONMENT == "production":
    if JWT_SECRET == "changeme-in-production":
        raise RuntimeError("JWT_SECRET must be configured in production")
    if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+psycopg://")):
        raise RuntimeError("DATABASE_URL must use PostgreSQL with psycopg in production")
    if not ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
        raise RuntimeError("Explicit ALLOWED_ORIGINS are required in production")
    if not TRUSTED_HOSTS or "*" in TRUSTED_HOSTS:
        raise RuntimeError("Explicit TRUSTED_HOSTS are required in production")
    if JWT_EXPIRE_MINUTES > 60:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be <= 60 in production")

# Phase 12 — notification delivery configuration.
NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
NOTIFICATION_EMAIL_ENABLED = os.getenv("NOTIFICATION_EMAIL_ENABLED", "false").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME or "no-reply@vignan.ac.in")
NOTIFICATION_HOD_PRIORITY_THRESHOLD = float(os.getenv("NOTIFICATION_HOD_PRIORITY_THRESHOLD", "80"))
NOTIFICATION_DEAN_PRIORITY_THRESHOLD = float(os.getenv("NOTIFICATION_DEAN_PRIORITY_THRESHOLD", "90"))

# Phase 14 — external AI privacy boundary. Third-party LLM calls are de-identified
# by default; production must explicitly opt in before student identifiers are sent.
AI_INCLUDE_STUDENT_IDENTIFIERS = os.getenv("AI_INCLUDE_STUDENT_IDENTIFIERS", "false").lower() == "true"
AI_ALLOWED_EXTERNAL_DATA = os.getenv("AI_ALLOWED_EXTERNAL_DATA", "false").lower() == "true"
if ENVIRONMENT == "production" and AI_INCLUDE_STUDENT_IDENTIFIERS and not AI_ALLOWED_EXTERNAL_DATA:
    raise RuntimeError("AI_INCLUDE_STUDENT_IDENTIFIERS requires explicit AI_ALLOWED_EXTERNAL_DATA=true in production")
