from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    id: str
    name: str
    role: str
    department: Optional[str] = None


class LoginResponse(BaseModel):
    user: AuthUser
    token: str
