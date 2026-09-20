# Adaptive English Learning Agent architecture

## Product boundary

The product is the adaptive loop, not an IELTS question bank:

```text
Study → Learning evidence → Learner profile → Weakness detection
      → Recommended plan + explanation → Study again
```

The G20 practice workspace is a content adapter and evidence producer. The feedback loop now consumes its submitted results, so validated Test 1–4 content can be imported without putting learning rules in the page or seed loader.

## Dependency direction

```text
Jinja pages / small browser interactions
        ↓
Focused application services
        ↓
Domain rules + repository protocols
        ↓
SQLAlchemy repository
        ↓
SQLite (local) / PostgreSQL (later)
```

The optional AI path follows the same direction:

```text
AIProvider → authorized typed Agent tools → application services
                                            ↓
                                  domain + repositories
```

The provider never receives a SQLAlchemy session, repository or learner identity from
model-generated arguments.

Templates never query the database and JavaScript never contains answer keys. Both HTML routes and API routes use the same application service. Domain rules have no FastAPI or SQLAlchemy dependency, so they can be tested independently.

## Current modules

- `api/routes/practice.py`: translates HTTP requests into use-case calls and safely streams approved local audio files.
- `api/routes/today.py`: renders today's persisted plan and exposes typed override/completion actions.
- `api/routes/listening.py`: renders the focused real-media/transcript workspace and exposes sentence-marking actions.
- `api/routes/speaking.py`: renders real-audio shadowing/retelling practice and exposes typed sentence, draft and submission actions.
- `api/routes/writing.py`: renders web-native IELTS tasks and exposes typed draft/submission actions.
- `api/routes/insights.py`: renders History and Progress from reporting services without querying tables.
- `api/routes/review.py`: renders the due queue/chunk library and validates typed create/rating requests.
- `api/routes/notebook.py`: renders notes, difficult sentences and retellings and exposes their typed write actions.
- `api/routes/resources.py`: owns Library reads and typed create/edit/user-state actions.
- `api/routes/dashboard.py`: renders composed Dashboard and current Weekly Review read models.
- `presenters/ielts.py`: creates an IELTS workspace read model, including native table blocks, figure blocks, and grouped multi-answer questions.
- `content_import/`: validates ordered manifests, complete 40-question IELTS sets, native tables/flowcharts/figures and grouped-answer invariants before a database write starts.
- `ai_agent/contracts.py`: strict provider, tool-input and tool-output Pydantic contracts.
- `ai_agent/tools.py`: allow-listed read tools that delegate only to application services.
- `ai_agent/authorization.py`: permission and per-tool allow-list enforcement.
- `ai_agent/provider.py` and `service.py`: provider protocol, offline mock and bounded model/tool loop.
- `ai_agent/capabilities.py`: replaceable recommendation/report interfaces with a deterministic mock seam.
- `domain/ai_evaluation/`: immutable learner-work evaluation contracts and provider/repository protocols.
- `services/ai_evaluation.py`: explicit Writing/Retelling evaluation use cases with input fingerprinting and idempotency.
- `integrations/openai/`: optional Responses function-calling and structured-output adapters; no provider SDK types cross this boundary.
- `repositories/sqlalchemy_ai_evaluation.py`: persists feedback separately from learner submissions and measured profile evidence.
- `presenters/today.py`: joins plan state with display-only resource and module information.
- `presenters/listening.py`: derives safe media presentation and stable transcript sentences without persistence.
- `presenters/speaking.py`: combines structured speaking content with learner sentence/draft state for display only.
- `presenters/writing.py`: builds the writing workspace view without scoring or database access.
- `domain/ielts/`: question types, grading result types, answer normalization and repository contract.
- `domain/learning_evidence/`: the five tracked skills and typed, provider-neutral evidence records.
- `domain/learner_profile/`: `SkillEvaluator` interface, centralized configuration and deterministic baseline implementation.
- `domain/weakness_detection/`: `WeaknessDetector` interface, centralized thresholds and deterministic confirmation rules.
- `domain/resources/`: resource selection inputs and the replaceable `ResourceRecommender` contract.
- `domain/study_plan/`: date-based plan entities, time-allocation configuration and `StudyPlanGenerator` contract.
- `domain/study_session/`: timed module-session lifecycle and repository contract.
- `domain/adaptive_learning/`: explicit recommendation/override decision types and repository boundary.
- `domain/history/`: persisted-session history read contracts.
- `domain/analytics/`: progress summaries and deterministic streak calculation.
- `domain/dashboard/` and `domain/weekly_review/`: composed read contracts and learner-local week calculations.
- `domain/vocabulary/`: chunk entities, mastery states and repository contract.
- `domain/review/`: scheduler contract, centralized intervals and deterministic fixed-interval implementation.
- `domain/listening/`, `domain/speaking/` and `domain/notebook/`: feature-specific records and repository contracts; none imports FastAPI or SQLAlchemy.
- `domain/writing/`: revisioned draft/submission contracts; it deliberately does not define a fake objective grader.
- `services/ielts_practice.py`: load practice, save an answer, require completion, grade and submit.
- `services/ielts_learning_evidence.py`: maps an IELTS result into generic learning evidence.
- `services/learning_evidence.py`: stable write use case for evidence producers.
- `services/study_session.py`: starts, resumes, saves and completes Today sessions, then refreshes adaptive evidence.
- `services/writing.py`: validates task content and drafts, submits immutable revisions and emits generic evidence.
- `services/speaking.py`: validates structured shadowing content, manages autosaved retellings and emits subjective speaking evidence.
- `repositories/sqlalchemy_ielts.py`: the only place that reads and writes IELTS database tables.
- `repositories/sqlalchemy_learning_evidence.py`: idempotently persists sessions, exercise attempts and skill performance.
- `repositories/sqlalchemy_learner_profile.py`: writes immutable profile snapshots and reads the latest profile.
- `repositories/sqlalchemy_weakness_detection.py`: writes idempotent assessment runs and reads the current classification.
- `repositories/sqlalchemy_resources.py`: reads active resources together with study and assignment history.
- `repositories/sqlalchemy_study_plan.py`: persists one plan per learner/date and its four independent items.
- `repositories/sqlalchemy_study_session.py`: persists revisioned active/completed module sessions and subjective performance evidence.
- `repositories/sqlalchemy_adaptive_learning.py`: atomically applies validated overrides and appends decision history.
- `repositories/sqlalchemy_history.py`: reads completed study sessions for timelines and analytics.
- `repositories/sqlalchemy_vocabulary.py`: persists normalized chunks together with their initial review item.
- `repositories/sqlalchemy_review.py`: reads the due queue and atomically appends idempotent review attempts.
- `repositories/sqlalchemy_listening.py`, `sqlalchemy_speaking.py` and `sqlalchemy_notebook.py`: persistence adapters for personal practice records; Speaking also owns sentence progress and immutable retelling submissions.
- `repositories/sqlalchemy_writing.py`: persists one autosaved draft and immutable submission revisions.
- `repositories/sqlalchemy_resources.py`: combines stable resource content, learner-specific state and derived study history without leaking SQL into pages.
- `models/ielts.py`: stable relational persistence concepts.
- `seed/manifest.json`: ordered catalogue of versioned IELTS tests and curated real-world resources.
- `seed/g20_test1.json` through `g20_test4.json`: proofread, structured web content imported into SQLite.
- `seed/australian_real_world.json`: official ABC/SBS audio, video, article and speaking-practice resources for daily rotation.
- `templates/` and `static/`: accessible server-rendered screens plus small progressive JavaScript interactions.
- `migrations/`: Alembic schema history and the adopted pre-Alembic baseline.
- `composition.py`: one explicit composition root so IELTS and Today use the same service graph.

## Implemented provider-neutral Agent boundary

`build_agent_tool_registry()` exposes nine read-only operations over the existing
service graph: plan, recent history, profile, weakness assessment, due reviews,
resource search/detail/recommendation and weekly report. Each tool has a generated
JSON Schema and rejects unknown fields. `user_key` is deliberately absent from every
tool input; `AgentExecutionContext` supplies it after authorization.

`LearningAgentService` gives a provider only the authorized catalogue, executes
validated tool calls, and returns their serialized contracts for the next provider
turn. Calls are bounded to prevent an unending model/tool loop. `MockAIProvider`
makes the whole path deterministic in tests. There is no browser chatbot or external
network call in this milestone; M17 can add an OpenAI Responses adapter without
changing any learning service or repository.

Read tools remain the default. `save_ai_recommendation` requires a separate permission
and appends a proposal without mutating the plan. Applying a proposal still requires
the existing explicit learner override path.

## Implemented optional AI evaluation

Writing and text Retelling pages can explicitly request structured coaching after a
submission. The provider is disabled by default, and submission never triggers a
network call. `OpenAIWorkEvaluator` uses structured output and `store=False`; the
result is saved as an immutable `WorkEvaluation` tied to the exact submission input.
It does not overwrite authored text, write objective accuracy or silently refresh the
learner profile. Text-only feedback cannot claim pronunciation or audio-fluency
assessment.

## Persistence safety

- Startup runs Alembic before importing content.
- A legacy database is stamped at the baseline only after its expected tables and columns are validated.
- Seed version changes update practice sets, sections, and questions in place. They do not delete learner attempts.
- Learner answers are serialized through one browser save queue because the current attempt schema stores an answer map as one JSON value.
- Future schema changes require a migration; `Base.metadata.create_all()` is not an application migration mechanism.

## Presentation boundary

Structured content contains semantic blocks such as `table`, `figure`, and question groups. The presenter turns those blocks into a rendering model. Jinja templates preserve the source layout using native HTML tables or approved source images, while answer inputs remain normal accessible form controls. Grading still works from question IDs and is independent of layout.

## Current limits

- A single local learner key is used until authentication is added.
- One working attempt is stored per learner and practice set. Attempt history and retakes will change this to multiple immutable submissions.
- G20 Test 1–4 Listening and Reading contain 40 web-interactive questions each, and all eight Writing tasks are web-native resources.
- Test 3's archaeological map is a verified crop from the learner-owned source. It is displayed as the original figure while its four answers remain ordinary autosaved form inputs.
- Current imported figures use a separate answer row. Coordinate overlays remain an optional later enhancement and must be visually checked per figure.

## Implemented learning-data pipeline

The IELTS grader remains independent. After it submits an attempt, an application-level observer translates the result:

```text
Submitted IELTS PracticeAttempt revision
        ↓
StudySession (one immutable learning activity)
        ↓
ExerciseAttempt × 40 + SkillPerformance
```

The conversion belongs in an application service and repository abstraction, not in a route, template, or JavaScript event handler. A unique source revision makes retries idempotent. Editing a submitted answer moves the practice attempt back to `in_progress`; the next submission creates a new revision while the previous session remains unchanged.

## Implemented learner profile pipeline

`LearnerProfileService` reads recent evidence for all five tracked skills and calls the replaceable `SkillEvaluator`. `RuleBasedSkillEvaluator` uses centrally configured weights and produces structured inputs, normalized weights, evidence sufficiency, trend and a numeric explanation. It deliberately does not classify skills as weak or strong.

Every snapshot stores the exact `SkillPerformance` IDs used to calculate it. A fingerprint of those IDs plus the algorithm version makes recalculation idempotent. When new evidence arrives, a new immutable snapshot is stored instead of overwriting the previous profile.

## Implemented weakness-detection pipeline

`WeaknessDetectionService` reads recent profile history through `LearnerProfileService` and calls the replaceable `WeaknessDetector`. The initial `RuleBasedWeaknessDetector` smooths the latest four profile scores and requires two consecutive threshold-confirming snapshots before assigning `weak` or `strong`. A single poor or excellent snapshot therefore cannot cause a sudden classification change.

Each immutable assessment run contains one result for every initial skill, the source profile snapshot IDs, actual observed metrics, threshold reasons, and a detector version. A fingerprint prevents duplicate runs when the same submission is retried. Missing or single-snapshot evidence is explicitly classified `insufficient_evidence`, not weak.

The planning and Progress layers consume the assessment through its service API. They do not read assessment tables directly.

## Implemented rule-based planning pipeline

`StudyPlanService` reads the latest assessment through `WeaknessDetectionService`, requests one candidate per skill through `ResourceService`, calls the replaceable `StudyPlanGenerator`, and persists the result through `StudyPlanRepository`.

```text
WeaknessAssessmentRun
        ↓
ResourceService → ResourceRecommender
        ↓
StudyPlanGenerator
        ↓
StudyPlan + four StudyPlanItems
```

The first request for a learner/date creates the plan; later reads return that same record. A new profile therefore does not silently rewrite an already assigned day. Every item stores the system duration and resource separately from the current values so the next milestone can preserve and explain manual overrides.

Resource rotation considers both completed `StudySession` history and resources assigned to prior plans. This avoids selecting yesterday's unfinished material again when another suitable candidate exists. If no resource exists, the item is retained with a `NULL` resource and an explicit reason rather than inventing content.

## Implemented adaptation-decision history

Creating a plan appends one `system_recommendation` decision per plan item. `AdaptationDecisionService` validates a requested duration against skill limits and verifies that a replacement resource is active and belongs to the same skill. The SQLAlchemy adapter then updates the current item values and plan total in the same transaction as a new `manual_override` decision.

The original system duration/resource never changes. Returning to those values clears the item's current override flag but still appends history, so the system can later answer whether and how recommendations were accepted. A repeated request with no value change is idempotent and does not create another decision.

## Implemented Today presentation

`GET /today` asks `StudyPlanService` for the Sydney calendar date, then passes its result and resource options to a presenter. The presenter contains labels and instructional copy but no persistence or adaptation rules. Jinja renders the established green/cream shell and four module cards.

Small browser interactions call typed endpoints for overrides and study sessions. The timer restores saved seconds, writes monotonically increasing duration, autosaves notes/ratings and completes explicitly. The completed session changes the plan item state, appends subjective performance evidence with `NULL` accuracy, and refreshes the profile/weakness services. A plan becomes complete only when all four items are complete, and reopening an item permits a new session revision. IELTS grading and Today state remain independent evidence producers.

## Implemented intensive-listening workspace

Listening resources resolve through `ResourceService`, then `ListeningPracticeService` validates learner visibility and skill before any sentence write. The presenter supports YouTube embeds, direct audio URLs and the existing private G20 section-audio route. Transcript text is split deterministically for display; marking a sentence creates or updates one learner/resource sentence record. `could_not_hear` and `difficult` ensure a review item exists, while hearing status and review mastery remain separate.

The workspace states when a resource has audio but no transcript instead of fabricating content. Personal resources can add a source URL and transcript through the existing Library editor. Provider fetching, automatic transcription and AI sentence analysis remain outside this milestone.

## Implemented History and Progress read models

`HistoryService` joins date-persisted plans with submitted study sessions at the application boundary. Its timeline is intentionally bounded, while its calendar queries the selected month so old records remain reachable. A day-detail page exposes the original assigned material, current completion state, manual-override marker and submitted evidence.

`ProgressAnalyticsService` calculates streaks, module completion, per-skill counts and a 28-day activity series from the same sources. The pure streak function is independent of FastAPI and SQLAlchemy. Existing `LearnerProfileService` and `WeaknessDetectionService` supply skill scores/classifications; Progress never recalculates a competing profile.

Plan completion minutes are an estimated workload measure, not elapsed study time. Only `StudySession.actual_duration_seconds` contributes to the tracked-time metric. This distinction is part of the service and page contract so later timer support can improve accuracy without rewriting analytics.

## Implemented vocabulary and review loop

`VocabularyService` normalizes and validates a complete chunk, rejects learner-local duplicates, optionally verifies its source resource, and asks the configured `ReviewScheduler` for its initial state. The SQLAlchemy adapter saves the chunk and first review item in one transaction.

`ReviewService` reads only active due items and passes their current structured state to `FixedIntervalReviewScheduler`. The scheduler has no FastAPI or database dependency. It returns the next step, date, interval and mastery state; the repository updates the current review item and appends an immutable `ReviewAttempt` in the same transaction.

Every rating request carries a UUID. Replaying the same UUID/rating returns the prior result without increasing the review count, while reusing it with a different rating is rejected. This protects the learning record from browser/network retries. Progress counts persisted review attempts through the repository contract rather than a UI counter.

## Implemented Notebook and multi-target review

Notebook stores three stable concepts rather than one generic JSON document: typed personal notes, saved listening sentences and speaking retelling records. Each record keeps an optional learning-resource reference plus a human-readable source context, so imported and manually entered material can coexist.

`ReviewItem` owns scheduling and mastery state and points to exactly one supported target. The `ReviewRepository` returns a provider-neutral `ReviewQueueItem`; routes resolve target content through `VocabularyService` or `ListeningPracticeService`. Consequently the scheduler and immutable attempts do not need a new code path for each future reviewable material type.

Listening sentence status describes hearing comprehension and is changed only by an explicit learner action. Review mastery describes recall scheduling and is changed only by a submitted review rating. Keeping these dimensions separate avoids a hidden side effect such as an `Easy` review silently changing a sentence to `mastered`.

Speaking retellings preserve the prompt, outline, intended chunks, optional written retelling, identified mistakes and improved version. Workspace-managed records autosave current state, while every explicit completion creates an immutable snapshot and generic subjective learning evidence. Sentence state is keyed by learner, resource and stable sentence key, so changing a label increments practice count without duplicating the sentence.

The browser plays the existing private G20 audio stream and renders proofread script excerpts from structured resource content. Hiding the transcript is a presentation action only. `voice_recording_reference` is nullable and currently remains empty; a later recording adapter can populate it without changing the core record or giving an AI provider raw database access.

## Implemented IELTS Writing workspace

Writing prompts are stored as structured `LearningResource.content`, so the browser renders real task text without loading the source PDF. `WritingPracticeService` validates the resource and word threshold, while the browser owns only timer display, word counting and autosave requests.

One `WritingDraft` retains current editable work. An explicit submit creates an immutable `WritingSubmission` revision and idempotent `StudySession`/`SkillPerformance` evidence. The evidence includes word count, active time and self-ratings with `NULL` accuracy. Future IELTS rubric evaluation will be a separate provider-neutral service and cannot overwrite the learner's original response.

The date rotation policy keeps Listening, Speaking and Vocabulary, then selects Reading or Writing for the fourth learning concern. It is deterministic and independently testable; existing saved daily plans remain unchanged.

## Implemented permanent Resource Library

`LearningResource` remains the stable content record already referenced by IELTS sets, plans and study sessions. Personal additions set `owner_user_key`; built-in resources keep it `NULL`. Rich text, transcript and personal resource notes are stored as explicit fields instead of being embedded in the current Library card layout.

`ResourceUserState` is a separate learner/resource relation containing favorite, saved-for-later and archived state. Archiving is recoverable and user-scoped. Candidate selection excludes that learner's archived resources while old `StudyPlanItem` and `StudySession` foreign keys continue to resolve, so organizing the Library cannot erase history.

`ResourceService` validates and normalizes all writes. The Library route uses typed filters for skill, type, topic, difficulty, completion and sorting. Completion and recent-study values are derived from `StudySession`; the UI does not maintain a competing counter. Only user-owned resources can be edited, because built-in seed resources are synchronized from versioned content at startup.

## Implemented Dashboard and Weekly Review

`DashboardService` composes `StudyPlanService`, `ProgressAnalyticsService`, `ReviewService` and `WeeklyReviewService`. It does not receive a database session and does not duplicate their calculations. Opening the Dashboard creates today's idempotent plan when needed, then presents one focused overview of the existing facts.

`WeeklyReviewService` reads plans, study sessions, vocabulary, saved listening sentences and review attempts through repository protocols. Week boundaries use the learner's Sydney timezone and current-week queries stop at the end of today. Skill highlights compare only skills with submitted-session accuracy; unknown performance remains unknown.

The review retention metric means `(Good + Easy) / all ratings recorded this week`. It is not labelled as historical due-item completion because mutable current schedules cannot prove how many items were due on an earlier day. A future event/snapshot can add that metric without changing the existing report contract.
