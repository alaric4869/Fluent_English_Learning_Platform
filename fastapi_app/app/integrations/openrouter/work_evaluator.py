import json

from app.domain.ai_evaluation.entities import (
    GeneratedWorkEvaluation,
    WorkEvaluationRequest,
)
from app.integrations.openai.work_evaluator import (
    InvalidStructuredEvaluationError,
    OpenAIWorkEvaluator,
    WorkEvaluationOutput,
    evaluation_instructions,
)
from app.integrations.openrouter.client import (
    OpenRouterClient,
    build_openrouter_client,
    is_transient_openrouter_error,
    require_free_model,
)


class OpenRouterWorkEvaluator(OpenAIWorkEvaluator):
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
        free_model = require_free_model(model)
        normalized_fallback = require_free_model(fallback_model)
        super().__init__(
            model=free_model,
            max_output_tokens=max_output_tokens,
            client=client or build_openrouter_client(api_key),
        )
        self.models = tuple(dict.fromkeys((free_model, normalized_fallback)))

    def evaluate(self, request: WorkEvaluationRequest) -> GeneratedWorkEvaluation:
        request_options = {
            "messages": [
                {"role": "system", "content": evaluation_instructions(request)},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task_prompt": request.task_prompt,
                            "learner_text": request.learner_text,
                            "supporting_context": request.supporting_context,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": WorkEvaluationOutput,
            "max_tokens": self.max_output_tokens,
        }
        completion = self._create_completion(request_options)
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise InvalidStructuredEvaluationError(
                "OpenRouter returned no structured evaluation"
            )
        return self.build_result(parsed, model_name=str(completion.model))

    def _create_completion(self, request_options: dict[str, object]):
        last_error: Exception | None = None
        for model in self.models:
            try:
                return self.client.chat.completions.parse(
                    **{**request_options, "model": model}
                )
            except Exception as error:
                if not is_transient_openrouter_error(error):
                    raise
                last_error = error
        assert last_error is not None
        raise last_error
