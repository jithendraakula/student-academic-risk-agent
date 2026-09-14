"""Generate the canonical Agent 14 CSE demo dataset.

Design goals:
- 1 current CSE department
- 10 sections, 50 students each (500 students)
- 5 mentors, each responsible for exactly 2 sections
- 1 HOD and 1 Dean
- sequential 241FA04xxx-style roll numbers
- mostly stable students with a small, intentional high/critical pocket
- textual academic observations linked to explainable academic context
- historical outcomes are generated from noisy latent processes rather than direct
  copies of the prediction-time features
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import math
import numpy as np
import pandas as pd
from faker import Faker

from config import (
    ACADEMIC_YEAR,
    ATTENDANCE_THRESHOLD,
    BATCH,
    CHECKPOINT_WEEK,
    COURSES,
    CURRENT_SEMESTER,
    DEPARTMENT_ID,
    DEPARTMENT_NAME,
    GPA_THRESHOLD,
    MENTOR_IDS,
    OUT,
    PROGRAM,
    SECTIONS,
    STUDENTS_PER_SECTION,
    CRITICAL_PER_SECTION,
    HIGH_PER_SECTION,
    WATCH_PER_SECTION,
)

SEED = 2026
rng = np.random.default_rng(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)


def clip(x, lo, hi):
    return float(np.clip(x, lo, hi))


def sigmoid(x):
    x = float(np.clip(x, -30, 30))
    return 1.0 / (1.0 + math.exp(-x))


def bool_probability(p: float) -> bool:
    return bool(rng.random() < np.clip(p, 0.0, 1.0))


def academic_year_for_semester(semester: int) -> str:
    """Return the academic year for a standard two-semester B.Tech progression.

    The 2024-entry cohort maps as:
      Sem 1-2 -> 2024-25
      Sem 3-4 -> 2025-26
      Sem 5-6 -> 2026-27
      Sem 7-8 -> 2027-28
    """
    if not 1 <= semester <= 8:
        raise ValueError(f"semester must be between 1 and 8, got {semester}")
    start_year = BATCH + ((semester - 1) // 2)
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def mentor_for_section(section: str) -> str:
    idx = SECTIONS.index(section) // 2
    return MENTOR_IDS[idx]


def build_student_profile(section: str, position: int) -> dict:
    critical_n = CRITICAL_PER_SECTION[section]
    high_n = HIGH_PER_SECTION[section]
    watch_n = WATCH_PER_SECTION[section]

    if position < critical_n:
        state = "critical"
    elif position < critical_n + high_n:
        state = "high"
    elif position < critical_n + high_n + watch_n:
        state = "watch"
    else:
        state = "stable"

    params = {
        "stable":  {"ability": (7.9, 0.45), "attendance": (87, 3.8), "engagement": (0.79, 0.06), "trend": (0.00, 0.05)},
        "watch":   {"ability": (7.35, 0.48), "attendance": (78, 4.8), "engagement": (0.69, 0.07), "trend": (-0.05, 0.08)},
        "high":    {"ability": (6.75, 0.55), "attendance": (70, 5.5), "engagement": (0.57, 0.08), "trend": (-0.13, 0.10)},
        "critical":{"ability": (6.15, 0.55), "attendance": (61, 6.0), "engagement": (0.44, 0.09), "trend": (-0.24, 0.11)},
    }[state]
    ability = clip(rng.normal(*params["ability"]), 4.5, 9.5)
    attendance = clip(rng.normal(*params["attendance"]), 48, 98)
    engagement = clip(rng.normal(*params["engagement"]), 0.15, 0.96)
    trend = clip(rng.normal(*params["trend"]), -0.50, 0.35)

    # A minority of students have one contextual issue that should appear as text to
    # a mentor. These are explanatory observations, not hidden ML labels.
    context = "none"
    if state in {"critical", "high"}:
        weighted = ["illness", "transport", "assessment", "family", "late_arrival", "academic"]
        context = rng.choice(weighted, p=[0.18, 0.12, 0.18, 0.12, 0.15, 0.25])
    elif state == "watch" and rng.random() < 0.55:
        context = rng.choice(["assessment", "late_arrival", "academic", "none"], p=[0.25, 0.25, 0.35, 0.15])
    elif state == "stable" and rng.random() < 0.08:
        context = "improvement"

    return {
        "state": state,
        "ability": ability,
        "attendance": attendance,
        "engagement": engagement,
        "trend": trend,
        "context": context,
        "mentor_id": mentor_for_section(section),
    }


def generate_students_and_teachers():
    teachers = [
        {"teacher_id": "T001", "teacher_name": "Mentor One", "role": "mentor", "department": DEPARTMENT_ID, "email": "mentor.one.cse@vignan.ac.in"},
        {"teacher_id": "T002", "teacher_name": "Mentor Two", "role": "mentor", "department": DEPARTMENT_ID, "email": "mentor.two.cse@vignan.ac.in"},
        {"teacher_id": "T003", "teacher_name": "Mentor Three", "role": "mentor", "department": DEPARTMENT_ID, "email": "mentor.three.cse@vignan.ac.in"},
        {"teacher_id": "T004", "teacher_name": "Mentor Four", "role": "mentor", "department": DEPARTMENT_ID, "email": "mentor.four.cse@vignan.ac.in"},
        {"teacher_id": "T005", "teacher_name": "Mentor Five", "role": "mentor", "department": DEPARTMENT_ID, "email": "mentor.five.cse@vignan.ac.in"},
        {"teacher_id": "H001", "teacher_name": "CSE HOD", "role": "hod", "department": DEPARTMENT_ID, "email": "hod.cse@vignan.ac.in"},
        {"teacher_id": "D001", "teacher_name": "Dean", "role": "dean", "department": "", "email": "dean@vignan.ac.in"},
    ]

    students = []
    profiles = {}
    assignments = []
    sid_counter = 1
    for section in SECTIONS:
        for position in range(STUDENTS_PER_SECTION):
            sid = f"S{sid_counter:04d}"
            roll = f"241FA04{sid_counter:03d}"
            profile = build_student_profile(section, position)
            profile["section_position"] = position
            profiles[sid] = profile
            students.append({
                "student_id": sid,
                "roll_number": roll,
                "student_name": fake.name(),
                "department": DEPARTMENT_ID,
                "program": PROGRAM,
                "batch": BATCH,
                "section": section,
                "academic_year": ACADEMIC_YEAR,
                "current_semester": CURRENT_SEMESTER,
            })
            assignments.append({
                "assignment_id": f"ASG{sid_counter:04d}",
                "student_id": sid,
                "teacher_id": profile["mentor_id"],
                "academic_year": ACADEMIC_YEAR,
                "semester": CURRENT_SEMESTER,
                "assignment_type": "mentor",
            })
            sid_counter += 1

    return pd.DataFrame(students), pd.DataFrame(teachers), pd.DataFrame(assignments), profiles


def semester_metrics(profile: dict, semester: int, current: bool, previous: dict | None) -> dict:
    state = profile["state"]
    progression = semester / CURRENT_SEMESTER
    stability_noise = 0.20 if current else 0.26

    # Current values are gently worse than early semesters for at-risk profiles, but
    # still contain enough noise that the eventual outcomes are not direct copies.
    gpa = clip(profile["ability"] + profile["trend"] * progression + rng.normal(0, stability_noise), 4.1, 9.7)
    previous_gpa = previous["current_gpa"] if previous else clip(gpa + rng.normal(0, 0.35), 4.0, 9.8)
    gpa_change = gpa - previous_gpa

    attendance = clip(profile["attendance"] + profile["trend"] * 10 * progression + rng.normal(0, 2.2), 45, 98)
    att30 = clip(attendance + rng.normal(-1.8 if profile["trend"] < 0 else 0.6, 2.4), 40, 99)
    engagement = clip(profile["engagement"] + profile["trend"] * 0.12 * progression + rng.normal(0, 0.025), 0.08, 0.98)

    prev_backlog = int(previous["current_backlog_count"]) if previous else 0
    backlog_rate = max(0.02, 0.06 + max(0, 7.3 - gpa) * 0.13 + max(0, 72 - attendance) * 0.012)
    new_backlogs = int(rng.poisson(backlog_rate))
    cleared = int(rng.binomial(prev_backlog, 0.24 if state in {"stable", "watch"} else 0.15)) if prev_backlog else 0
    current_backlog = max(0, prev_backlog + new_backlogs - cleared)

    internal = clip(gpa * 8.4 + engagement * 9 + rng.normal(0, 4.2), 25, 94)
    midterm = clip(internal + rng.normal(0, 4.8), 20, 94)
    quiz = clip(internal + rng.normal(0, 5.2), 20, 95)
    assignment = clip(internal + engagement * 7 + rng.normal(0, 4.5), 20, 96)
    practical = clip(internal + rng.normal(1.5, 4.8), 20, 96)
    completion = clip(0.40 + engagement * 0.62 + rng.normal(0, 0.035), 0.25, 1.0)
    participation = clip(0.48 + engagement * 0.52 + rng.normal(0, 0.035), 0.25, 1.0)

    absent_days = int(np.clip(round((100 - attendance) * 0.42 + rng.normal(1.2, 1.3)), 0, 30))
    consecutive = int(rng.integers(2, 6)) if att30 < 68 else int(rng.integers(0, 3))
    prolonged = bool(att30 < 58 or (attendance < 62 and engagement < 0.38))

    fee_pressure = clip((1 - engagement) * 0.34 + (0.20 if profile["context"] == "family" else 0) + rng.normal(0, 0.06), 0, 0.85)
    fee_status = "overdue" if rng.random() < fee_pressure * 0.16 else "pending" if rng.random() < 0.05 else "paid"
    fee_arrears = int(rng.integers(5000, 25000)) if fee_status == "overdue" else int(rng.integers(500, 3500)) if fee_status == "pending" else 0
    payment_delay = int(rng.integers(5, 50)) if fee_status == "overdue" else 0

    return {
        "current_gpa": round(gpa, 2),
        "current_cgpa": round(clip((gpa * 0.62 + previous_gpa * 0.38) + rng.normal(0, 0.08), 4.0, 9.7), 2),
        "previous_gpa": round(previous_gpa, 2),
        "previous_cgpa": round(clip(previous_gpa + rng.normal(0, 0.13), 4.0, 9.7), 2),
        "gpa_change": round(gpa_change, 2),
        "internal_marks_average": round(internal, 1),
        "midterm_marks_average": round(midterm, 1),
        "quiz_average": round(quiz, 1),
        "assignment_average": round(assignment, 1),
        "practical_marks_average": round(practical, 1),
        "assessment_trend": "declining" if gpa_change < -0.35 else "improving" if gpa_change > 0.35 else "stable",
        "assignment_completion_rate": round(completion, 2),
        "current_attendance_percentage": round(attendance, 1),
        "attendance_last_30_days": round(att30, 1),
        "attendance_trend": "declining" if att30 < attendance - 1.5 else "improving" if att30 > attendance + 1.5 else "stable",
        "consecutive_absence_days": consecutive,
        "total_absent_days": absent_days,
        "recent_absence_rate": round((100 - att30) / 100, 2),
        "projected_final_attendance": round(clip(attendance * 0.62 + att30 * 0.38, 40, 99), 1),
        "current_backlog_count": current_backlog,
        "previous_backlog_count": prev_backlog,
        "total_historical_backlogs": max(current_backlog, prev_backlog) + int(rng.integers(0, 2)),
        "new_backlogs_last_semester": new_backlogs,
        "repeated_backlog_subject_count": int(min(current_backlog, rng.integers(0, 2 + current_backlog))),
        "backlog_growth_rate": round((current_backlog - prev_backlog) / max(1, prev_backlog + 1), 3),
        "assessment_participation_rate": round(participation, 2),
        "recent_engagement_score": round(engagement, 2),
        "engagement_trend": "declining" if engagement < profile["engagement"] - 0.035 else "improving" if engagement > profile["engagement"] + 0.035 else "stable",
        "fee_status": fee_status,
        "fee_arrears_amount": fee_arrears,
        "payment_delay_days": payment_delay,
        "installment_pending": bool(fee_status == "pending" and rng.random() < 0.65),
        "prolonged_absence_flag": prolonged,
        "prolonged_absence_days": int(consecutive + rng.integers(2, 8)) if prolonged else 0,
        "academic_decline_flag": bool(gpa_change < -0.45 or (assignment < 48 and internal < 52)),
        "repeated_backlog_flag": bool(current_backlog > 0 and prev_backlog > 0),
        "engagement_decline_flag": bool(engagement < 0.46 or profile["trend"] < -0.20),
    }


def generate_semester_and_course_data(students_df, profiles):
    semester_rows = []
    course_rows = []
    previous_by_student = {}

    for student in students_df.to_dict("records"):
        sid = student["student_id"]
        profile = profiles[sid]
        previous = None
        for semester in range(1, CURRENT_SEMESTER + 1):
            current = semester == CURRENT_SEMESTER
            metrics = semester_metrics(profile, semester, current, previous)
            row = {
                "student_id": sid,
                "roll_number": student["roll_number"],
                "cohort": BATCH,
                "academic_year": academic_year_for_semester(semester),
                "semester": semester,
                "checkpoint_week": CHECKPOINT_WEEK,
                "department": DEPARTMENT_ID,
                "batch": BATCH,
                "section": student["section"],
                "snapshot_type": "current" if current else "historical",
                **metrics,
            }
            semester_rows.append(row)

            for course_id, course_name, credits in COURSES[semester]:
                # Course-specific performance is correlated with student state but has
                # enough variability that one weak course does not make every course fail.
                difficulty = {
                    "CSE103": 1.5, "CSE202": 1.4, "CSE203": 1.2,
                    "CSE401": 1.5, "CSE405": 1.3, "CSE501": 1.4,
                    "CSE503": 1.5, "CSE504": 1.1,
                }.get(course_id, 0.0)
                course_marks = clip(metrics["internal_marks_average"] - difficulty + rng.normal(0, 5.5), 18, 96)
                midterm = clip(course_marks + rng.normal(0, 6), 15, 96)
                quiz = clip(course_marks + rng.normal(0, 6), 15, 98)
                assignment = clip(course_marks + metrics["recent_engagement_score"] * 7 + rng.normal(0, 5), 15, 98)
                practical = clip(course_marks + rng.normal(1, 6), 15, 98)
                cat = clip(metrics["current_attendance_percentage"] + rng.normal(0, 3.5), 45, 98)
                prior_attempts = int(1 if previous and previous.get("current_backlog_count", 0) > 0 and rng.random() < 0.22 else 0)
                # Course failure is a relatively uncommon outcome, but it becomes materially
                # more likely when marks, attendance, assignment completion, or prior attempts
                # are weak. The outcome is stochastic and is not a direct copy of the feature.
                course_gap = max(0.0, 50.0 - course_marks) / 10.0
                attendance_gap = max(0.0, 75.0 - cat) / 10.0
                completion_gap = max(0.0, 0.75 - metrics["assignment_completion_rate"]) / 0.10
                course_signal = (
                    -4.25
                    + 0.92 * course_gap
                    + 0.72 * attendance_gap
                    + 0.45 * completion_gap
                    + 0.62 * prior_attempts
                    + 0.20 * max(0.0, 6.5 - metrics["current_gpa"])
                )
                failed = False if current else bool(rng.random() < sigmoid(course_signal))
                course_rows.append({
                    "student_id": sid,
                    "roll_number": student["roll_number"],
                    "cohort": BATCH,
                    "academic_year": academic_year_for_semester(semester),
                    "semester": semester,
                    "checkpoint_week": CHECKPOINT_WEEK,
                    "snapshot_type": "current" if current else "historical",
                    "course_id": course_id,
                    "course_name": course_name,
                    "course_credits": credits,
                    "internal_marks": round(course_marks, 1),
                    "midterm_marks": round(midterm, 1),
                    "quiz_average": round(quiz, 1),
                    "assignment_average": round(assignment, 1),
                    "practical_marks": round(practical, 1),
                    "course_attendance_percentage": round(cat, 1),
                    "course_attendance_trend": "declining" if cat < metrics["current_attendance_percentage"] - 2 else "stable",
                    "previous_course_attempts": prior_attempts,
                    "previous_course_grade": "F" if prior_attempts else "",
                    "assessment_trend": metrics["assessment_trend"],
                    "assignment_completion_rate": metrics["assignment_completion_rate"],
                    "course_failed": np.nan if current else failed,
                })
            previous = metrics
            previous_by_student[sid] = metrics

    return pd.DataFrame(semester_rows), pd.DataFrame(course_rows)


def generate_outcomes(semester_df, course_df, profiles):
    outcomes = []
    historical_sem = semester_df[semester_df["snapshot_type"] == "historical"]
    for row in historical_sem.to_dict("records"):
        p = profiles[row["student_id"]]
        attendance_signal = (75 - row["projected_final_attendance"]) / 10
        academic_signal = (7.0 - row["current_gpa"]) / 0.7
        backlog_signal = row["current_backlog_count"] * 0.7 + max(0, row["backlog_growth_rate"]) * 1.1
        engagement_signal = (0.50 - row["recent_engagement_score"]) / 0.12
        decline_signal = 0.6 if row["academic_decline_flag"] else 0.0

        # Outcome prevalences are intentionally lower than the R0 baseline so that a
        # healthy cohort does not look like an institution-wide crisis. State affects the
        # latent propensity, but features remain the primary observable evidence.
        state_bias = {"stable": 0.0, "watch": 0.35, "high": 0.85, "critical": 1.35}[p["state"]]
        attendance_p = sigmoid(-3.00 + 1.30 * attendance_signal + 0.60 * max(0, row["consecutive_absence_days"] - 2) / 2 + 0.60 * state_bias)
        gpa_p = sigmoid(-3.40 + 1.50 * academic_signal + 0.80 * max(0, -row["gpa_change"]) + decline_signal * 0.45 + 0.50 * state_bias)
        backlog_p = sigmoid(-3.20 + 1.10 * backlog_signal + 0.45 * max(0, 7.0 - row["current_gpa"]) + 0.50 * state_bias)
        support_p = sigmoid(-6.00 + 0.80 * max(0, attendance_signal) + 0.60 * max(0, academic_signal) + 1.10 * max(0, engagement_signal) + 0.95 * (1 if row["prolonged_absence_flag"] else 0) + 0.60 * (1 if p["context"] in {"family", "illness"} else 0) + 0.65 * state_bias)

        course_slice = course_df[(course_df.student_id == row["student_id"]) & (course_df.semester == row["semester"])]
        weak_courses = int((course_slice.internal_marks < 48).sum())
        average_course_attendance_gap = max(0.0, 75.0 - float(course_slice.course_attendance_percentage.mean())) / 10.0
        average_course_marks_gap = max(0.0, 52.0 - float(course_slice.internal_marks.mean())) / 10.0
        course_failure_p = sigmoid(
            -3.70
            + 0.85 * weak_courses
            + 0.72 * average_course_attendance_gap
            + 0.62 * average_course_marks_gap
            + 0.34 * max(0, 6.8 - row["current_gpa"])
            + 0.32 * state_bias
        )

        outcomes.append({
            "student_id": row["student_id"],
            "cohort": BATCH,
            "academic_year": row["academic_year"],
            "semester": row["semester"],
            "checkpoint_week": row["checkpoint_week"],
            "outcome_horizon": "end_of_semester",
            "course_failed": bool_probability(course_failure_p),
            "new_backlog": bool_probability(backlog_p),
            "gpa_below_threshold": bool_probability(gpa_p),
            "attendance_shortage": bool_probability(attendance_p),
            "discontinued": bool_probability(support_p * 0.32),
        })
    return pd.DataFrame(outcomes)


def generate_reference_data():
    rows = []
    for semester, courses in COURSES.items():
        for course_id, course_name, credits in courses:
            rows.append({
                "department_id": DEPARTMENT_ID,
                "department_name": DEPARTMENT_NAME,
                "course_id": course_id,
                "course_name": course_name,
                "semester": semester,
                "course_credits": credits,
                "passing_marks": 40,
                "attendance_threshold": ATTENDANCE_THRESHOLD,
                "gpa_threshold": GPA_THRESHOLD,
            })
    return pd.DataFrame(rows)


def generate_observations(students_df, profiles):
    rows = []
    obs_counter = 1
    base_date = date(2026, 8, 3)
    for student in students_df.to_dict("records"):
        sid = student["student_id"]
        p = profiles[sid]
        context = p["context"]
        observation_texts = []
        category = None
        follow_up = False

        if context == "illness":
            observation_texts.append("Absent for three consecutive days due to fever; mentor requested a check-in after return.")
            category, follow_up = "health_related", True
        elif context == "transport":
            observation_texts.append("Recent first-hour attendance was affected by recurring transport delays; mentor is reviewing a practical attendance plan.")
            category, follow_up = "attendance", True
        elif context == "assessment":
            observation_texts.append("Missed one internal assessment and two quiz attempts; subject support is being considered before the next checkpoint.")
            category, follow_up = "assessment", True
        elif context == "family":
            observation_texts.append("Student reported a short-term family responsibility affecting attendance and study time; mentor scheduled a follow-up.")
            category, follow_up = "support", True
        elif context == "late_arrival":
            observation_texts.append("Repeated late arrival to first-hour classes observed over the last two weeks; attendance recovery target discussed.")
            category, follow_up = "attendance", True
        elif context == "academic":
            subject = rng.choice(["Design and Analysis of Algorithms", "Database Management Systems", "Computer Networks"])
            observation_texts.append(f"Student is finding {subject} difficult and has requested additional problem-solving support.")
            category, follow_up = "academic_performance", True
        elif context == "improvement":
            observation_texts.append("Attendance and assignment completion improved after the previous mentor follow-up.")
            category, follow_up = "improvement", False

        if observation_texts:
            rows.append({
                "observation_id": f"OBS{obs_counter:05d}",
                "student_id": sid,
                "observed_on": (base_date + timedelta(days=int(rng.integers(0, 30)))).isoformat(),
                "category": category,
                "observation_text": observation_texts[0],
                "source_role": "mentor",
                "follow_up_required": follow_up,
                "status": "OPEN" if follow_up else "CLOSED",
            })
            obs_counter += 1
    return pd.DataFrame(rows)


def generate_alert_seed_data(semester_df, course_df, observations_df, students_df, profiles):
    # Seed a modest number of historical/current work items so the intervention UI
    # has examples. Canonical predictions/alerts will be regenerated from RiskPrediction
    # after the new ML models are trained.
    current = semester_df[semester_df["snapshot_type"] == "current"].copy()
    candidates = current[(current["current_attendance_percentage"] < 72) | (current["current_gpa"] < 6.8) | (current["current_backlog_count"] >= 2)].copy()
    candidates["priority_seed"] = (
        (75 - candidates["current_attendance_percentage"]).clip(lower=0) * 1.8
        + (7.0 - candidates["current_gpa"]).clip(lower=0) * 22
        + candidates["current_backlog_count"] * 10
    )
    candidates = candidates.sort_values("priority_seed", ascending=False).head(72)

    rows = []
    for i, row in enumerate(candidates.to_dict("records"), start=1):
        if row["current_attendance_percentage"] < 70:
            risk_type = "attendance_shortage"
            action = "Review attendance context and agree on a recovery plan."
        elif row["current_backlog_count"] >= 2:
            risk_type = "backlog"
            action = "Arrange subject-focused backlog recovery support."
        else:
            risk_type = "gpa_threshold"
            action = "Review academic progress and agree on a focused study plan."
        mentor_id = profiles[row["student_id"]]["mentor_id"]
        priority = float(np.clip(row["priority_seed"] + rng.uniform(10, 22), 40, 96))
        status = str(rng.choice(["NEW", "ACKNOWLEDGED", "ACTION_TAKEN", "FOLLOW_UP"], p=[0.30, 0.30, 0.25, 0.15]))
        rows.append({
            "alert_id": f"ALT{i:05d}",
            "student_id": row["student_id"],
            "teacher_id": mentor_id,
            "risk_type": risk_type,
            "risk_score": round(float(np.clip(row["priority_seed"] + rng.uniform(5, 18), 20, 98)), 1),
            "priority_score": round(priority, 1),
            "confidence_level": "Medium",
            "intervenability_score": "High" if risk_type == "attendance_shortage" else "Medium",
            "created_at": "2026-09-01",
            "alert_status": status,
            "intervention_id": f"INT{i:05d}",
            "intervention_type": "mentor_check_in",
            "suggested_action": action,
            "action_taken": "Mentor follow-up completed" if status in {"ACTION_TAKEN", "FOLLOW_UP"} else "",
            "intervention_date": "2026-09-03" if status in {"ACTION_TAKEN", "FOLLOW_UP"} else "",
            "follow_up_date": "2026-09-10" if status == "FOLLOW_UP" else "",
            "outcome_status": "",
            "outcome_notes": "",
            "risk_score_after_intervention": "",
        })
    return pd.DataFrame(rows)


def write_outputs():
    OUT.mkdir(parents=True, exist_ok=True)
    students, teachers, assignments, profiles = generate_students_and_teachers()
    semester, courses = generate_semester_and_course_data(students, profiles)
    outcomes = generate_outcomes(semester, courses, profiles)
    reference = generate_reference_data()
    observations = generate_observations(students, profiles)
    alerts = generate_alert_seed_data(semester, courses, observations, students, profiles)

    datasets = {
        "students": students,
        "teachers": teachers,
        "assignments": assignments,
        "student_semester_features": semester,
        "student_course_features": courses,
        "historical_outcomes": outcomes,
        "academic_reference_data": reference,
        "academic_observations": observations,
        "alerts_interventions": alerts,
    }
    for name, frame in datasets.items():
        frame.to_csv(OUT / f"{name}.csv", index=False)

    summary = {
        "dataset_version": "agent14-cse-2026-r8",
        "department": DEPARTMENT_NAME,
        "students": len(students),
        "sections": len(SECTIONS),
        "students_per_section": STUDENTS_PER_SECTION,
        "mentors": len(MENTOR_IDS),
        "hods": 1,
        "deans": 1,
        "assignments": len(assignments),
        "semester_snapshots": len(semester),
        "course_snapshots": len(courses),
        "historical_outcomes": len(outcomes),
        "reference_rows": len(reference),
        "observations": len(observations),
        "seed_alerts": len(alerts),
        "roll_number_first": students.iloc[0]["roll_number"],
        "roll_number_last": students.iloc[-1]["roll_number"],
        "current_semester": CURRENT_SEMESTER,
    }
    pd.Series(summary).to_json(OUT / "dataset_manifest.json", indent=2)

    print(summary)
    print("Historical outcome rates:")
    print(outcomes[["course_failed", "new_backlog", "gpa_below_threshold", "attendance_shortage", "discontinued"]].mean().round(3).to_dict())
    print("State distribution:")
    print(pd.Series([p["state"] for p in profiles.values()]).value_counts().to_dict())
    print("Section/mentor check:")
    print(assignments.merge(students[["student_id", "section"]], on="student_id").groupby("teacher_id")["section"].nunique().to_dict())


if __name__ == "__main__":
    write_outputs()
