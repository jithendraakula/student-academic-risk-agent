# Remediation R14 — Security & Privacy Final Gate

## Goal
Harden deployment-facing security and put an explicit privacy boundary around external AI calls.

## Changes
- Production API docs default to disabled unless `ENABLE_DOCS=true` is deliberately set.
- Added a root `.gitignore` protecting `.env`, runtime databases, Python/Node artifacts, and local logs.
- Added `backend/.env.example` as the safe configuration template.
- External AI calls are de-identified by default (`AI_INCLUDE_STUDENT_IDENTIFIERS=false`).
- Production requires explicit `AI_ALLOWED_EXTERNAL_DATA=true` before identifiable student data can be sent to an external AI provider.
- AI responses report whether identifiers were sent to the provider.
- Malformed/negative `Content-Length` values now return `400` instead of causing an exception.
- Existing JWT/session revocation, RBAC, audit logging, security headers, CORS, request-size controls, and support-only restrictions remain in force.

## Privacy behavior
Default external AI context includes a non-identifying case reference plus department/batch/section. Student name and roll number are omitted unless explicitly enabled by server configuration.

The numerical risk engine is unaffected.

## Deployment rule
Never commit real API keys, SMTP passwords, JWT secrets, database credentials, or `.env` files. Configure them in the deployment environment/secret manager.
