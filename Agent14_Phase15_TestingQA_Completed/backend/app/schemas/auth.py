from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthUser(BaseModel):
    id: str
    name: str
    role: str
    department: Optional[str] = None


class LoginResponse(BaseModel):
    user: AuthUser
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password_policy(self):
        value = self.new_password
        if not any(c.islower() for c in value):
            raise ValueError("New password must contain a lowercase letter")
        if not any(c.isupper() for c in value):
            raise ValueError("New password must contain an uppercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("New password must contain a digit")
        return self
