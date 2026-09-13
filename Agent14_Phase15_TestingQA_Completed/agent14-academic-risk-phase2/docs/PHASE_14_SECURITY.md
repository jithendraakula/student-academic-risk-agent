# Phase 14 — Security

## Goal
Harden the Agent 14 institutional application while preserving role-scoped visibility and the support-only treatment of discontinuation/support-attention risk.

## Implemented
- Centralized JWT claims with `sub`, `iat`, `exp`, `jti`, and `typ=access`.
- Server-side authentication session registry (`auth_sessions`) with persisted logout/session revocation.
- Persisted revoked-token tombstones (`revoked_tokens`) for explicit token invalidation.
- Active-user and token-role validation on every authenticated request.
- Password hashing remains server-side with PBKDF2-SHA256; plaintext password fallback was removed.
- Login failure accounting, per-IP/email throttling, and temporary account lockout.
- Password-change endpoint with minimum length and mixed-character policy.
- Audit log table (`audit_logs`) for security-relevant events without storing passwords or API secrets.
- Admin audit-log endpoint.
- Security response headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, CSP, request ID, and no-store for auth responses.
- Configurable CORS origins and production trusted hosts.
- Production guardrails: explicit JWT secret, explicit origins/hosts, shorter JWT lifetime, and optional disabling of interactive API docs.
- Request body size limit (default 2 MiB).
- Frontend logout now attempts server-side token revocation before clearing `sessionStorage`.
- LLM and SMTP credentials remain backend-only environment settings.

## Access-control rules preserved
- Mentor: assigned students only.
- HOD: department students only.
- Dean: institution-level authorized analytics.
- Admin: system/administrative scope, without Support Attention/Discontinuation risk output.
- Support Attention/Discontinuation is support-only and must not be used for admission, scholarship, placement, grading, discipline, or exclusion decisions.

## Authentication behavior
Seed/demo accounts continue to use the demo password in development. On a real deployment, set a strong password and configure `JWT_SECRET` before exposing the backend.

Changing a password revokes active sessions for that user and requires re-authentication.

## Verification limits
The offline environment does not contain the production `python-jose` and `passlib` packages, so API security regression tests use a test-only stub for those libraries. The actual project requirements still pin the production dependencies. No production credentials, SMTP server, or live AI provider were contacted during validation.
