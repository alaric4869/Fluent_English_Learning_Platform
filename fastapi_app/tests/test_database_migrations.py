import json

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app import database_migrations
from app.config import FASTAPI_ROOT
from app.models.ielts import PracticeAttempt


EXPECTED_TABLES = {
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
    "weakness_assessment_runs",
    "weakness_skill_assessments",
}
HEAD_REVISION = "0004_weakness_assessments"


def test_upgrade_database_creates_a_fresh_schema(tmp_path, monkeypatch) -> None:
    engine = _use_database(tmp_path / "fresh.db", monkeypatch)

    database_migrations.upgrade_database()

    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
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
