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

## Planned tools and service owners

- `get_skill_profile()` → `LearnerProfileService`
- `get_weak_skills()` → `WeaknessDetectionService`
- `search_learning_resources(filters)` → `ResourceService`
- `get_resource(resource_id)` / `recommend_resources(...)` → `ResourceService`; write access remains limited to validated service commands
- `get_today_plan()` / `create_daily_plan()` / `update_daily_plan()` → `StudyPlanService` and `AdaptationDecisionService`
- `start_study_session()` / `save_study_progress()` / `complete_study_session()` → `StudySessionService`
- `get_recent_study_history(days)` → `HistoryService`
- `get_due_reviews()` → `ReviewService`
- `get_recent_mistakes()` → `NotebookService`, `ListeningPracticeService` and `SpeakingPracticeService` through a future read-only tool adapter
- `save_ai_recommendation()` → `AdaptationDecisionService` after an AI-specific command contract is added
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

The implemented catalogue is intentionally read-only: `get_today_plan`,
`get_recent_study_history`, `get_skill_profile`, `get_due_reviews`,
`get_weak_skills`, `search_learning_resources`, `get_resource`,
`recommend_resources` and `generate_weekly_report`. A missing profile or plan is
returned explicitly and never created as a hidden side effect.

## Recommended first provider

Use the OpenAI Responses API (`POST /responses`) as the first production adapter. It supports custom function tools, so `OpenAIProvider` can present a small allow-listed tool catalogue and return structured tool calls to `AgentService`. The service validates every argument with Pydantic and invokes the existing application services; the model never receives a SQLAlchemy session or database credentials.

Start M16 with `MockAIProvider`, typed tool contracts and deterministic authorization tests. Add the networked `OpenAIProvider` only after the tool boundary is stable. The API key remains a server-side environment variable and is never sent to templates or browser JavaScript. If another provider is added later, it implements the same `AIProvider` contract; learning-domain code and pages remain unchanged.

M16 now provides that mock boundary. M17 is the first appropriate milestone for a
networked `OpenAIProvider`, rubric evaluation and AI-supplemented planning.

The OpenAI Agents SDK is optional. It can be introduced later for richer tracing or multi-agent handoffs, but the core application should not depend on its runtime types. The Responses API is sufficient for the initial model-and-tools loop.

## Replacement strategy

The existing `SkillEvaluator`, `WeaknessDetector`, `ResourceRecommender` and `StudyPlanGenerator` interfaces are deterministic baselines. AI implementations may be added alongside them, selected by configuration, and compared using stored algorithm versions and evidence IDs. The UI and persistence layer should not need to change when a rule-based strategy is supplemented or replaced.

The current `AdaptationDecisionService` accepts validated learner overrides only. A future AI action must use a separate typed command and actor value instead of impersonating a user override.
