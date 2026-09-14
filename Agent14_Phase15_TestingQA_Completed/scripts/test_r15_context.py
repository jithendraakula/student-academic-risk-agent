from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.context_intelligence import classify_observation, summarize_observations


class Observation:
    def __init__(self, oid, cat, text, follow=False, status="OPEN"):
        self.id = oid
        self.observed_on = "2026-09-01"
        self.category = cat
        self.observation_text = text
        self.source_role = "mentor"
        self.follow_up_required = follow
        self.status = status


def main():
    cases = [
        ("health_recovery", "health_related", "Absent for three consecutive days due to fever; mentor requested a check-in after return."),
        ("transport_attendance", "attendance", "Recent first-hour attendance was affected by recurring transport delays; mentor is reviewing a practical attendance plan."),
        ("attendance_pattern", "attendance", "Repeated late arrival to first-hour classes observed over the last two weeks; attendance recovery target discussed."),
        ("assessment_support", "assessment", "Missed one internal assessment and two quiz attempts; subject support is being considered before the next checkpoint."),
        ("family_support", "support", "Student reported a short-term family responsibility affecting attendance and study time; mentor scheduled a follow-up."),
        ("subject_academic_support", "academic_performance", "Student is finding Database Management Systems difficult and has requested additional problem-solving support."),
        ("improvement_maintain", "improvement", "Attendance and assignment completion improved after the previous mentor follow-up."),
    ]
    for expected, category, text in cases:
        result = classify_observation(category, text)
        assert result["intent"] == expected, (expected, result)
        assert result["recommended_action"], expected
        assert result["classifier"] == "context_intent_v2"

    rows = [Observation("1", "health_related", "Absent due to fever.", True), Observation("2", "attendance", "Repeated late arrival to first-hour classes.", True)]
    summary = summarize_observations(rows)
    assert summary["observation_count"] == 2
    assert summary["active_follow_up_count"] == 2
    assert summary["primary_context_intent"] in {"health_recovery", "attendance_pattern"}
    assert summary["primary_action_path"] is not None
    assert summary["method"] == "context_intent_v2"
    print("R1.5 context/intent tests: PASS")


if __name__ == "__main__":
    main()
