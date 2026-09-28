import json

from app.ai_agent.contracts import (
    AIProviderRequest,
    AIProviderResponse,
    AgentToolDefinition,
    ProviderToolCall,
)
from app.integrations.openrouter.client import (
    OpenRouterClient,
    build_openrouter_client,
    is_transient_openrouter_error,
    require_free_model,
)


class OpenRouterChatProvider:
    """OpenRouter adapter with local, request-scoped tool conversation state."""

    provider_name = "openrouter"

    def __init__(
        self,
        *,
        model: str,
        fallback_model: str = "openrouter/free",
        api_key: str | None = None,
        max_output_tokens: int = 2000,
        client: OpenRouterClient | None = None,
    ) -> None:
        self.model = require_free_model(model)
        normalized_fallback = require_free_model(fallback_model)
        self.models = tuple(dict.fromkeys((self.model, normalized_fallback)))
        if not 256 <= max_output_tokens <= 8192:
            raise ValueError("max_output_tokens must be between 256 and 8192")
        self.max_output_tokens = max_output_tokens
        self.client = client or build_openrouter_client(api_key)
        self._conversations: dict[str, list[dict[str, object]]] = {}

    def respond(self, request: AIProviderRequest) -> AIProviderResponse:
        messages = self._messages_for(request)
        request_options: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_output_tokens,
        }
        if request.tools:
            request_options.update(
                tools=[_chat_tool(item) for item in request.tools],
                tool_choice="auto",
                parallel_tool_calls=False,
            )
        response = self._create_completion(request_options)
        choice = response.choices[0]
        message = choice.message
        raw_tool_calls = tuple(message.tool_calls or ())
        tool_calls = tuple(_provider_tool_call(item) for item in raw_tool_calls)
        output_text = _message_text(message.content)
        response_id = str(response.id)

        assistant_message: dict[str, object] = {
            "role": "assistant",
            "content": output_text,
        }
        if raw_tool_calls:
            assistant_message["tool_calls"] = [
                _serialized_tool_call(item) for item in raw_tool_calls
            ]
        reasoning_details = getattr(message, "reasoning_details", None)
        if reasoning_details:
            assistant_message["reasoning_details"] = reasoning_details
        self._conversations[response_id] = [*messages, assistant_message]

        return AIProviderResponse(
            response_id=response_id,
            output_text=output_text,
            tool_calls=tool_calls,
        )

    def _create_completion(self, request_options: dict[str, object]):
        last_error: Exception | None = None
        for model in self.models:
            try:
                return self.client.chat.completions.create(
                    **{**request_options, "model": model}
                )
            except Exception as error:
                if not is_transient_openrouter_error(error):
                    raise
                last_error = error
        assert last_error is not None
        raise last_error

    def _messages_for(self, request: AIProviderRequest) -> list[dict[str, object]]:
        if request.previous_response_id is None:
            return [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ]
        previous = self._conversations.get(request.previous_response_id)
        if previous is None:
            raise OpenRouterConversationStateError(
                "The previous OpenRouter response is not available in this run"
            )
        messages = [dict(item) for item in previous]
        messages.extend(
            {
                "role": "tool",
                "tool_call_id": result.call_id,
                "content": json.dumps(
                    result.output,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            }
            for result in request.tool_results
        )
        return messages


def _chat_tool(definition: AgentToolDefinition) -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": definition.name.value,
            "description": definition.description,
            "parameters": definition.input_schema,
            "strict": False,
        },
    }


def _provider_tool_call(item) -> ProviderToolCall:
    raw_arguments = item.function.arguments
    try:
        arguments = json.loads(raw_arguments)
    except (TypeError, json.JSONDecodeError) as error:
        raise InvalidOpenRouterToolCallError(
            "OpenRouter returned invalid tool JSON"
        ) from error
    if not isinstance(arguments, dict):
        raise InvalidOpenRouterToolCallError(
            "OpenRouter tool arguments must be an object"
        )
    return ProviderToolCall(
        call_id=str(item.id),
        name=str(item.function.name),
        arguments=arguments,
    )


def _serialized_tool_call(item) -> dict[str, object]:
    return {
        "id": str(item.id),
        "type": "function",
        "function": {
            "name": str(item.function.name),
            "arguments": str(item.function.arguments),
        },
    }


def _message_text(content) -> str | None:
    if isinstance(content, str):
        return content.strip() or None
    if isinstance(content, list):
        parts = [
            str(getattr(item, "text", "")).strip()
            for item in content
            if getattr(item, "text", None)
        ]
        return "\n".join(parts) or None
    return None


class OpenRouterConversationStateError(RuntimeError):
    pass


class InvalidOpenRouterToolCallError(RuntimeError):
    pass
