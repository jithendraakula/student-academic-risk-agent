from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.what_if import WhatIfRequest


class CopilotIntent(str, Enum):
    RISK_SUMMARY = "risk_summary"
    INTERVENTION_PLAN = "intervention_plan"
    WHAT_IF_EXPLANATION = "what_if_explanation"


class CopilotRequest(BaseModel):
    intent: CopilotIntent
    what_if: Optional[WhatIfRequest] = None
    focus: Optional[str] = Field(default=None, max_length=240)


class CopilotResponse(BaseModel):
    student_id: str
    intent: CopilotIntent
    provider: str
    model: str
    grounded: bool
    explanation: str
    recommended_actions: list[str]
    priority_rationale: str
    cautions: list[str]
    source_snapshot: dict
