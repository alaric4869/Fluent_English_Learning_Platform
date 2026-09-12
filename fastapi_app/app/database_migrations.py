from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.config import FASTAPI_ROOT, settings
from app.database import engine


BASELINE_REVISION = "0001_ielts_baseline"
BASELINE_TABLE_COLUMNS = {
    "ielts_practice_sets": {"id", "slug", "content_version"},
    "ielts_practice_sections": {"id", "practice_set_id", "order_index"},
    "ielts_practice_questions": {"id", "practice_set_id", "section_id", "number"},
    "ielts_practice_attempts": {"id", "practice_set_id", "user_key", "answers"},
}


def upgrade_database() -> None:
    """Upgrade new databases and safely adopt the pre-Alembic local schema."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    known_tables = set(BASELINE_TABLE_COLUMNS)
    existing_known_tables = tables & known_tables

    config = Config(FASTAPI_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

    if "alembic_version" not in tables and existing_known_tables:
        if existing_known_tables != known_tables:
            missing = ", ".join(sorted(known_tables - existing_known_tables))
            raise RuntimeError(f"Cannot adopt incomplete IELTS schema; missing tables: {missing}")
        _validate_baseline_columns(inspector)
        command.stamp(config, BASELINE_REVISION)

    command.upgrade(config, "head")


def _validate_baseline_columns(inspector) -> None:
    for table, expected_columns in BASELINE_TABLE_COLUMNS.items():
        actual_columns = {column["name"] for column in inspector.get_columns(table)}
        missing = expected_columns - actual_columns
        if missing:
            names = ", ".join(sorted(missing))
            raise RuntimeError(f"Cannot adopt {table}; missing columns: {names}")
