from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import AlertIntervention, CourseFeature, Student, User
from app.services.auth import require_roles

router = APIRouter()


@router.get("/department-comparison")
def get_department_comparison(db: Session = Depends(get_db), user: User = Depends(require_roles("dean"))):
    students = db.scalars(select(Student)).all()
    alerts = db.scalars(select(AlertIntervention)).all()
    rows = []
    for department in sorted({student.department for student in students}):
        department_students = [student for student in students if student.department == department]
        department_ids = {student.id for student in department_students}
        department_alerts = [alert for alert in alerts if alert.student_id in department_ids]
        rows.append({"department": department, "total_students": len(department_students), "critical_students": len({a.student_id for a in department_alerts if a.risk_score >= 75}), "high_risk_students": len({a.student_id for a in department_alerts if a.risk_score >= 50}), "average_priority": round(sum(a.priority_score for a in department_alerts) / len(department_alerts), 1) if department_alerts else 0, "active_interventions": sum(a.status != "RESOLVED" for a in department_alerts), "resolved_interventions": sum(a.status == "RESOLVED" for a in department_alerts)})
    return {"items": rows}


@router.get("/risk-heatmap")
def get_risk_heatmap(db: Session = Depends(get_db), user: User = Depends(require_roles("dean"))):
    students = db.scalars(select(Student)).all()
    alerts = db.scalars(select(AlertIntervention)).all()
    course_features = db.scalars(select(CourseFeature)).all()
    rows = []
    for department in sorted({student.department for student in students}):
        student_ids = {student.id for student in students if student.department == department}
        department_alerts = [alert for alert in alerts if alert.student_id in student_ids]
        course_rows = [course.data for course in course_features if course.student_id in student_ids]

        def rate(risk_types: set[str]) -> float:
            affected = {alert.student_id for alert in department_alerts if alert.risk_type in risk_types and alert.risk_score >= 50}
            return round(len(affected) / max(1, len(student_ids)) * 100, 1)

        failed_courses = sum(1 for row in course_rows if row.get("course_failed") in (True, "True", "true", 1, "1"))
        rows.append({"department": department, "attendance_shortage": rate({"attendance"}), "course_failure": round(failed_courses / max(1, len(course_rows)) * 100, 1), "backlog": rate({"backlog"}), "gpa_threshold": rate({"gpa"}), "discontinuation": rate({"support_attention", "discontinuation"})})
    return {"items": rows}


@router.get("/departments/{department}/students")
def list_department_students(department: str, db: Session = Depends(get_db), user: User = Depends(require_roles("dean"))):
    students = db.scalars(select(Student).where(Student.department == department)).all()
    return {"department": department, "items": [{"student_id": student.id, "student_name": student.name, "batch": student.batch, "section": student.section, "department": student.department} for student in students]}
