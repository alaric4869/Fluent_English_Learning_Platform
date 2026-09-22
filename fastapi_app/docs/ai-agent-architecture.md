# Future AI agent architecture

## Boundary

An AI agent will call application services and typed tool adapters. It will never receive a database session or unrestricted table access. Learning-domain logic must remain usable without an AI provider.

```text
Agent tool adapter
        ↓
Application services
        ↓
Domain policies and repository protocols
        ↓
SQLAlchemy / external integration adapters
```

## Tools and service owners

- `get_skill_profile()` → `LearnerProfileService`
- `get_weak_skills()` → `WeaknessDetectionService`
- `search_learning_resources(filters)` → `ResourceService`
- `get_resource(resource_id)` / `recommend_resources(...)` → `ResourceService`; write access remains limited to validated service commands
- `get_today_plan()` / `create_daily_plan()` / `update_daily_plan()` → `StudyPlanService` and `AdaptationDecisionService`
- `start_study_session()` / `save_study_progress()` / `complete_study_session()` → `StudySessionService`
- `get_recent_study_history(days)` → `HistoryService`
- `get_due_reviews()` → `ReviewService`
- `get_recent_mistakes()` → `NotebookService`, `ListeningPracticeService` and `SpeakingPracticeService` through a future read-only tool adapter
- `save_ai_recommendation()` → `AdaptationDecisionService`; it appends a non-applied recommendation under a separate permission
- `generate_weekly_report()` → `WeeklyReviewService`; a future AI layer may explain its typed evidence but must not replace the measured values

Request and response schemas will be explicit Pydantic contracts at the tool boundary. Provider-specific SDK objects will be contained behind an `AIProvider` interface; the domain will not import OpenAI, Anthropic, Gemini or another vendor SDK.

## Implemented M16 boundary

The first boundary is available in `app/ai_agent`:

- `AIProvider` contains the only model-runtime dependency seam; `MockAIProvider` runs fully offline.
- `LearningAgentService` performs a bounded model/tool loop.
- `AgentToolRegistry` validates every argument and checks authorization before dispatch.
- `AgentExecutionContext` owns the learner key, so a model cannot select another learner by adding `user_key` to an argument.
- `build_agent_tool_registry()` wires tools to existing application services, not repositories.
- recommendation and weekly-narrative generation have provider-neutral protocols and a deterministic mock for the next milestone.

The default catalogue is intentionally read-only: `get_today_plan`,
`get_recent_study_history`, `get_skill_profile`, `get_due_reviews`,
`get_weak_skills`, `search_learning_resources`, `get_resource`,
`recommend_resources` and `generate_weekly_report`. A missing profile or plan is
returned explicitly and never created as a hidden side effect.

M17 adds `save_ai_recommendation` under `SAVE_AI_RECOMMENDATION`, which is not
granted to a normal read principal. Its validated command records proposed time,
resource, evidence reasons, provider and model without mutating `StudyPlanItem`.

## Recommended first provider

Use the OpenAI Responses API (`POST /responses`) as the first production adapter. It supports custom function tools, so `OpenAIProvider` can present a small allow-listed tool catalogue and return structured tool calls to `AgentService`. The service validates every argument with Pydantic and invokes the existing application services; the model never receives a SQLAlchemy session or database credentials.

Start M16 with `MockAIProvider`, typed tool contracts and deterministic authorization tests. Add the networked `OpenAIProvider` only after the tool boundary is stable. The API key remains a server-side environment variable and is never sent to templates or browser JavaScript. If another provider is added later, it implements the same `AIProvider` contract; learning-domain code and pages remain unchanged.

The first user-facing Agent action lives on Weekly Review. It is not a free-form chat:
the server supplies a fixed coaching objective and an allow-list containing only
`generate_weekly_report`, `get_skill_profile`, `get_weak_skills` and
`get_due_reviews`. All four calls are required before output can be persisted. Saved
coaching text remains separate from measured evidence and cannot update a study plan.

The second explicit action lives on Today. `AgentPlanningService` requires the Agent to
read the existing plan, profile, weakness assessment and due reviews before it may call
the separately authorized `save_ai_recommendation` tool. The tool can only append a
proposal. Today renders its evidence and before/after values, and only a learner action
can accept or dismiss it. That response is linked back to the proposal; an accepted
change and its audit decision are committed together. Old or already answered proposals
cannot be applied.

`OpenAIResponsesProvider` now implements the same protocol using custom function
tools, `previous_response_id`, non-parallel calls and `store=False`. The OpenAI SDK is
an optional dependency and is imported only when the provider is explicitly enabled.

The OpenAI Agents SDK is optional. It can be introduced later for richer tracing or multi-agent handoffs, but the core application should not depend on its runtime types. The Responses API is sufficient for the initial model-and-tools loop.

## Replacement strategy

The existing `SkillEvaluator`, `WeaknessDetector`, `ResourceRecommender` and `StudyPlanGenerator` interfaces are deterministic baselines. AI implementations may be added alongside them, selected by configuration, and compared using stored algorithm versions and evidence IDs. The UI and persistence layer should not need to change when a rule-based strategy is supplemented or replaced.

## Structured learner-work evaluation

`LearningWorkEvaluationService` builds an immutable request from a specific Writing
or Retelling submission snapshot. `WorkEvaluator` remains provider-neutral;
`MockWorkEvaluator` verifies the path offline and `OpenAIWorkEvaluator` uses Responses
structured output. The provider returns a 0–100 coaching score, rubric evidence,
strengths, priorities, corrections and a suggested revision. It is explicitly
instructed not to claim an official IELTS/PTE Band or infer pronunciation from text.

`WorkEvaluation` stores this output in a separate table keyed by submission revision,
evaluator version and input fingerprint. It never changes learner-authored work,
objective accuracy, profile evidence or a saved plan. Repeated evaluation of the same
version is idempotent and does not incur another provider call.
