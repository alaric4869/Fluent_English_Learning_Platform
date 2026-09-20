from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


FASTAPI_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = FASTAPI_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Fluent Daily English"
    database_url: str = f"sqlite:///{FASTAPI_ROOT / 'data' / 'english_learning.db'}"
    seed_path: Path = FASTAPI_ROOT / "seed" / "manifest.json"
    resources_root: Path = REPOSITORY_ROOT / "resources"
    ielts_assets_root: Path = FASTAPI_ROOT / "assets" / "ielts"
    ai_provider: Literal["disabled", "openai"] = "disabled"
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "OPENAI_API_KEY",
            "ENGLISH_TOOL_OPENAI_API_KEY",
        ),
    )
    openai_model: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OPENAI_MODEL",
            "ENGLISH_TOOL_OPENAI_MODEL",
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="ENGLISH_TOOL_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
