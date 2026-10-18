from typing import Protocol


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
FREE_MODEL_SUFFIX = ":free"
FREE_ROUTER_MODEL = "openrouter/free"


class OpenRouterClient(Protocol):
    @property
    def chat(self):
        ...


def require_free_model(model: str) -> str:
    normalized = model.strip()
    if not normalized:
        raise ValueError("An OpenRouter model must be configured")
    if not (
        normalized.endswith(FREE_MODEL_SUFFIX)
        or normalized == FREE_ROUTER_MODEL
    ):
        raise ValueError(
            "OpenRouter is restricted to an explicit :free model in this application"
        )
    return normalized


def build_openrouter_client(api_key: str | None) -> OpenRouterClient:
    try:
        from openai import OpenAI
    except ImportError as error:
        raise OpenRouterConfigurationError(
            "Install the optional AI dependency with: pip install -e '.[ai]'"
        ) from error
    if not api_key:
        raise OpenRouterConfigurationError(
            "OPENROUTER_API_KEY is required for the OpenRouter provider"
        )
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        # The adapter owns one bounded free-only fallback. SDK retries would
        # otherwise wait on the same saturated upstream before that fallback.
        max_retries=0,
    )


def is_transient_openrouter_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    return status_code in {429, 500, 502, 503, 504} or (
        error.__class__.__name__ == "APIConnectionError"
    )


class OpenRouterConfigurationError(RuntimeError):
    pass
