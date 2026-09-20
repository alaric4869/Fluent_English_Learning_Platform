import json
from typing import Protocol

from app.ai_agent.contracts import (
    AIProviderRequest,
    AIProviderResponse,
    AgentToolDefinition,
    ProviderToolCall,
)


class ResponsesClient(Protocol):
    @property
    def responses(self):
        ...


class OpenAIResponsesProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        client: ResponsesClient | None = None,
    ) -> None:
        normalized_model = model.strip()
        if not normalized_model:
            raise ValueError("An OpenAI model must be configured")
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise OpenAIProviderConfigurationError(
                    "Install the optional AI dependency with: pip install -e '.[ai]'"
                ) from error
            if not api_key:
                raise OpenAIProviderConfigurationError(
                    "OPENAI_API_KEY is required for the OpenAI provider"
                )
            client = OpenAI(api_key=api_key)
        self.model = normalized_model
        self.client = client

    def respond(self, request: AIProviderRequest) -> AIProviderResponse:
        response = self.client.responses.create(
            model=self.model,
            instructions=request.system_prompt,
            input=_response_input(request),
            tools=[_function_tool(item) for item in request.tools],
            previous_response_id=request.previous_response_id,
            parallel_tool_calls=False,
            store=False,
        )
        calls = tuple(
            _provider_tool_call(item)
            for item in response.output
            if _value(item, "type") == "function_call"
        )
        return AIProviderResponse(
            response_id=str(response.id),
            output_text=(str(response.output_text).strip() or None),
            tool_calls=calls,
        )


def _response_input(request: AIProviderRequest):
    if not request.tool_results:
        return request.user_prompt
    return [
        {
            "type": "function_call_output",
            "call_id": result.call_id,
            "output": json.dumps(
                result.output,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
        for result in request.tool_results
    ]


def _function_tool(definition: AgentToolDefinition) -> dict[str, object]:
    return {
        "type": "function",
        "name": definition.name.value,
        "description": definition.description,
        "parameters": definition.input_schema,
        # Pydantic validates every call again inside our process. False permits
        # optional/defaulted fields while retaining a closed object schema.
        "strict": False,
    }


def _provider_tool_call(item) -> ProviderToolCall:
    raw_arguments = _value(item, "arguments")
    try:
        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    except json.JSONDecodeError as error:
        raise InvalidOpenAIToolCallError("OpenAI returned invalid tool JSON") from error
    if not isinstance(arguments, dict):
        raise InvalidOpenAIToolCallError("OpenAI tool arguments must be an object")
    return ProviderToolCall(
        call_id=str(_value(item, "call_id")),
        name=str(_value(item, "name")),
        arguments=arguments,
    )


def _value(item, field: str):
    if isinstance(item, dict):
        return item.get(field)
    return getattr(item, field, None)


class OpenAIProviderConfigurationError(RuntimeError):
    pass


class InvalidOpenAIToolCallError(RuntimeError):
    pass
