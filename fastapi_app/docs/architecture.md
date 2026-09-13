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
- `presenters/ielts.py`: creates an IELTS workspace read model, including native table blocks, figure blocks, and grouped multi-answer questions.
- `domain/ielts/`: question types, grading result types, answer normalization and repository contract.
- `domain/learning_evidence/`: the four initial skills and typed, provider-neutral evidence records.
- `domain/learner_profile/`: `SkillEvaluator` interface, centralized configuration and deterministic baseline implementation.
- `domain/weakness_detection/`: `WeaknessDetector` interface, centralized thresholds and deterministic confirmation rules.
- `domain/resources/`: resource selection inputs and the replaceable `ResourceRecommender` contract.
- `domain/study_plan/`: date-based plan entities, time-allocation configuration and `StudyPlanGenerator` contract.
- `domain/adaptive_learning/`: explicit recommendation/override decision types and repository boundary.
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
- `models/ielts.py`: stable relational persistence concepts.
- `seed/g20_test1.json`: versioned, structured web content imported into SQLite.
- `templates/` and `static/`: accessible server-rendered screens plus small progressive JavaScript interactions.
- `migrations/`: Alembic schema history and the adopted pre-Alembic baseline.

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

The next planning layer will consume the assessment through its service API. It will not read assessment tables directly.

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
