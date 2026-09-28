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
    local_user_key: str = "local-user"
    ai_provider: Literal["disabled", "openai", "openrouter"] = "disabled"
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
    openai_max_output_tokens: int = Field(
        default=2000,
        ge=256,
        le=8192,
        validation_alias=AliasChoices(
            "OPENAI_MAX_OUTPUT_TOKENS",
            "ENGLISH_TOOL_OPENAI_MAX_OUTPUT_TOKENS",
        ),
    )
    openrouter_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "OPENROUTER_API_KEY",
            "ENGLISH_TOOL_OPENROUTER_API_KEY",
            # Compatibility for the first local setup, where an OpenRouter key
            # may already have been entered in the former single-provider slot.
            "OPENAI_API_KEY",
        ),
    )
    openrouter_model: str = Field(
        default="qwen/qwen3.8-27b:free",
        validation_alias=AliasChoices(
            "OPENROUTER_MODEL",
            "ENGLISH_TOOL_OPENROUTER_MODEL",
        ),
    )
    openrouter_fallback_model: str = Field(
        default="openrouter/free",
        validation_alias=AliasChoices(
            "OPENROUTER_FALLBACK_MODEL",
            "ENGLISH_TOOL_OPENROUTER_FALLBACK_MODEL",
        ),
    )
    openrouter_max_output_tokens: int = Field(
        default=2000,
        ge=256,
        le=8192,
        validation_alias=AliasChoices(
            "OPENROUTER_MAX_OUTPUT_TOKENS",
            "ENGLISH_TOOL_OPENROUTER_MAX_OUTPUT_TOKENS",
            "OPENAI_MAX_OUTPUT_TOKENS",
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="ENGLISH_TOOL_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
