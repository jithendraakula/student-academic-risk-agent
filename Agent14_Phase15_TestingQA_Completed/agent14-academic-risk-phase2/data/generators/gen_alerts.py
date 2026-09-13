"""Generates Dataset 6: Alerts and Interventions."""

import pandas as pd
from datetime import datetime, timedelta
from config import RNG, GPA_THRESHOLD, ATTENDANCE_THRESHOLD
import scoring

ALERT_THRESHOLD = 50  # only students at/above this score for a risk type get an alert
STATUS_CYCLE = ["NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP", "RESOLVED"]
BASE_DATE = datetime(2026, 9, 1)


def generate_alerts(semester_df: pd.DataFrame, assignments_df: pd.DataFrame):
    student_to_mentor = dict(zip(assignments_df["student_id"], assignments_df["teacher_id"]))
    rows = []
    alert_counter = 1

    for _, s in semester_df.iterrows():
        teacher_id = student_to_mentor.get(s["student_id"])
        scores = {
            "attendance": scoring.attendance_shortage_risk(s, ATTENDANCE_THRESHOLD),
            "gpa": scoring.gpa_threshold_risk(s, GPA_THRESHOLD),
            "backlog": scoring.backlog_risk(s),
            "support_attention": scoring.support_attention_risk(s),
        }

        for risk_type, score in scores.items():
            if score < ALERT_THRESHOLD:
                continue

            priority = round(
                score * 0.5
                + (30 if scoring.intervenability_label(risk_type, s) == "High" else 15)
                + RNG.uniform(0, 10),
                1,
            )

            # Archetype-driven lifecycle: critical cases skew toward NEW/ACKNOWLEDGED
            # (still open, demo-relevant); normal-tier alerts skew resolved (shows
            # the intervention loop actually closes cases).
            if s["_archetype"] == "critical_multi_risk":
                status = RNG.choice(STATUS_CYCLE[:3], p=[0.5, 0.3, 0.2])
            else:
                status = RNG.choice(STATUS_CYCLE, p=[0.15, 0.15, 0.2, 0.2, 0.3])

            created_at = BASE_DATE - timedelta(days=int(RNG.integers(0, 10)))
            intervention_date = None
            follow_up_date = None
            action_taken = None
            outcome_status = None
            outcome_notes = None
            risk_after = None

            if status != "NEW":
                intervention_date = created_at + timedelta(days=int(RNG.integers(1, 4)))
                action_taken = scoring.suggested_action(risk_type)
            if status in ("FOLLOW_UP", "RESOLVED"):
                follow_up_date = intervention_date + timedelta(days=int(RNG.integers(3, 10)))
            if status == "RESOLVED":
                outcome_status = RNG.choice(["improved", "no_change"], p=[0.75, 0.25])
                outcome_notes = (
                    "Student showed measurable improvement after intervention."
                    if outcome_status == "improved"
                    else "No significant change observed yet; continuing monitoring."
                )
                risk_after = round(max(0, score - RNG.uniform(10, 35)), 1) if outcome_status == "improved" else score

            rows.append({
                "alert_id": f"ALT{alert_counter:05d}",
                "student_id": s["student_id"],
                "teacher_id": teacher_id,
                "risk_type": risk_type,
                "risk_score": round(score, 1),
                "priority_score": priority,
                "confidence_level": scoring.confidence_label(score),
                "intervenability_score": scoring.intervenability_label(risk_type, s),
                "created_at": created_at.strftime("%Y-%m-%d"),
                "alert_status": status,
                "intervention_id": f"INT{alert_counter:05d}" if status != "NEW" else None,
                "intervention_type": "mentor_check_in" if status != "NEW" else None,
                "suggested_action": scoring.suggested_action(risk_type),
                "action_taken": action_taken,
                "intervention_date": intervention_date.strftime("%Y-%m-%d") if intervention_date else None,
                "follow_up_date": follow_up_date.strftime("%Y-%m-%d") if follow_up_date else None,
                "outcome_status": outcome_status,
                "outcome_notes": outcome_notes,
                "risk_score_after_intervention": risk_after,
            })
            alert_counter += 1

    return pd.DataFrame(rows)


if __name__ == "__main__":
    semester_df = pd.read_csv("../processed/student_semester_features.csv")
    assignments_df = pd.read_csv("../processed/assignments.csv")
    df = generate_alerts(semester_df, assignments_df)
    df.to_csv("../processed/alerts_interventions.csv", index=False)
    print(f"Alert rows: {len(df)}")
    print(df["alert_status"].value_counts())
    print(df["risk_type"].value_counts())