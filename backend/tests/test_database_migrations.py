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
    "notebook_notes",
    "review_attempts",
    "review_items",
    "resource_user_states",
    "saved_sentences",
    "skill_performances",
    "study_sessions",
    "study_plan_items",
    "study_plans",
    "speaking_retelling_records",
    "speaking_retelling_submissions",
    "speaking_sentence_progress",
    "vocabulary_items",
    "weakness_assessment_runs",
    "weakness_skill_assessments",
    "writing_drafts",
    "writing_submissions",
    "work_evaluations",
    "weekly_coaching_reports",
}
HEAD_REVISION = "0016_ai_recommendation_responses"


def test_upgrade_database_creates_a_fresh_schema(tmp_path, monkeypatch) -> None:
    engine = _use_database(tmp_path / "fresh.db", monkeypatch)

    database_migrations.upgrade_database()

    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
    assert "priority" in {
        column["name"] for column in inspect(engine).get_columns("learning_resources")
    }
    assert {"started_at", "completed_at"} <= {
        column["name"] for column in inspect(engine).get_columns("study_plan_items")
    }
    study_session_columns = {
        column["name"]: column
        for column in inspect(engine).get_columns("study_sessions")
    }
    assert "updated_at" in study_session_columns
    assert study_session_columns["completed_at"]["nullable"] is True
    assert study_session_columns["accuracy"]["nullable"] is True
    skill_performance_columns = {
        column["name"]: column
        for column in inspect(engine).get_columns("skill_performances")
    }
    assert skill_performance_columns["accuracy"]["nullable"] is True
    assert "source_decision_id" in {
        column["name"]
        for column in inspect(engine).get_columns("adaptation_decisions")
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


def test_plan_item_timestamp_migration_can_downgrade_cleanly(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "timestamps.db", monkeypatch)
    database_migrations.upgrade_database()
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    command.downgrade(config, "0006_adaptation_decisions")

    assert {"started_at", "completed_at"}.isdisjoint(
        column["name"] for column in inspect(engine).get_columns("study_plan_items")
    )
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == "0006_adaptation_decisions"


def test_vocabulary_review_migration_can_downgrade_cleanly(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "reviews.db", monkeypatch)
    database_migrations.upgrade_database()
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    command.downgrade(config, "0007_plan_item_timestamps")

    assert {"vocabulary_items", "review_items", "review_attempts"}.isdisjoint(
        inspect(engine).get_table_names()
    )
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == "0007_plan_item_timestamps"


def test_work_evaluation_migration_can_downgrade_cleanly(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "work-evaluations.db", monkeypatch)
    database_migrations.upgrade_database()
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    command.downgrade(config, "0013_speaking_workspace")

    assert "work_evaluations" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == "0013_speaking_workspace"


def test_weekly_coaching_migration_can_downgrade_cleanly(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "weekly-coaching.db", monkeypatch)
    database_migrations.upgrade_database()
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    command.downgrade(config, "0014_work_evaluations")

    assert "weekly_coaching_reports" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == "0014_work_evaluations"


def test_ai_recommendation_response_migration_can_downgrade_cleanly(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "ai-recommendation-responses.db", monkeypatch)
    database_migrations.upgrade_database()
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    command.downgrade(config, "0015_weekly_coaching_reports")

    assert "source_decision_id" not in {
        column["name"]
        for column in inspect(engine).get_columns("adaptation_decisions")
    }
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == "0015_weekly_coaching_reports"


def test_practice_notebook_migration_preserves_vocabulary_review_state(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "practice-notebook.db", monkeypatch)
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "0008_vocabulary_review")
    with engine.begin() as connection:
        vocabulary = connection.exec_driver_sql(
            """
            INSERT INTO vocabulary_items (
                user_key, chunk, normalized_chunk, meaning, example_sentence,
                learned_on, personal_note, difficulty, mastery_status,
                source_resource_id, source_context, tags, favorite, saved_for_later,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "learner", "make an appointment", "make an appointment", "预约", "",
                "2026-09-12", "", "medium", "familiar", None, "Daily English",
                json.dumps([]), 0, 0, "2026-09-12 00:00:00", "2026-09-12 00:00:00",
            ),
        )
        connection.exec_driver_sql(
            """
            INSERT INTO review_items (
                user_key, item_type, vocabulary_item_id, scheduler_version,
                schedule_step, next_review_date, last_reviewed_at, review_count,
                active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "learner", "vocabulary", vocabulary.lastrowid, "fixed-interval-v1",
                2, "2026-09-19", "2026-09-12 00:00:00", 2, 1,
                "2026-09-12 00:00:00", "2026-09-12 00:00:00",
            ),
        )

    command.upgrade(config, "head")

    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT vocabulary_item_id, saved_sentence_id, mastery_status, review_count "
            "FROM review_items"
        ).one()
        assert tuple(row) == (vocabulary.lastrowid, None, "familiar", 2)
        assert "mastery_status" not in {
            column["name"] for column in inspect(engine).get_columns("vocabulary_items")
        }

    command.downgrade(config, "0008_vocabulary_review")

    with engine.connect() as connection:
        restored = connection.exec_driver_sql(
            "SELECT mastery_status FROM vocabulary_items"
        ).scalar_one()
        assert restored == "familiar"


def test_resource_library_migration_preserves_existing_resources(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "resource-library.db", monkeypatch)
    database_url = database_migrations.settings.database_url
    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "0009_practice_notebook")
    with engine.begin() as connection:
        resource = connection.exec_driver_sql(
            """
            INSERT INTO learning_resources (
                slug, title, resource_type, skill, topic, difficulty,
                estimated_duration_minutes, source_url, local_asset_reference,
                content, tags, priority, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "existing-listening-resource", "Existing listening", "audio",
                "listening", "Daily English", "intermediate", 20,
                "https://example.com/audio", None, json.dumps({}), json.dumps(["audio"]),
                60, 1, "2026-09-12 00:00:00", "2026-09-12 00:00:00",
            ),
        )
        resource_id = resource.lastrowid

    command.upgrade(config, "head")

    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT title, owner_user_key, description, transcript, notes "
            "FROM learning_resources WHERE id = ?",
            (resource_id,),
        ).one()
        assert tuple(row) == ("Existing listening", None, "", "", "")

    command.downgrade(config, "0009_practice_notebook")

    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT title FROM learning_resources WHERE id = ?", (resource_id,)
        ).scalar_one() == "Existing listening"


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
