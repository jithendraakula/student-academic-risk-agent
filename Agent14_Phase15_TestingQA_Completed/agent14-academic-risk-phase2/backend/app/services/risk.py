from __future__ import annotations
import sys
from pathlib import Path
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.domain import CourseFeature, RiskPrediction, SemesterFeature, Student, SystemSetting, User
from app.services.rbac import can_access_student, can_view_support_attention_risk
from app.services.risk_engine import PriorityInputs, calculate_priority, intervenability_score, urgency_score


def _scalar(value):
    if value in (None, "", "None"): return None
    if isinstance(value, str):
        if value in ("True", "False"): return value == "True"
        try:
            number=float(value); return int(number) if number.is_integer() else number
        except ValueError: return value
    return value


def _features(data: dict) -> dict: return {key: _scalar(value) for key, value in data.items()}


def get_student_or_404(db: Session, student_id: str) -> Student:
    student=db.get(Student,student_id)
    if not student: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def _upsert_prediction(db: Session, student_id: str, semester: int, checkpoint_week: int, risk_type: str, course_id: str|None, prediction: dict, student_data: dict):
    iv=intervenability_score(risk_type, student_data)
    urg=urgency_score(risk_type, student_data)
    priority=calculate_priority(PriorityInputs(float(prediction["risk_score"]), str(prediction["confidence"]), iv, urg))
    record=db.scalar(select(RiskPrediction).where(
        RiskPrediction.student_id==student_id,
        RiskPrediction.risk_type==risk_type,
        RiskPrediction.course_id==course_id,
        RiskPrediction.semester==semester,
        RiskPrediction.checkpoint_week==checkpoint_week,
    ))
    if record is None:
        record=RiskPrediction(student_id=student_id,risk_type=risk_type,course_id=course_id,semester=semester,checkpoint_week=checkpoint_week)
        db.add(record)
    record.risk_probability=float(prediction["risk_probability"])
    record.risk_score=float(prediction["risk_score"])
    record.risk_level=str(prediction["risk_level"])
    record.confidence=str(prediction["confidence"])
    record.decision_threshold=float(prediction.get("decision_threshold",0.5))
    record.intervenability_score=float(iv)
    record.priority_score=float(priority)
    record.top_factors=prediction.get("top_factors",[])
    record.model_version=str(prediction.get("model_version","unknown"))


def _predict(student_data: dict, course_data: list[dict]) -> dict:
    project_root=Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path: sys.path.insert(0,str(project_root))
    try:
        from ml.predictor import predict_all_risks
        return predict_all_risks(student_data, course_data)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Risk prediction service unavailable: {exc}") from exc


def refresh_student_predictions(db: Session, student_id: str, *, allowed_user: User|None=None) -> dict:
    student=get_student_or_404(db,student_id)
    if allowed_user is not None and not can_access_student(db,allowed_user,student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student is outside your access scope")
    semester=db.scalars(select(SemesterFeature).where(SemesterFeature.student_id==student_id).order_by(SemesterFeature.id.desc())).first()
    if not semester: raise HTTPException(status_code=404,detail="Semester features not found")
    courses=db.scalars(select(CourseFeature).where(CourseFeature.student_id==student_id,CourseFeature.semester==semester.semester)).all()
    student_data={"student_id":student.id,**_features(semester.data)}
    course_data=[_features(c.data) for c in courses]
    result=_predict(student_data,course_data)
    checkpoint=int(student_data.get("checkpoint_week",6) or 6)
    for prediction in result["risks"].get("course_failure",[]):
        iv = intervenability_score("course_failure", {**student_data, **prediction})
        urg = urgency_score("course_failure", {**student_data, **prediction})
        prediction["intervenability_score"] = iv
        prediction["priority_score"] = calculate_priority(PriorityInputs(float(prediction["risk_score"]), str(prediction["confidence"]), iv, urg))
        _upsert_prediction(db,student.id,int(semester.semester),checkpoint,"course_failure",prediction.get("course_id"),prediction,student_data)
    for key in ("backlog","gpa_threshold","attendance_shortage","discontinuation"):
        if key not in result["risks"]: continue
        prediction = result["risks"][key]
        iv = intervenability_score(key, student_data)
        urg = urgency_score(key, student_data)
        prediction["intervenability_score"] = iv
        prediction["priority_score"] = calculate_priority(PriorityInputs(float(prediction["risk_score"]), str(prediction["confidence"]), iv, urg))
        _upsert_prediction(db,student.id,int(semester.semester),checkpoint,key,None,prediction,student_data)
    db.commit()
    if allowed_user is not None and not can_view_support_attention_risk(allowed_user.role):
        result["risks"].pop("discontinuation",None)
    return {"student":{"student_id":student.id,"student_name":student.name,"department":student.department,"batch":student.batch,"section":student.section},**result}


def build_student_risk_profile(db: Session, student_id: str, user: User) -> dict:
    result=refresh_student_predictions(db,student_id,allowed_user=user)
    settings={s.key:s.value for s in db.query(SystemSetting).all()}
    thresholds={"gpa_threshold":settings.get("gpa_threshold",7.0),"attendance_threshold":settings.get("attendance_threshold",75.0)}
    student_data=db.scalar(select(SemesterFeature).where(SemesterFeature.student_id==student_id).order_by(SemesterFeature.id.desc()))
    data=_features(student_data.data)
    result["thresholds"]={**thresholds,"current_gpa_below_threshold":float(data.get("current_gpa",0))<thresholds["gpa_threshold"],"projected_attendance_below_threshold":float(data.get("projected_final_attendance",100))<thresholds["attendance_threshold"],"source":"admin_configuration"}
    result["student_metrics"]={"current_gpa":float(data.get("current_gpa",0)),"current_cgpa":float(data.get("current_cgpa",0)),"attendance":float(data.get("current_attendance_percentage",0)),"backlogs":int(data.get("current_backlog_count",0)),"internal_marks":float(data.get("internal_marks_average",0)),"absence_rate":round(float(data.get("recent_absence_rate",0))*100,1)}
    return result
