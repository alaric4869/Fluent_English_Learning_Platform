from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


FASTAPI_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = FASTAPI_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Fluent Daily English"
    database_url: str = f"sqlite:///{FASTAPI_ROOT / 'data' / 'english_learning.db'}"
    seed_path: Path = FASTAPI_ROOT / "seed" / "g20_test1.json"
    resources_root: Path = REPOSITORY_ROOT / "resources"

    model_config = SettingsConfigDict(env_prefix="ENGLISH_TOOL_", env_file=".env")


settings = Settings()

