"""Reusable FastAPI dependencies with token revocation and active-user checks."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import BEARER, decode_access_token
from app.db.session import get_db
from app.models.domain import AuthSession, RevokedToken, User


def get_current_user(credentials=Depends(BEARER), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    payload = decode_access_token(credentials.credentials)
    jti = str(payload["jti"])
    if db.get(RevokedToken, jti) is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    session = db.get(AuthSession, jti)
    if not session or session.revoked_at is not None or session.expires_at <= __import__("datetime").datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication session is no longer valid")
    user = db.get(User, str(payload["sub"]))
    if not user or not getattr(user, "is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive or unavailable")
    token_role = payload.get("role")
    if token_role and str(token_role).lower() != str(user.role).lower():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token role is no longer valid")
    return user


def require_roles(*roles: str):
    allowed = {str(r).lower() for r in roles}

    def dep(user: User = Depends(get_current_user)) -> User:
        if str(user.role).lower() not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")
        return user

    return dep
