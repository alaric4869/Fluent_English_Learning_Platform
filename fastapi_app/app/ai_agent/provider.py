from collections import deque
from typing import Protocol

from app.ai_agent.contracts import AIProviderRequest, AIProviderResponse


class AIProvider(Protocol):
    @property
    def provider_name(self) -> str:
        ...

    def respond(self, request: AIProviderRequest) -> AIProviderResponse:
        ...


class MockAIProvider:
    """Deterministic provider used to test the model-and-tools loop offline."""

    provider_name = "mock"

    def __init__(self, responses: tuple[AIProviderResponse, ...]) -> None:
        self._responses = deque(responses)
        self.requests: list[AIProviderRequest] = []

    def respond(self, request: AIProviderRequest) -> AIProviderResponse:
        self.requests.append(request)
        if not self._responses:
            raise RuntimeError("MockAIProvider has no scripted response remaining")
        return self._responses.popleft()
