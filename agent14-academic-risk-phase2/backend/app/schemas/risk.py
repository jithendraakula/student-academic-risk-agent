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
