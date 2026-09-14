import csv
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import Index, create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.models.domain import (
    AcademicObservation,
    AcademicReference,
    AlertIntervention,
    Assignment,
    CourseFeature,
    InterventionRecord,
    Notification,
    HistoricalOutcome,
    SemesterFeature,
    Student,
    SystemSetting,
    Teacher,
    User,
    Base,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BACKEND_DIR / 'agent14.db'}",
)

CONNECT_ARGS = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=CONNECT_ARGS,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _read_csv(filename: str) -> list[dict]:
    with (
        PROJECT_DIR / "data" / "processed" / filename
    ).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def _as_bool(value):
    return value in (True, "True", "true", "1", 1)


def _as_int(value):
    if value in (None, "", "None"):
        return None
    return int(float(value))


def _ensure_student_roll_number_column() -> None:
    """Add the roll-number column to an existing database if required."""
    inspector = inspect(engine)

    if not inspector.has_table("students"):
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("students")
    }

    if "roll_number" in columns:
        return

    statement = (
        "ALTER TABLE students "
        "ADD COLUMN roll_number VARCHAR(32)"
    )

    with engine.begin() as connection:
        connection.execute(text(statement))


def seed_database(db) -> None:
    from app.services.auth import hash_password

    _ensure_student_roll_number_column()

    # ---------------------------------------------------------------
    # Existing database
    # ---------------------------------------------------------------

    if db.query(Student).first():
        roll_map = {
            row["student_id"]: row.get("roll_number")
            for row in _read_csv("students.csv")
        }

        changed = False

        for student in db.query(Student).all():
            if (
                not student.roll_number
                and roll_map.get(student.id)
            ):
                student.roll_number = roll_map[student.id]
                changed = True

        if changed:
            db.commit()

        for user in db.query(User).all():
            if user.password_hash == "demo":
                user.password_hash = hash_password("demo")

        db.commit()

        if not db.get(
            SystemSetting,
            "gpa_threshold",
        ):
            db.add_all(
                [
                    SystemSetting(
                        key="gpa_threshold",
                        value=7.0,
                        description="GPA risk threshold",
                    ),
                    SystemSetting(
                        key="attendance_threshold",
                        value=75.0,
                        description="Attendance shortage threshold",
                    ),
                ]
            )
            db.commit()

        return

    # ---------------------------------------------------------------
    # Load CSV data
    # ---------------------------------------------------------------

    students = _read_csv("students.csv")
    teachers = _read_csv("teachers.csv")
    assignments = _read_csv("assignments.csv")
    references = _read_csv("academic_reference_data.csv")
    semester = _read_csv("student_semester_features.csv")
    courses = _read_csv("student_course_features.csv")
    historical = _read_csv("historical_outcomes.csv")
    observations = _read_csv("academic_observations.csv")
    alerts = _read_csv("alerts_interventions.csv")

    # ---------------------------------------------------------------
    # 1. Parent tables
    #
    # Teachers and students must exist before inserting records
    # that reference them.
    # ---------------------------------------------------------------

    db.add_all(
        [
            Teacher(
                id=row["teacher_id"],
                name=row["teacher_name"],
                role=row["role"],
                department=row["department"] or None,
                email=row["email"],
            )
            for row in teachers
        ]
    )

    db.add_all(
        [
            Student(
                id=row["student_id"],
                roll_number=row.get("roll_number"),
                name=row["student_name"],
                department=row["department"],
                program=row["program"],
                batch=row["batch"],
                section=row["section"],
                academic_year=row["academic_year"],
                current_semester=_as_int(
                    row["current_semester"]
                ),
            )
            for row in students
        ]
    )

    # Force parent INSERTs before dependent records.
    db.flush()

    # ---------------------------------------------------------------
    # 2. Student/teacher-dependent academic records
    # ---------------------------------------------------------------

    db.add_all(
        [
            Assignment(
                id=row["assignment_id"],
                student_id=row["student_id"],
                teacher_id=row["teacher_id"],
                academic_year=row["academic_year"],
                semester=_as_int(row["semester"]),
                assignment_type=row["assignment_type"],
            )
            for row in assignments
        ]
    )

    db.add_all(
        [
            AcademicReference(
                data=row
            )
            for row in references
        ]
    )

    db.add_all(
        [
            SemesterFeature(
                student_id=row["student_id"],
                semester=_as_int(row["semester"]),
                data=row,
            )
            for row in semester
        ]
    )

    db.add_all(
        [
            CourseFeature(
                student_id=row["student_id"],
                course_id=row["course_id"],
                semester=_as_int(row["semester"]),
                data=row,
            )
            for row in courses
        ]
    )

    db.add_all(
        [
            HistoricalOutcome(
                student_id=row["student_id"],
                semester=_as_int(row["semester"]),
                data=row,
            )
            for row in historical
        ]
    )

    # Persist all student-dependent academic rows before
    # observations and alerts.
    db.flush()

    # ---------------------------------------------------------------
    # 3. Observations
    # ---------------------------------------------------------------

    db.add_all(
        [
            AcademicObservation(
                id=row["observation_id"],
                student_id=row["student_id"],
                observed_on=row["observed_on"],
                category=row["category"],
                observation_text=row["observation_text"],
                source_role=row["source_role"],
                follow_up_required=_as_bool(
                    row["follow_up_required"]
                ),
                status=row["status"],
            )
            for row in observations
        ]
    )

    # ---------------------------------------------------------------
    # 4. Alerts / interventions
    # ---------------------------------------------------------------

    db.add_all(
        [
            AlertIntervention(
                id=row["alert_id"],
                student_id=row["student_id"],
                teacher_id=row["teacher_id"],
                risk_type=row["risk_type"],
                risk_score=float(row["risk_score"]),
                priority_score=float(
                    row["priority_score"]
                ),
                status=row["alert_status"],
                data=row,
            )
            for row in alerts
        ]
    )

    # ---------------------------------------------------------------
    # 5. Demo users
    # ---------------------------------------------------------------

    demo_users = [
        User(
            id="T001",
            email="mentor.one.cse@vignan.ac.in",
            name="Mentor One",
            role="mentor",
            department="DEPT_CSE",
            password_hash=hash_password("demo"),
        ),
        User(
            id="T002",
            email="mentor.two.cse@vignan.ac.in",
            name="Mentor Two",
            role="mentor",
            department="DEPT_CSE",
            password_hash=hash_password("demo"),
        ),
        User(
            id="T003",
            email="mentor.three.cse@vignan.ac.in",
            name="Mentor Three",
            role="mentor",
            department="DEPT_CSE",
            password_hash=hash_password("demo"),
        ),
        User(
            id="T004",
            email="mentor.four.cse@vignan.ac.in",
            name="Mentor Four",
            role="mentor",
            department="DEPT_CSE",
            password_hash=hash_password("demo"),
        ),
        User(
            id="T005",
            email="mentor.five.cse@vignan.ac.in",
            name="Mentor Five",
            role="mentor",
            department="DEPT_CSE",
            password_hash=hash_password("demo"),
        ),
        User(
            id="H001",
            email="hod.cse@vignan.ac.in",
            name="HOD CSE",
            role="hod",
            department="DEPT_CSE",
            password_hash=hash_password("demo"),
        ),
        User(
            id="D001",
            email="dean@vignan.ac.in",
            name="Dean",
            role="dean",
            password_hash=hash_password("demo"),
        ),
        User(
            id="A001",
            email="admin@vignan.ac.in",
            name="Admin",
            role="admin",
            password_hash=hash_password("demo"),
        ),
    ]

    db.add_all(demo_users)

    # ---------------------------------------------------------------
    # 6. System settings
    # ---------------------------------------------------------------

    db.add_all(
        [
            SystemSetting(
                key="gpa_threshold",
                value=7.0,
                description="GPA risk threshold",
            ),
            SystemSetting(
                key="attendance_threshold",
                value=75.0,
                description="Attendance shortage threshold",
            ),
        ]
    )

    # ---------------------------------------------------------------
    # 7. Final commit
    # ---------------------------------------------------------------

    db.commit()


def run_migrations() -> None:
    try:
        from alembic import command
        from alembic.config import Config

        cfg = Config(
            str(PROJECT_DIR / "alembic.ini")
        )

        cfg.set_main_option(
            "sqlalchemy.url",
            DATABASE_URL.replace("%", "%%"),
        )

        # Fresh database:
        # create complete SQLAlchemy schema first, then mark
        # the current Alembic migration as applied.
        if not inspect(engine).has_table("students"):
            Base.metadata.create_all(bind=engine)
            command.stamp(cfg, "head")

        # Existing database:
        # apply pending Alembic migrations.
        else:
            command.upgrade(cfg, "head")

    except Exception:
        # Keep fresh installation recoverable if Alembic
        # cannot be executed during initialization.
        if not inspect(engine).has_table("students"):
            Base.metadata.create_all(bind=engine)


def _ensure_case_schema() -> None:
    """Reconcile case tables for databases stamped before case support."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    if not inspector.has_table("alerts_interventions"):
        return

    columns = {
        column["name"]
        for column in inspector.get_columns(
            "alerts_interventions"
        )
    }

    if "case_id" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE alerts_interventions "
                    "ADD COLUMN case_id VARCHAR(40)"
                )
            )

    Index(
        "ix_alerts_interventions_case_id",
        AlertIntervention.case_id,
    ).create(
        bind=engine,
        checkfirst=True,
    )


def init_db() -> None:
    inspector = inspect(engine)

    if (
        inspector.has_table("alembic_version")
        or inspector.has_table("students")
    ):
        run_migrations()

    else:
        Base.metadata.create_all(bind=engine)

        try:
            from alembic import command
            from alembic.config import Config

            cfg = Config(
                str(PROJECT_DIR / "alembic.ini")
            )

            cfg.set_main_option(
                "sqlalchemy.url",
                DATABASE_URL.replace("%", "%%"),
            )

            command.stamp(cfg, "head")

        except Exception:
            pass

    _ensure_case_schema()

    with SessionLocal() as db:
        seed_database(db)

        from app.services.cases import backfill_student_cases

        backfill_student_cases(db)

        # Precompute the current-risk snapshot once at startup
        # so dashboards and student profiles do not trigger ML
        # generation during the first page load.
        try:
            from app.services.performance import (
                warm_current_risk_store
            )

            warm_current_risk_store(db)

        except Exception:
            # Startup remains available if optional model warming fails.
            # Request-time lazy generation remains the fallback.
            db.rollback()