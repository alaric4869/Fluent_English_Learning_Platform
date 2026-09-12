from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app import database_migrations
from app.database import Base
from app.models.ielts import PracticeAttempt, PracticeSet


EXPECTED_TABLES = {
    "alembic_version",
    "ielts_practice_attempts",
    "ielts_practice_questions",
    "ielts_practice_sections",
    "ielts_practice_sets",
}


def test_upgrade_database_creates_a_fresh_schema(tmp_path, monkeypatch) -> None:
    engine = _use_database(tmp_path / "fresh.db", monkeypatch)

    database_migrations.upgrade_database()

    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == (
            database_migrations.BASELINE_REVISION
        )


def test_upgrade_database_adopts_existing_schema_without_losing_attempts(
    tmp_path,
    monkeypatch,
) -> None:
    engine = _use_database(tmp_path / "existing.db", monkeypatch)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        practice_set = PracticeSet(
            slug="existing-listening",
            book_number=20,
            test_number=1,
            skill="listening",
            title="Existing",
            description="Existing learner data",
            duration_minutes=30,
            content_version="v1",
        )
        session.add(practice_set)
        session.flush()
        session.add(
            PracticeAttempt(
                practice_set_id=practice_set.id,
                user_key="local-learner",
                answers={"17": "A", "18": "E"},
            )
        )
        session.commit()

    database_migrations.upgrade_database()

    with Session(engine) as session:
        attempt = session.scalar(select(PracticeAttempt))
        assert attempt is not None
        assert attempt.answers == {"17": "A", "18": "E"}
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == (
            database_migrations.BASELINE_REVISION
        )


def _use_database(path, monkeypatch):
    database_url = f"sqlite:///{path}"
    engine = create_engine(database_url)
    monkeypatch.setattr(database_migrations, "engine", engine)
    monkeypatch.setattr(database_migrations.settings, "database_url", database_url)
    return engine
