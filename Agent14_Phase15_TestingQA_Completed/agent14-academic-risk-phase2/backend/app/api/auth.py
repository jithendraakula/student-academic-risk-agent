"""Authentication endpoints with lockout, JWT issuance, logout, and password change."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import LOGIN_LOCK_MINUTES, LOGIN_MAX_FAILURES
from app.core.dependencies import get_current_user
from app.core.security import BEARER, create_access_token, decode_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.domain import AuthSession, RevokedToken, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, AuthUser
from app.services.audit import record_audit

router = APIRouter()

_LOGIN_FAILURES: dict[str, tuple[int, datetime]] = {}


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _throttle_key(request: Request, email: str) -> str:
    return f"{_client_ip(request) or 'unknown'}:{email.strip().lower()}"


def _is_temporarily_throttled(key: str) -> bool:
    count, first = _LOGIN_FAILURES.get(key, (0, datetime.now(timezone.utc)))
    if datetime.now(timezone.utc) - first > timedelta(minutes=LOGIN_LOCK_MINUTES):
        _LOGIN_FAILURES.pop(key, None)
        return False
    return count >= LOGIN_MAX_FAILURES


def _register_failure(key: str) -> None:
    now = datetime.now(timezone.utc)
    count, first = _LOGIN_FAILURES.get(key, (0, now))
    if now - first > timedelta(minutes=LOGIN_LOCK_MINUTES):
        count, first = 0, now
    _LOGIN_FAILURES[key] = (count + 1, first)


def _clear_failures(key: str) -> None:
    _LOGIN_FAILURES.pop(key, None)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    key = _throttle_key(request, payload.email)
    if _is_temporarily_throttled(key):
        record_audit(db, action="LOGIN_THROTTLED", ip_address=_client_ip(request), details={"email_domain": payload.email.rsplit("@", 1)[-1] if "@" in payload.email else "unknown"})
        db.commit()
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed login attempts. Try again later.")

    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    now = datetime.utcnow()
    if user and user.locked_until and user.locked_until > now:
        _register_failure(key)
        record_audit(db, action="LOGIN_BLOCKED", actor=user, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"), details={"reason": "account_locked"})
        db.commit()
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Account temporarily locked. Try again later.")

    valid = bool(user) and verify_password(payload.password, user.password_hash)
    if not valid:
        _register_failure(key)
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= LOGIN_MAX_FAILURES:
                user.locked_until = now + timedelta(minutes=LOGIN_LOCK_MINUTES)
                user.failed_login_attempts = 0
        record_audit(db, action="LOGIN_FAILED", actor=user, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"), details={"reason": "invalid_credentials"})
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    _clear_failures(key)
    record_audit(db, action="LOGIN_SUCCESS", actor=user, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
    db.commit()
    token = create_access_token(user.id, user.role)
    token_payload = decode_access_token(token)
    db.add(AuthSession(
        jti=str(token_payload["jti"]),
        user_id=user.id,
        issued_at=now,
        expires_at=(datetime.fromtimestamp(float(token_payload["exp"]), tz=timezone.utc).replace(tzinfo=None) if isinstance(token_payload["exp"], (int, float)) else now + timedelta(minutes=LOGIN_LOCK_MINUTES)),
    ))
    db.commit()
    return LoginResponse(
        user=AuthUser(id=user.id, name=user.name, role=user.role, department=user.department),
        token=token,
    )


@router.post("/logout")
def logout(request: Request, credentials=Depends(BEARER), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = decode_access_token(credentials.credentials)
    raw_exp = payload["exp"]
    if isinstance(raw_exp, datetime):
        exp = raw_exp.replace(tzinfo=None)
    elif isinstance(raw_exp, (int, float)):
        exp = datetime.fromtimestamp(float(raw_exp), tz=timezone.utc).replace(tzinfo=None)
    else:
        parsed = str(raw_exp).replace("Z", "+00:00")
        try:
            exp = datetime.fromisoformat(parsed).replace(tzinfo=None)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Invalid token expiry") from exc
    jti = str(payload["jti"])
    session = db.get(AuthSession, jti)
    if session and session.revoked_at is None:
        session.revoked_at = datetime.utcnow()
    if db.get(RevokedToken, jti) is None:
        db.add(RevokedToken(jti=jti, user_id=user.id, expires_at=exp))
    record_audit(db, action="LOGOUT", actor=user, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"))
    db.commit()
    return {"status": "logged_out"}


@router.get("/me", response_model=AuthUser)
def me(user: User = Depends(get_current_user)):
    return AuthUser(id=user.id, name=user.name, role=user.role, department=user.department)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    credentials=Depends(BEARER),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        record_audit(db, action="PASSWORD_CHANGE_FAILED", actor=user, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"), details={"reason": "invalid_current_password"})
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must differ from the current password")
    current_payload = decode_access_token(credentials.credentials)
    current_jti = str(current_payload["jti"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user.password_hash = hash_password(payload.new_password)
    sessions = db.query(AuthSession).filter(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).all()
    for session in sessions:
        session.revoked_at = now
        if session.jti != current_jti and db.get(RevokedToken, session.jti) is None:
            db.add(RevokedToken(jti=session.jti, user_id=user.id, expires_at=session.expires_at))
    if db.get(RevokedToken, current_jti) is None:
        db.add(RevokedToken(jti=current_jti, user_id=user.id, expires_at=now + timedelta(minutes=LOGIN_LOCK_MINUTES)))
    record_audit(db, action="PASSWORD_CHANGED", actor=user, ip_address=_client_ip(request), user_agent=request.headers.get("user-agent"), details={"sessions_revoked": len(sessions)})
    db.commit()
    return {
        "status": "password_changed",
        "sessions_revoked": len(sessions),
        "changed_at": now.isoformat(timespec="seconds"),
        "note": "All active sessions must authenticate again.",
    }
