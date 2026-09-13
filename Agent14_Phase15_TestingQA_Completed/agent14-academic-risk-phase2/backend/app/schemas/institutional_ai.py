from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InstitutionalAIIntent(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    RISK_ANALYSIS = "risk_analysis"
    MENTOR_WORKLOAD = "mentor_workload"
    INTERVENTION_COVERAGE = "intervention_coverage"
    PRIORITY_REVIEW = "priority_review"


class InstitutionalAIRequest(BaseModel):
    intent: InstitutionalAIIntent = InstitutionalAIIntent.EXECUTIVE_SUMMARY
    focus: Optional[str] = Field(default=None, max_length=300)


class InstitutionalAIResponse(BaseModel):
    role: str
    scope: str
    intent: InstitutionalAIIntent
    provider: str
    model: str
    grounded: bool
    title: str
    executive_summary: str
    key_findings: list[str]
    recommended_actions: list[str]
    cautions: list[str]
    source_snapshot: dict
