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
- `get_today_plan()` / `create_daily_plan()` / `update_daily_plan()` → `StudyPlanService` and `AdaptationDecisionService`
- `get_recent_study_history(days)` → future `HistoryService`
- `get_due_reviews()` → future `ReviewService`
- `save_ai_recommendation()` → `AdaptationDecisionService` after an AI-specific command contract is added
- `generate_weekly_report()` → future `ProgressAnalyticsService`

Request and response schemas will be explicit Pydantic contracts at the tool boundary. Provider-specific SDK objects will be contained behind an `AIProvider` interface; the domain will not import OpenAI, Anthropic, Gemini or another vendor SDK.

## Replacement strategy

The existing `SkillEvaluator`, `WeaknessDetector`, `ResourceRecommender` and `StudyPlanGenerator` interfaces are deterministic baselines. AI implementations may be added alongside them, selected by configuration, and compared using stored algorithm versions and evidence IDs. The UI and persistence layer should not need to change when a rule-based strategy is supplemented or replaced.

The current `AdaptationDecisionService` accepts validated learner overrides only. A future AI action must use a separate typed command and actor value instead of impersonating a user override.
