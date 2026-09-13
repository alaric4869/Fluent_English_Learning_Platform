import json

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app import database_migrations
from app.config import FASTAPI_ROOT
from app.models.adaptive_learning import AdaptationDecisionModel
from app.models.ielts import PracticeAttempt


EXPECTED_TABLES = {
    "adaptation_decisions",
    "alembic_version",
    "exercise_attempts",
    "ielts_practice_attempts",
    "ielts_practice_questions",
    "ielts_practice_sections",
    "ielts_practice_sets",
    "learner_profile_snapshots",
    "learner_profiles",
    "learner_skill_snapshots",
    "learning_resources",
    "skill_performances",
    "study_sessions",
    "study_plan_items",
    "study_plans",
    "weakness_assessment_runs",
    "weakness_skill_assessments",
}
HEAD_REVISION = "0006_adaptation_decisions"


def test_upgrade_database_creates_a_fresh_schema(tmp_path, monkeypatch) -> None:
    engine = _use_database(tmp_path / "fresh.db", monkeypatch)

    database_migrations.upgrade_database()

    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
    assert "priority" in {
        column["name"] for column in inspect(engine).get_columns("learning_resources")
    }
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == (
            HEAD_REVISION
        )


def test_upgrade_database_adopts_existing_schema_without_losing_attempts(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "existing.db", monkeypatch)
    _create_unversioned_baseline(engine, database_migrations.settings.database_url)

    database_migrations.upgrade_database()

    with Session(engine) as session:
        attempt = session.scalar(select(PracticeAttempt))
        assert attempt is not None
        assert attempt.answers == {"17": "A", "18": "E"}
        assert attempt.submission_revision == 0
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == (
            HEAD_REVISION
        )


def test_upgrade_backfills_decisions_for_plans_created_at_previous_revision(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "previous-plan.db", monkeypatch)
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "0005_daily_study_plans")
    with engine.begin() as connection:
        resource = connection.exec_driver_sql(
            """
            INSERT INTO learning_resources (
                slug, title, resource_type, skill, topic, difficulty,
                estimated_duration_minutes, content, tags, priority, active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "existing-resource",
                "Existing resource",
                "practice",
                "listening",
                "Daily English",
                "intermediate",
                30,
                json.dumps({}),
                json.dumps([]),
                50,
                1,
                "2026-09-13 00:00:00",
                "2026-09-13 00:00:00",
            ),
        )
        plan = connection.exec_driver_sql(
            """
            INSERT INTO study_plans (
                user_key, plan_date, status, source, generator_version,
                weakness_assessment_run_id, recommender_version, total_minutes,
                explanation, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "learner",
                "2026-09-14",
                "active",
                "rule_based",
                "rule-based-v1",
                None,
                "rule-based-v1",
                110,
                json.dumps(["Existing plan"]),
                "2026-09-13 00:00:00",
                "2026-09-13 00:00:00",
            ),
        )
        connection.exec_driver_sql(
            """
            INSERT INTO study_plan_items (
                study_plan_id, skill, position, system_planned_minutes,
                planned_minutes, system_resource_id, resource_id, status,
                recommendation_score, reasons, manual_override, override_note,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan.lastrowid,
                "listening",
                1,
                40,
                40,
                resource.lastrowid,
                resource.lastrowid,
                "pending",
                95.0,
                json.dumps(["Listening weakness confirmed"]),
                0,
                "",
                "2026-09-13 00:00:00",
                "2026-09-13 00:00:00",
            ),
        )

    database_migrations.upgrade_database()

    with Session(engine) as session:
        decision = session.scalar(select(AdaptationDecisionModel))
        assert decision is not None
        assert decision.decision_type == "system_recommendation"
        assert decision.previous_planned_minutes == 30
        assert decision.new_planned_minutes == 40
        assert decision.new_resource_id == resource.lastrowid
        assert decision.reasons == ["Listening weakness confirmed"]


def _use_database(path, monkeypatch):
    database_url = f"sqlite:///{path}"
    engine = create_engine(database_url)
    monkeypatch.setattr(database_migrations, "engine", engine)
    monkeypatch.setattr(database_migrations.settings, "database_url", database_url)
    return engine


def _create_unversioned_baseline(engine, database_url: str) -> None:
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, database_migrations.BASELINE_REVISION)
    with engine.begin() as connection:
        result = connection.exec_driver_sql(
            """
            INSERT INTO ielts_practice_sets (
                slug, book_number, test_number, skill, title, description,
                duration_minutes, content_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "existing-listening",
                20,
                1,
                "listening",
                "Existing",
                "Existing learner data",
                30,
                "v1",
            ),
        )
        connection.exec_driver_sql(
            """
            INSERT INTO ielts_practice_attempts (
                practice_set_id, user_key, status, answers, results, score,
                started_at, updated_at, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.lastrowid,
                "local-learner",
                "in_progress",
                json.dumps({"17": "A", "18": "E"}),
                json.dumps([]),
                None,
                "2026-09-13 00:00:00",
                "2026-09-13 00:00:00",
                None,
            ),
        )
        connection.exec_driver_sql("DROP TABLE alembic_version")
