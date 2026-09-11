"""
Demo-mode auth for Phase 2 scaffold. Accepts any of the seed demo
accounts below and returns a fake bearer token. Replace with real
password hashing + JWT issuance + DB lookup in Phase 5.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import User
from app.services.auth import create_access_token, verify_password
from app.schemas.auth import LoginRequest, LoginResponse, AuthUser

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(user=AuthUser(id=user.id, name=user.name, role=user.role, department=user.department), token=create_access_token(user))
