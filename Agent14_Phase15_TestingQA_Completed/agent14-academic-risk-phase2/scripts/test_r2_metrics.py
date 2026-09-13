"""R2 canonical metric semantics and cross-role count consistency tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.domain import AlertIntervention, Base, RiskPrediction, Student, Teacher
import app.services.aggregation as aggregation


def make_prediction(student_id: str, risk_type: str, score: float, level: str, priority: float, course_id: str | None = None) -> RiskPrediction:
    return RiskPrediction(
        student_id=student_id,
        risk_type=risk_type,
        course_id=course_id,
        semester=5,
        checkpoint_week=6,
        risk_probability=score / 100,
        risk_score=score,
        risk_level=level,
        confidence="HIGH",
        decision_threshold=0.2,
        intervenability_score=80,
        priority_score=priority,
        top_factors=[],
        model_version="r2-test",
    )


def main() -> int:
    db_path = Path(tempfile.gettempdir()) / "agent14_r2_metrics.db"
    db_path.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    # R2 tests the aggregation contract, not prediction generation. Prevent the
    # test fixture from invoking real ML inference.
    original_ensure = aggregation.ensure_current_predictions
    original_alerts = aggregation.get_active_alerts
    aggregation.ensure_current_predictions = lambda db, student_ids=None: None

    try:
        with Session() as db:
            teacher = Teacher(id="T-R2", name="R2 Mentor", role="mentor", department="DEPT_CSE", email="r2@example.com")
            students = [
                Student(id=f"S-R2-{i}", name=f"Student {i}", department="DEPT_CSE", program="B.Tech CSE", batch="2024", section="CSE-A", academic_year="2026-27", current_semester=5)
                for i in range(1, 5)
            ]
            db.add(teacher)
            db.add_all(students)
            db.add_all([
                # Student 1: one HIGH attendance risk + two course failures.
                make_prediction("S-R2-1", "attendance_shortage", 45, "HIGH", 72),
                make_prediction("S-R2-1", "course_failure", 61, "CRITICAL", 85, "CSE501"),
                make_prediction("S-R2-1", "course_failure", 55, "HIGH", 75, "CSE502"),
                # Student 2: one CRITICAL risk plus one MODERATE risk (only the
                # elevated risk must count toward R2 exposure).
                make_prediction("S-R2-2", "gpa_threshold", 65, "CRITICAL", 90),
                make_prediction("S-R2-2", "backlog", 28, "MODERATE", 40),
                # Student 3: all LOW; must not appear in risk exposure.
                make_prediction("S-R2-3", "attendance_shortage", 12, "LOW", 18),
                make_prediction("S-R2-3", "gpa_threshold", 10, "LOW", 16),
                # Student 4: elevated support-attention risk.
                make_prediction("S-R2-4", "discontinuation", 44, "HIGH", 64),
            ])
            db.commit()

            alerts = [
                AlertIntervention(id="AL-R2-1", student_id="S-R2-1", teacher_id="T-R2", risk_type="course_failure", risk_score=61, priority_score=85, status="NEW", data={"course_id": "CSE501"}),
                AlertIntervention(id="AL-R2-2", student_id="S-R2-1", teacher_id="T-R2", risk_type="attendance_shortage", risk_score=45, priority_score=72, status="ACTION_TAKEN", data={}),
                AlertIntervention(id="AL-R2-3", student_id="S-R2-2", teacher_id="T-R2", risk_type="gpa_threshold", risk_score=65, priority_score=90, status="NEW", data={}),
            ]
            db.add_all(alerts)
            db.commit()

            def fixed_alerts(db, student_ids, user=None):
                ids = set(student_ids)
                return [a for a in alerts if a.student_id in ids]

            aggregation.get_active_alerts = fixed_alerts

            summaries = aggregation.student_summary(db, [s.id for s in students], include_support_attention=True)
            assert summaries["S-R2-1"]["risk_types"] == ["attendance_shortage", "course_failure"]
            assert summaries["S-R2-1"]["risk_signal_count"] == 2, "multiple course failures must still be one course_failure signal"
            assert summaries["S-R2-1"]["multiple_risks"] is True
            assert summaries["S-R2-3"]["risk_types"] == [], "LOW predictions must not be labelled as affected risk"
            assert summaries["S-R2-4"]["risk_types"] == ["discontinuation"]

            metrics = aggregation.scope_metrics(db, [s.id for s in students], include_support_attention=True)
            assert metrics["monitored_students"] == 4
            assert metrics["elevated_risk_students"] == 3
            assert metrics["high_risk_students"] == 3
            assert metrics["critical_students"] == 2
            assert metrics["high_only_students"] == 1
            assert metrics["students_needing_action"] == 3
            assert metrics["students_with_multiple_risks"] == 1
            assert metrics["risk_signals"] == 4
            assert metrics["actionable_risk_signals"] == 4
            assert metrics["open_alerts"] == 3
            assert metrics["open_alert_students"] == 2
            assert metrics["open_alerts"] > metrics["open_alert_students"], "alerts are work items, not unique students"

            dist = {row["risk_type"]: row for row in metrics["risk_distribution"]}
            assert dist["course_failure"]["affected_students"] == 1
            assert dist["course_failure"]["actionable_students"] == 1
            assert dist["attendance_shortage"]["affected_students"] == 1
            assert dist["gpa_threshold"]["affected_students"] == 1
            assert dist["backlog"]["affected_students"] == 0
            assert dist["discontinuation"]["affected_students"] == 1
            assert sum(row["affected_students"] for row in metrics["risk_distribution"]) == metrics["risk_signals"]
            assert metrics["critical_students"] <= metrics["high_risk_students"] <= metrics["monitored_students"]
            assert metrics["students_needing_action"] <= metrics["monitored_students"]

            print("R2 student summary semantics: PASS")
            print("R2 scope metrics: PASS")
            print("R2 risk distribution: PASS")
            print("R2 alert-vs-student distinction: PASS")
            print("R2 canonical metric regression: PASS")
            return 0
    finally:
        aggregation.ensure_current_predictions = original_ensure
        aggregation.get_active_alerts = original_alerts
        db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
