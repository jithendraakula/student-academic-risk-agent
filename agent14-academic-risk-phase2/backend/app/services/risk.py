import sys
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import CourseFeature, SemesterFeature, Student, SystemSetting, User
from app.services.rbac import can_access_student, can_view_support_attention_risk


def _scalar(value):
    if value in (None, "", "None"):
        return None
    if isinstance(value, str):
        if value in ("True", "False"):
            return value == "True"
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except ValueError:
            return value
    return value


def _features(data: dict) -> dict:
    return {key: _scalar(value) for key, value in data.items()}


def get_student_or_404(db: Session, student_id: str) -> Student:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def build_student_risk_profile(db: Session, student_id: str, user: User) -> dict:
    student = get_student_or_404(db, student_id)
    if not can_access_student(db, user, student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student is outside your access scope")
    semester = db.scalars(select(SemesterFeature).where(SemesterFeature.student_id == student_id).order_by(SemesterFeature.id.desc())).first()
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester features not found")
    courses = db.scalars(select(CourseFeature).where(CourseFeature.student_id == student_id)).all()
    student_data = {"student_id": student.id, **_features(semester.data)}
    course_data = [_features(course.data) for course in courses]
    settings = {setting.key: setting.value for setting in db.query(SystemSetting).all()}
    thresholds = {
        "gpa_threshold": settings.get("gpa_threshold", 7.0),
        "attendance_threshold": settings.get("attendance_threshold", 75.0),
    }
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from ml.predictor import predict_all_risks
    result = predict_all_risks(student_data, course_data)
    if not can_view_support_attention_risk(user.role):
        result["risks"].pop("discontinuation", None)
    result["thresholds"] = {
        **thresholds,
        "current_gpa_below_threshold": float(student_data.get("current_gpa", 0)) < thresholds["gpa_threshold"],
        "projected_attendance_below_threshold": float(student_data.get("projected_final_attendance", 100)) < thresholds["attendance_threshold"],
        "source": "admin_configuration",
    }
    return {"student": {"student_id": student.id, "student_name": student.name, "department": student.department, "batch": student.batch, "section": student.section}, **result}
