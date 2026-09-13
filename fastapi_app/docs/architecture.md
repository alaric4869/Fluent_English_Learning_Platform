# Adaptive English Learning Agent architecture

## Product boundary

The product is the adaptive loop, not an IELTS question bank:

```text
Study → Learning evidence → Learner profile → Weakness detection
      → Recommended plan + explanation → Study again
```

The current G20 practice workspace is a content adapter and evidence producer. Bulk content import is intentionally paused until the loop can consume its results.

## Dependency direction

```text
Jinja pages / small browser interactions
        ↓
Application services (currently IeltsPracticeService)
        ↓
Domain rules + repository protocols
        ↓
SQLAlchemy repository
        ↓
SQLite (local) / PostgreSQL (later)
```

Templates never query the database and JavaScript never contains answer keys. Both HTML routes and API routes use the same application service. Domain rules have no FastAPI or SQLAlchemy dependency, so they can be tested independently.

## Current modules

- `api/routes/practice.py`: translates HTTP requests into use-case calls and safely streams approved local audio files.
- `api/routes/today.py`: renders today's persisted plan and exposes typed override/completion actions.
- `api/routes/insights.py`: renders History and Progress from reporting services without querying tables.
- `api/routes/review.py`: renders the due queue/chunk library and validates typed create/rating requests.
- `api/routes/notebook.py`: renders notes, difficult sentences and retellings and exposes their typed write actions.
- `presenters/ielts.py`: creates an IELTS workspace read model, including native table blocks, figure blocks, and grouped multi-answer questions.
- `presenters/today.py`: joins plan state with display-only resource and module information.
- `domain/ielts/`: question types, grading result types, answer normalization and repository contract.
- `domain/learning_evidence/`: the four initial skills and typed, provider-neutral evidence records.
- `domain/learner_profile/`: `SkillEvaluator` interface, centralized configuration and deterministic baseline implementation.
- `domain/weakness_detection/`: `WeaknessDetector` interface, centralized thresholds and deterministic confirmation rules.
- `domain/resources/`: resource selection inputs and the replaceable `ResourceRecommender` contract.
- `domain/study_plan/`: date-based plan entities, time-allocation configuration and `StudyPlanGenerator` contract.
- `domain/adaptive_learning/`: explicit recommendation/override decision types and repository boundary.
- `domain/history/`: persisted-session history read contracts.
- `domain/analytics/`: progress summaries and deterministic streak calculation.
- `domain/vocabulary/`: chunk entities, mastery states and repository contract.
- `domain/review/`: scheduler contract, centralized intervals and deterministic fixed-interval implementation.
- `domain/listening/`, `domain/speaking/` and `domain/notebook/`: feature-specific records and repository contracts; none imports FastAPI or SQLAlchemy.
- `services/ielts_practice.py`: load practice, save an answer, require completion, grade and submit.
- `services/ielts_learning_evidence.py`: maps an IELTS result into generic learning evidence.
- `services/learning_evidence.py`: stable write use case for evidence producers.
- `repositories/sqlalchemy_ielts.py`: the only place that reads and writes IELTS database tables.
- `repositories/sqlalchemy_learning_evidence.py`: idempotently persists sessions, exercise attempts and skill performance.
- `repositories/sqlalchemy_learner_profile.py`: writes immutable profile snapshots and reads the latest profile.
- `repositories/sqlalchemy_weakness_detection.py`: writes idempotent assessment runs and reads the current classification.
- `repositories/sqlalchemy_resources.py`: reads active resources together with study and assignment history.
- `repositories/sqlalchemy_study_plan.py`: persists one plan per learner/date and its four independent items.
- `repositories/sqlalchemy_adaptive_learning.py`: atomically applies validated overrides and appends decision history.
- `repositories/sqlalchemy_history.py`: reads submitted study sessions for timelines and analytics.
- `repositories/sqlalchemy_vocabulary.py`: persists normalized chunks together with their initial review item.
- `repositories/sqlalchemy_review.py`: reads the due queue and atomically appends idempotent review attempts.
- `repositories/sqlalchemy_listening.py`, `sqlalchemy_speaking.py` and `sqlalchemy_notebook.py`: persistence adapters for personal practice records.
- `models/ielts.py`: stable relational persistence concepts.
- `seed/g20_test1.json`: versioned, structured web content imported into SQLite.
- `templates/` and `static/`: accessible server-rendered screens plus small progressive JavaScript interactions.
- `migrations/`: Alembic schema history and the adopted pre-Alembic baseline.
- `composition.py`: one explicit composition root so IELTS and Today use the same service graph.

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
- Only G20 Test 1 Listening and Reading have been curated and quality checked.
- G20 Test 1 has no map question. The figure block preserves a verified crop and answer association; coordinate overlays should be added and visually checked when a real map resource is curated.

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

`LearnerProfileService` reads recent evidence for all four initial skills and calls the replaceable `SkillEvaluator`. `RuleBasedSkillEvaluator` uses centrally configured weights and produces structured inputs, normalized weights, evidence sufficiency, trend and a numeric explanation. It deliberately does not classify skills as weak or strong.

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

Small browser interactions call typed endpoints for an override or status change. The override endpoint delegates to `AdaptationDecisionService`; the status endpoint delegates to `StudyPlanService`. A plan becomes complete only when all four items are complete, and reopening any item makes the plan active again. IELTS grading and Today state remain independent use cases connected through the generic evidence pipeline.

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

Speaking retellings preserve the prompt, outline, intended chunks, identified mistakes and improved version. `voice_recording_reference` is nullable and currently remains empty; adding recording later does not require reshaping existing records.
