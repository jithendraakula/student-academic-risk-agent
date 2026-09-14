from typing import Any, Optional

from pydantic import BaseModel, Field


class InterventionUpdate(BaseModel):
    status: str = Field(pattern="^(ACKNOWLEDGED|ACTION_TAKEN|FOLLOW_UP|RESOLVED)$")
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None


class RiskProfileResponse(BaseModel):
    student: dict[str, Any]
    student_id: str
    risks: dict[str, Any]


class CaseCompletionRequest(BaseModel):
    action_category: str = Field(default="GENERAL_SUPPORT", min_length=1, max_length=64)
    completion_reason: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None, max_length=2000)
    follow_up_outcome: Optional[str] = Field(default=None, max_length=128)
