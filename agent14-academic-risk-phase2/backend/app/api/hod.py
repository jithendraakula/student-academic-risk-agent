from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import AlertIntervention, Assignment, Student, Teacher, User
from app.services.auth import require_roles

router = APIRouter()


@router.get("/mentor-comparison")
def get_mentor_comparison(db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    mentors = db.scalars(select(Teacher).where(Teacher.role == "mentor", Teacher.department == user.department)).all()
    rows = []
    for mentor in mentors:
        student_ids = list(db.scalars(select(Assignment.student_id).where(Assignment.teacher_id == mentor.id)).all())
        alerts = db.scalars(select(AlertIntervention).where(AlertIntervention.student_id.in_(student_ids))).all()
        rows.append({"mentor_id": mentor.id, "mentor_name": mentor.name, "assigned_students": len(student_ids), "open_alerts": sum(a.status != "RESOLVED" for a in alerts), "critical_students": len({a.student_id for a in alerts if a.risk_score >= 75}), "high_risk_students": len({a.student_id for a in alerts if a.risk_score >= 50}), "intervention_load": sum(a.priority_score for a in alerts if a.status != "RESOLVED")})
    rows.sort(key=lambda row: (row["high_risk_students"], row["critical_students"], row["intervention_load"]), reverse=True)
    return {"department": user.department, "items": rows}


@router.get("/mentors/{mentor_id}/students")
def list_mentor_students(mentor_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    mentor = db.scalar(select(Teacher).where(Teacher.id == mentor_id, Teacher.role == "mentor", Teacher.department == user.department))
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found in your department")
    assignments = db.scalars(select(Assignment).where(Assignment.teacher_id == mentor_id)).all()
    rows = []
    for assignment in assignments:
        student = db.get(Student, assignment.student_id)
        alerts = db.scalars(select(AlertIntervention).where(AlertIntervention.student_id == assignment.student_id)).all()
        open_alerts = [alert for alert in alerts if alert.status != "RESOLVED"]
        rows.append({
            "student_id": student.id,
            "student_name": student.name,
            "batch": student.batch,
            "section": student.section,
            "risk_score": max((alert.risk_score for alert in alerts), default=0),
            "priority_score": max((alert.priority_score for alert in open_alerts), default=0),
            "high_risk": any(alert.risk_score >= 50 for alert in alerts),
            "critical": any(alert.risk_score >= 75 for alert in alerts),
            "open_alerts": len(open_alerts),
            "risk_types": sorted({alert.risk_type for alert in alerts}),
        })
    rows.sort(key=lambda row: (row["high_risk"], row["critical"], row["priority_score"]), reverse=True)
    return {"mentor_id": mentor.id, "mentor_name": mentor.name, "items": rows}


@router.get("/students")
def list_department_students(db: Session = Depends(get_db), user: User = Depends(require_roles("hod"))):
    students = db.scalars(select(Student).where(Student.department == user.department)).all()
    return {"items": [{"student_id": s.id, "student_name": s.name, "batch": s.batch, "section": s.section, "department": s.department} for s in students]}
