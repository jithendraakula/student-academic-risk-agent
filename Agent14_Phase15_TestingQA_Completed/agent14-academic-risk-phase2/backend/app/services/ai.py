"""Grounded Mentor AI Copilot.

The LLM is an explanation/recommendation layer only. It never computes or
stores risk probabilities. Numeric risk and priority values come from the
canonical ML/RiskPrediction/priority pipeline and are supplied as structured
context to the provider.
"""
from __future__ import annotations

import json
import os
import re
from urllib import error, request
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import AcademicObservation, AlertIntervention, InterventionRecord, Student, User
from app.services.aggregation import student_summary
from app.core.config import AI_INCLUDE_STUDENT_IDENTIFIERS, AI_ALLOWED_EXTERNAL_DATA
from app.services.rbac import can_access_student, can_view_support_attention_risk
from app.services.context_intelligence import summarize_observations
from app.services.risk import build_student_risk_profile
from app.services.risk_engine import RISK_TYPES
from app.services.what_if import simulate_student
from app.schemas.ai import CopilotIntent, CopilotRequest

AI_PROVIDER = os.getenv("AI_PROVIDER", "xai" if os.getenv("XAI_API_KEY") else "gemini").strip().lower()
AI_API_KEY = (os.getenv("AI_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()
AI_MODEL = os.getenv("AI_MODEL", "").strip()
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "25"))

PROVIDER_CONFIG = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model_default": "gemini-3.8-flash",
    },
    "xai": {
        "url": "https://api.x.ai/v1/chat/completions",
        "model_default": "grok-4.6",
    },
}

SYSTEM_PROMPT = """You are Agent 14 Mentor Copilot for an institutional academic early-warning system.

Your job is to explain structured academic risk evidence and recommend supportive,
actionable mentor steps. The supplied risk_score, probability, severity, priority,
and course-level values are authoritative outputs from the application's ML and
priority engines. NEVER calculate, invent, overwrite, or contradict these values.
Do not diagnose students, infer mental-health conditions, or recommend punitive
or high-stakes decisions. Support Attention / discontinuation risk is strictly a
support signal and must never be used for admission, scholarship, placement,
grading, discipline, or exclusion decisions.

Use only the supplied context. State when evidence is insufficient. Prefer a few
specific actions tied to the observed risk drivers. Do not claim to have contacted
students, parents, faculty, or external systems. Return ONLY valid JSON with keys:
explanation (string), recommended_actions (array of short strings),
priority_rationale (string), cautions (array of strings)."""


def _visible_risks(profile: dict, user: User) -> dict:
    risks = dict(profile.get("risks", {}))
    if not can_view_support_attention_risk(user.role):
        risks.pop("discontinuation", None)
    return risks


def _safe_factor_rows(result: dict) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for risk_type, value in result.items():
        if risk_type == "course_failure":
            for item in value or []:
                rows.append({
                    "risk_type": risk_type,
                    "course_id": item.get("course_id"),
                    "course_name": item.get("course_name"),
                    "risk_score": round(float(item.get("risk_score", 0)), 1),
                    "probability": round(float(item.get("risk_probability", 0)), 3),
                    "risk_level": item.get("risk_level"),
                    "priority_score": round(float(item.get("priority_score", 0)), 1),
                    "confidence": item.get("confidence"),
                    "top_factors": (item.get("top_factors") or [])[:4],
                })
        else:
            rows.append({
                "risk_type": risk_type,
                "risk_score": round(float(value.get("risk_score", 0)), 1),
                "probability": round(float(value.get("risk_probability", 0)), 3),
                "risk_level": value.get("risk_level"),
                "priority_score": round(float(value.get("priority_score", 0)), 1),
                "confidence": value.get("confidence"),
                "top_factors": (value.get("top_factors") or [])[:4],
            })
    return rows


def build_context(db: Session, student_id: str, user: User, intent: CopilotIntent, what_if: Any = None) -> dict:
    if not can_access_student(db, user, student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student is outside your access scope")

    profile = build_student_risk_profile(db, student_id, user)
    student = profile["student"]
    summaries = student_summary(db, [student_id], include_support_attention=can_view_support_attention_risk(user.role))
    summary = summaries.get(student_id, {})
    alerts = db.scalars(
        select(AlertIntervention)
        .where(AlertIntervention.student_id == student_id)
        .order_by(AlertIntervention.priority_score.desc())
    ).all()
    interventions = db.scalars(
        select(InterventionRecord)
        .where(InterventionRecord.student_id == student_id)
        .order_by(InterventionRecord.created_at.desc())
    ).all()
    observations = db.scalars(
        select(AcademicObservation)
        .where(AcademicObservation.student_id == student_id)
        .order_by(AcademicObservation.observed_on.desc(), AcademicObservation.id.desc())
    ).all()
    academic_context = summarize_observations(observations)

    if AI_INCLUDE_STUDENT_IDENTIFIERS and not AI_ALLOWED_EXTERNAL_DATA:
        raise HTTPException(status_code=500, detail="External AI student-identifier sharing is not permitted by server policy")

    student_context = {
        "case_reference": f"student-case-{student["student_id"]}",
        "department": student["department"],
        "batch": student["batch"],
        "section": student["section"],
    }
    if AI_INCLUDE_STUDENT_IDENTIFIERS:
        student_context.update({"id": student["student_id"], "name": student["student_name"]})

    context = {
        "student": student_context,
        "metrics": profile.get("student_metrics", {}),
        "thresholds": profile.get("thresholds", {}),
        "canonical_summary": {
            "risk_score": summary.get("risk_score", 0),
            "priority_score": summary.get("priority_score", 0),
            "risk_level": summary.get("risk_level", "LOW"),
            "primary_risk": summary.get("primary_risk"),
            "risk_types": summary.get("risk_types", []),
        },
        "risk_evidence": _safe_factor_rows(_visible_risks(profile, user)),
        "active_alerts": [
            {
                "risk_type": alert.risk_type,
                "risk_score": round(float(alert.risk_score), 1),
                "priority_score": round(float(alert.priority_score), 1),
                "status": alert.status,
                "course_id": (alert.data or {}).get("course_id"),
                "suggested_action": (alert.data or {}).get("suggested_action"),
            }
            for alert in alerts
            if alert.status != "RESOLVED"
        ][:8],
        "recent_intervention_history": [
            {
                "from_status": row.from_status,
                "to_status": row.to_status,
                "follow_up_date": row.follow_up_date,
            }
            for row in interventions[:8]
        ],
        "academic_context": {
            "primary_context_intent": academic_context.get("primary_context_intent"),
            "primary_action_path": academic_context.get("primary_action_path"),
            "active_follow_up_count": academic_context.get("active_follow_up_count", 0),
            "observations": academic_context.get("observations", [])[:8],
            "method": academic_context.get("method"),
        },
    }

    if intent == CopilotIntent.WHAT_IF_EXPLANATION:
        if what_if is None or not what_if.has_change():
            raise HTTPException(status_code=400, detail="what_if values are required for what_if_explanation")
        simulation = simulate_student(db, student_id, user, what_if)
        context["what_if_simulation"] = {
            "persistent": simulation["simulation"]["persistent"],
            "changes": simulation["simulation"]["changes"],
            "baseline_summary": simulation["baseline"]["summary"],
            "simulated_summary": simulation["simulated"]["summary"],
            "risk_changes": simulation["changes"],
            "interpretation": simulation["interpretation"],
        }
    return context


def _prompt_for(intent: CopilotIntent, context: dict, focus: str | None) -> str:
    intent_instruction = {
        CopilotIntent.RISK_SUMMARY: "Summarize the student's current academic risk, explain the strongest evidence, and identify the most important mentor action.",
        CopilotIntent.INTERVENTION_PLAN: "Create a concise, supportive intervention plan ordered by urgency and feasibility. Tie each action to a supplied risk driver.",
        CopilotIntent.WHAT_IF_EXPLANATION: "Explain what changes under the simulated scenario, what improved or worsened, and what the mentor should do next. Emphasize that the scenario is non-persistent.",
    }[intent]
    payload = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    focus_line = f"Mentor focus: {focus.strip()}\n" if focus and focus.strip() else ""
    return f"{intent_instruction}\n{focus_line}Structured context (authoritative):\n{payload}"


def _call_provider(messages: list[dict[str, str]]) -> tuple[str, str]:
    if not AI_API_KEY:
        raise HTTPException(status_code=503, detail="AI provider is not configured. Set AI_API_KEY in the backend environment.")
    config = PROVIDER_CONFIG.get(AI_PROVIDER)
    if not config:
        raise HTTPException(status_code=500, detail=f"Unsupported AI_PROVIDER: {AI_PROVIDER}")
    model = AI_MODEL or config["model_default"]
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }).encode("utf-8")
    req = request.Request(
        config["url"],
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {AI_API_KEY}"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=AI_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {detail}") from exc
    except (error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=504, detail="AI provider did not respond within the configured timeout") from exc

    try:
        data = json.loads(raw)
        text = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an unexpected response") from exc
    return str(text), model


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S).strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned non-JSON copilot output") from exc
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="AI provider returned an invalid copilot payload")
    return {
        "explanation": str(result.get("explanation", "")),
        "recommended_actions": [str(x) for x in (result.get("recommended_actions") or [])][:6],
        "priority_rationale": str(result.get("priority_rationale", "")),
        "cautions": [str(x) for x in (result.get("cautions") or [])][:6],
    }


def run_copilot(db: Session, student_id: str, user: User, payload: CopilotRequest) -> dict:
    context = build_context(db, student_id, user, payload.intent, payload.what_if)
    prompt = _prompt_for(payload.intent, context, payload.focus)
    content, model = _call_provider([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    parsed = _parse_json_text(content)
    return {
        "student_id": student_id,
        "intent": payload.intent,
        "provider": AI_PROVIDER,
        "model": model,
        "grounded": True,
        **parsed,
        "source_snapshot": {
            "risk_source": "RiskPrediction + canonical priority engine",
            "student_identifiers_sent_to_provider": AI_INCLUDE_STUDENT_IDENTIFIERS,
            "risk_types": list(RISK_TYPES),
            "what_if_persistent": False if payload.intent == CopilotIntent.WHAT_IF_EXPLANATION else None,
        },
    }
