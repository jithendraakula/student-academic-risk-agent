"""Context/intent intelligence for human-written academic observations.

The quantitative ML system remains the source of risk. This layer interprets
faculty-written observations into an auditable workflow context so the same
student metrics can lead to different *support pathways* when circumstances
are different.

R12 upgrades this to context-aware v2:
- cue groups are evaluated semantically enough to avoid common negation traps;
- category is used as a secondary signal, not as the sole classifier;
- active/follow-up and recent observations are prioritized over old history;
- uncertainty is surfaced instead of inventing a precise intent.

No LLM call is required to route a case. The LLM may later explain the already
structured context.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any, Iterable


@dataclass(frozen=True)
class ContextIntent:
    key: str
    label: str
    area: str
    urgency: str
    action_type: str
    recommended_action: str
    support_only: bool = False


INTENTS: dict[str, ContextIntent] = {
    "health_recovery": ContextIntent("health_recovery", "Health-related recovery", "attendance", "medium", "support", "Check in after the student returns, review the attendance impact, and agree on a short recovery plan.", True),
    "transport_attendance": ContextIntent("transport_attendance", "Transport-related attendance", "attendance", "medium", "planning", "Review practical arrival options and agree on an achievable attendance recovery target."),
    "attendance_pattern": ContextIntent("attendance_pattern", "Repeated attendance pattern", "attendance", "medium", "accountability", "Review the attendance pattern with the student and set a specific recovery target with a follow-up date."),
    "assessment_support": ContextIntent("assessment_support", "Missed assessment / catch-up support", "assessment", "high", "academic_support", "Review missed assessment opportunities and coordinate an appropriate catch-up or subject-support path."),
    "family_support": ContextIntent("family_support", "Temporary family responsibility", "support", "medium", "support", "Acknowledge the temporary constraint, agree on a realistic academic recovery plan, and schedule a follow-up.", True),
    "subject_academic_support": ContextIntent("subject_academic_support", "Subject-specific academic difficulty", "academic_performance", "medium", "academic_support", "Connect the student with focused subject/problem-solving support and review progress at the next checkpoint."),
    "improvement_maintain": ContextIntent("improvement_maintain", "Positive improvement after support", "improvement", "low", "reinforcement", "Maintain the current support plan, acknowledge the improvement, and continue light monitoring."),
    "general_support": ContextIntent("general_support", "General academic support context", "support", "low", "review", "Review the observation with the student and record the specific support need before choosing an intervention."),
}

# Ordered strongest-to-weakest cue families. Each intent gets a score from
# matched cues, category agreement, and conservative penalties for conflicts.
CUE_GROUPS: dict[str, tuple[str, ...]] = {
    "health_recovery": ("fever", "illness", "unwell", "medical", "doctor", "hospital", "treatment", "health issue", "sick"),
    "transport_attendance": ("transport", "bus delay", "travel delay", "first-hour attendance", "late due to transport", "commute"),
    "attendance_pattern": ("late arrival", "repeated late", "unexcused absence", "repeated absence", "attendance pattern", "frequently absent", "habitual absence"),
    "assessment_support": ("missed internal assessment", "missed assessment", "missed quiz", "missed midterm", "missed exam", "quiz attempt", "assessment attempt", "catch-up assessment"),
    "family_support": ("family responsibility", "family emergency", "caregiving", "family situation", "personal responsibility", "family care"),
    "subject_academic_support": ("finding .* difficult", "struggling with", "difficulty in", "requested additional", "problem-solving support", "subject support", "needs help with", "extra practice"),
    "improvement_maintain": ("improved", "improvement", "better after", "recovered", "made progress", "attendance increased", "assignment completion improved"),
}

CATEGORY_HINTS: dict[str, set[str]] = {
    "health_related": {"health_recovery"},
    "attendance": {"transport_attendance", "attendance_pattern", "health_recovery"},
    "assessment": {"assessment_support"},
    "academic_performance": {"assessment_support", "subject_academic_support"},
    "academic": {"assessment_support", "subject_academic_support"},
    "support": {"family_support", "general_support"},
    "family_related": {"family_support"},
    "improvement": {"improvement_maintain"},
}

_NEGATION_WORDS = {"no", "not", "never", "without", "denies", "denied", "none"}
_NEGATED_PATTERNS = (
    r"\bdoes\s+not\s+have\b",
    r"\bdid\s+not\s+have\b",
    r"\bhas\s+not\s+had\b",
    r"\bno\s+longer\b",
    r"\bnot\s+due\s+to\b",
    r"\bwithout\b",
    r"\bno\s+(?:recent\s+)?(?:missed|attendance|fever|illness)\b",
)


def _term_present(text: str, term: str) -> bool:
    """Match a cue and reject simple negation immediately before the cue."""
    pattern = re.compile(term, flags=re.IGNORECASE)
    for match in pattern.finditer(text):
        prefix = text[max(0, match.start() - 60):match.start()].lower()
        # Explicit negation phrases are stronger than the cue itself.
        if any(re.search(p, prefix) for p in _NEGATED_PATTERNS):
            continue
        suffix = text[match.end():match.end() + 36].lower()
        if re.search(r"\b(?:not\s+present|absent|ruled\s+out|negative)\b", suffix):
            continue
        words = re.findall(r"\b[\w'-]+\b", prefix)[-4:]
        if any(word in _NEGATION_WORDS for word in words):
            continue
        return True
    return False


def _date_value(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _recency_score(observed_on: Any) -> float:
    observed = _date_value(observed_on)
    if not observed:
        return 0.25
    age = max(0, (date.today() - observed).days)
    # Smooth decay across ~90 days; recent observations still dominate.
    return max(0.05, 1.0 / (1.0 + age / 30.0))


def classify_observation(category: str | None, text: str | None) -> dict[str, Any]:
    raw = (text or "").strip()
    normalized = re.sub(r"\s+", " ", raw.lower())
    cat = (category or "").strip().lower()

    scores: dict[str, float] = {key: 0.0 for key in INTENTS if key != "general_support"}
    evidence: dict[str, list[str]] = {key: [] for key in scores}

    for intent_key, terms in CUE_GROUPS.items():
        for term in terms:
            if _term_present(normalized, term):
                scores[intent_key] += 1.0
                evidence[intent_key].append(f"cue:{term}")

    explicit_negation = bool(re.search(r"\b(?:no|not|never|without|does not|did not|has not|denies|denied)\b", normalized))
    for intent_key in scores:
        if intent_key in CATEGORY_HINTS.get(cat, set()):
            # Do not let a category label override a clearly negated statement.
            # For example, "health_related" + "does not have fever" should not
            # become a health-recovery intent merely because the category exists.
            if not (explicit_negation and not evidence[intent_key]):
                scores[intent_key] += 0.75
                evidence[intent_key].append(f"category:{cat}")

    # Avoid treating generic "missed" wording as assessment support unless the
    # surrounding category/phrasing actually indicates assessment context.
    if "missed" in normalized and cat not in {"assessment", "academic_performance", "academic"}:
        scores["assessment_support"] = min(scores["assessment_support"], 1.0)

    # Explicit improvement language wins only when it is not negated.
    if _term_present(normalized, r"not improved"):
        scores["improvement_maintain"] = 0.0

    best_key, best_score = max(scores.items(), key=lambda item: (item[1], item[0]))
    second_score = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.0

    if best_score <= 0:
        intent = INTENTS["general_support"]
        confidence = 0.55
        basis = ["no supported specific context pattern"]
    else:
        intent = INTENTS[best_key]
        # Confidence rises with evidence but is reduced when two intents are
        # close, preventing false certainty in ambiguous observations.
        confidence = min(0.98, 0.60 + 0.10 * min(best_score, 3.0))
        if best_score - second_score < 0.75:
            confidence -= 0.08
        confidence = round(max(0.55, confidence), 2)
        basis = evidence[best_key] or ["category agreement"]

    return {
        "intent": intent.key,
        "intent_label": intent.label,
        "impact_area": intent.area,
        "urgency": intent.urgency,
        "action_type": intent.action_type,
        "recommended_action": intent.recommended_action,
        "support_only": intent.support_only,
        "confidence": confidence,
        "classifier": "context_intent_v2",
        "evidence_basis": basis,
        "ambiguity": bool(best_score > 0 and (best_score - second_score) < 0.75),
    }


def _row_priority(row: dict[str, Any]) -> tuple[int, int, float, float]:
    active = 0 if row["status"] == "CLOSED" else 1
    follow_up = 1 if row["follow_up_required"] else 0
    return (active, follow_up, _recency_score(row["observed_on"]), float(row["confidence"]))


def summarize_observations(observations: Iterable[Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    intent_counts: dict[str, int] = {}

    for observation in observations:
        context = classify_observation(getattr(observation, "category", None), getattr(observation, "observation_text", None))
        row = {
            "observation_id": getattr(observation, "id", None),
            "observed_on": getattr(observation, "observed_on", None),
            "category": getattr(observation, "category", None),
            "observation_text": getattr(observation, "observation_text", None),
            "source_role": getattr(observation, "source_role", None),
            "follow_up_required": bool(getattr(observation, "follow_up_required", False)),
            "status": getattr(observation, "status", None) or "OPEN",
            **context,
        }
        row["recency_score"] = round(_recency_score(row["observed_on"]), 3)
        rows.append(row)
        intent_counts[context["intent"]] = intent_counts.get(context["intent"], 0) + 1

    rows.sort(key=_row_priority, reverse=True)
    ordered_intents = sorted(intent_counts.items(), key=lambda item: (-item[1], item[0]))

    primary_row = rows[0] if rows else None
    primary = primary_row["intent"] if primary_row else None
    primary_action = None
    if primary_row:
        primary_action = {
            "intent": primary_row["intent"],
            "intent_label": primary_row["intent_label"],
            "recommended_action": primary_row["recommended_action"],
            "count": intent_counts.get(primary_row["intent"], 1),
        }

    return {
        "observation_count": len(rows),
        "active_follow_up_count": sum(1 for row in rows if row["follow_up_required"] and row["status"] != "CLOSED"),
        "active_observation_count": sum(1 for row in rows if row["status"] != "CLOSED"),
        "intent_distribution": [{"intent": key, "count": count} for key, count in ordered_intents],
        "primary_context_intent": primary,
        "primary_action_path": primary_action,
        "observations": rows[:12],
        "method": "context_intent_v2",
    }
