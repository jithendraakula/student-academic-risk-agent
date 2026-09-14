from app.models.domain import StudentCase, CaseEvent, AlertIntervention

def test_case_models_exist_and_alert_has_case_link():
    assert StudentCase.__tablename__ == "student_cases"
    assert CaseEvent.__tablename__ == "case_events"
    assert "case_id" in AlertIntervention.__table__.c
