"""Grounded HOD/Dean AI analyst built on canonical institutional metrics.

The analyst summarizes and interprets already-computed facts. It never computes
risk, priority, percentages, rankings, or intervention states itself.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.domain import User
from app.schemas.institutional_ai import InstitutionalAIIntent, InstitutionalAIRequest
from app.services import ai as ai_service
from app.services.dean import department_comparison, institution_summary, priority_queue, risk_heatmap
from app.services.hod import department_summary, mentor_comparison, department_risk_overview
from app.services.risk_engine import RISK_TYPE_ORDER, RISK_TYPES
from app.services.rbac import normalize_role

ANALYST_SYSTEM_PROMPT = """You are Agent 14 Institutional Academic Risk Analyst.

You support HOD and Dean decision-making by explaining structured, authoritative
metrics from the application's canonical academic-risk system. The supplied
numbers, percentages, counts, risk levels, priority values, and rankings are
authoritative. NEVER calculate, invent, modify, infer, or contradict numeric
values. Do not produce new unsupported statistics.

HOD scope means one department only. Dean scope means institution-wide only.
Never claim visibility outside the supplied context. Do not make individual
student admission, scholarship, placement, grading, discipline, or exclusion
decisions. Support Attention / discontinuation is a support-only signal and must
never be used as a punitive ranking. Prefer operational recommendations such as
mentor allocation, follow-up coverage, attendance recovery, academic support,
and review cadence. Recommendations must be grounded in the supplied evidence.
Do not claim that an action has already been taken.

Return ONLY valid JSON with keys:
title (string), executive_summary (string), key_findings (array of short strings),
recommended_actions (array of short strings), cautions (array of short strings).
"""


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _build_hod_context(db: Session, user: User, intent: InstitutionalAIIntent) -> dict:
    summary = department_summary(db, user)
    risk_overview = department_risk_overview(db, user)
    context: dict[str, Any] = {
        "role": "hod",
        "scope": {"department": user.department},
        "summary": _jsonable(summary),
        "risk_overview": _jsonable(risk_overview),
        "canonical_definitions": {
            "risk_types": {key: RISK_TYPES[key] for key in RISK_TYPE_ORDER},
            "alert_policy": {"priority_threshold": 60, "critical_override": True},
            "risk_source": "RiskPrediction + canonical priority engine",
        },
    }
    if intent in {InstitutionalAIIntent.MENTOR_WORKLOAD, InstitutionalAIIntent.INTERVENTION_COVERAGE, InstitutionalAIIntent.EXECUTIVE_SUMMARY}:
        context["mentor_comparison"] = _jsonable(mentor_comparison(db, user))
    return context


def _build_dean_context(db: Session, user: User, intent: InstitutionalAIIntent) -> dict:
    summary = institution_summary(db, user)
    context: dict[str, Any] = {
        "role": "dean",
        "scope": {"institution": "all departments"},
        "summary": _jsonable(summary),
        "canonical_definitions": {
            "risk_types": {key: RISK_TYPES[key] for key in RISK_TYPE_ORDER},
            "alert_policy": {"priority_threshold": 60, "critical_override": True},
            "risk_source": "RiskPrediction + canonical priority engine",
        },
    }
    if intent in {InstitutionalAIIntent.RISK_ANALYSIS, InstitutionalAIIntent.EXECUTIVE_SUMMARY}:
        context["department_comparison"] = _jsonable(department_comparison(db, user))
        context["risk_heatmap"] = _jsonable(risk_heatmap(db, user))
    if intent in {InstitutionalAIIntent.INTERVENTION_COVERAGE, InstitutionalAIIntent.PRIORITY_REVIEW}:
        queue = priority_queue(db, user, limit=20)
        # Keep student-level context minimized: IDs and operational fields are enough
        # for an institution-level support review; names are intentionally omitted.
        queue["items"] = [
            {
                "student_id": row["student_id"],
                "department": row["department"],
                "batch": row["batch"],
                "section": row["section"],
                "primary_risk": row["primary_risk"],
                "risk_score": row["risk_score"],
                "priority_score": row["priority_score"],
                "risk_level": row["risk_level"],
                "critical": row["critical"],
                "risk_types": row["risk_types"],
            }
            for row in queue["items"]
        ]
        context["priority_queue"] = _jsonable(queue)
    return context


def _intent_instruction(role: str, intent: InstitutionalAIIntent) -> str:
    instructions = {
        InstitutionalAIIntent.EXECUTIVE_SUMMARY: "Give a concise executive readout of the current situation and the most important operational next steps.",
        InstitutionalAIIntent.RISK_ANALYSIS: "Identify the strongest concentration patterns across risk types and departments, using only the supplied figures.",
        InstitutionalAIIntent.MENTOR_WORKLOAD: "Assess mentor support workload and identify where additional attention or rebalancing should be considered. Workload is support demand, not teacher performance.",
        InstitutionalAIIntent.INTERVENTION_COVERAGE: "Assess intervention and follow-up coverage, identify gaps, and recommend practical coverage improvements.",
        InstitutionalAIIntent.PRIORITY_REVIEW: "Review the canonical priority queue and explain what institutional support pattern it represents. Do not create a new ranking.",
    }
    role_note = "HOD" if role == "hod" else "Dean"
    return f"You are preparing a {role_note} view. {instructions[intent]}"


def _build_messages(context: dict, payload: InstitutionalAIRequest) -> list[dict[str, str]]:
    focus = f"User focus: {payload.focus.strip()}\n" if payload.focus and payload.focus.strip() else ""
    body = {
        "instruction": _intent_instruction(context["role"], payload.intent),
        "focus": focus.strip() or None,
        "context": context,
    }
    return [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(body, ensure_ascii=False, separators=(",", ":"))},
    ]


def _parse_institutional_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        import re
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned non-JSON institutional analysis") from exc
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="AI provider returned an invalid institutional analysis payload")
    return {
        "title": str(result.get("title", "Institutional academic risk analysis")),
        "executive_summary": str(result.get("executive_summary", "")),
        "key_findings": [str(x) for x in (result.get("key_findings") or [])][:8],
        "recommended_actions": [str(x) for x in (result.get("recommended_actions") or [])][:8],
        "cautions": [str(x) for x in (result.get("cautions") or [])][:8],
    }


def run_institutional_analysis(db: Session, user: User, payload: InstitutionalAIRequest) -> dict:
    role = normalize_role(user.role)
    if role not in {"hod", "dean"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only HOD and Dean users can access the institutional AI analyst")
    if role == "hod" and not user.department:
        raise HTTPException(status_code=400, detail="HOD user must have a department scope")

    context = _build_hod_context(db, user, payload.intent) if role == "hod" else _build_dean_context(db, user, payload.intent)
    content, model = ai_service._call_provider(_build_messages(context, payload))
    parsed = _parse_institutional_json(content)
    return {
        "role": role,
        "scope": user.department if role == "hod" else "institution",
        "intent": payload.intent,
        "provider": ai_service.AI_PROVIDER,
        "model": model,
        "grounded": True,
        "title": parsed.get("title", "Institutional academic risk analysis"),
        "executive_summary": parsed.get("executive_summary", ""),
        "key_findings": parsed.get("key_findings", []),
        "recommended_actions": parsed.get("recommended_actions", []),
        "cautions": parsed.get("cautions", []),
        "source_snapshot": {
            "risk_source": "RiskPrediction + canonical priority engine",
            "risk_types": list(RISK_TYPE_ORDER),
            "scope": context["scope"],
        },
    }
