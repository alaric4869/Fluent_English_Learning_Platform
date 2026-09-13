# Current and planned data model

## Implemented IELTS resource slice

- `PracticeSet`: one book/test/skill combination, such as G20 Test 1 Listening.
- `PracticeSection`: one Listening Part or Reading Section; owns instructions, passage blocks and an optional private audio path.
- `PracticeQuestion`: prompt, type, choices, accepted answers, unordered-pair group and inline explanation.
- `PracticeAttempt`: learner answers, status, submitted score and a snapshot of per-question results.

The practice content and learner attempt are separate sources of truth. Answer keys remain on the server and are never embedded in the page before submission.

Content synchronization preserves stable IDs and existing attempts. Database shape is managed by Alembic migrations.

## Implemented learning-evidence slice

These concepts are now persisted:

- `LearningResource`: provider-neutral material metadata. Each current IELTS `PracticeSet` links to one resource.
- `StudySession`: an immutable submitted activity with skill, resource, timestamps, accuracy and optional self-ratings.
- `ExerciseAttempt`: one immutable question result with answer, correctness, score and prompt/answer/explanation snapshots.
- `SkillPerformance`: normalized session evidence such as accuracy and correct/incorrect counts. Unknown ratings remain `NULL`; the system does not invent confidence or difficulty values.

`PracticeAttempt.submission_revision` identifies each completed version. The same submission can safely be retried without duplicating evidence; changing an answer and submitting again creates a new historical session.

## Implemented learner-profile slice

- `LearnerProfile`: stable local learner identity for profile history.
- `LearnerProfileSnapshot`: immutable calculation timestamp, algorithm version and evidence fingerprint.
- `LearnerSkillSnapshot`: one row per skill with score, evidence status, averages, trend, calculation weights, evidence IDs and explanation.

A snapshot always contains Listening, Speaking, Reading and Vocabulary. A skill with no evidence stores `NULL` as its score and `no_data` as its status. This distinguishes unknown ability from poor ability.

## Implemented weakness-assessment slice

- `WeaknessAssessmentRun`: immutable learner-wide assessment time, detector version and evidence fingerprint.
- `WeaknessSkillAssessment`: one classification per skill, its smoothed/latest scores, observed metrics, evidence snapshot IDs and measurable reasons.

The detector distinguishes `insufficient_evidence`, `weak`, `developing`, `stable`, and `strong`. It needs at least two scored snapshots, and weak/strong classifications require confirmation rather than reacting to one outlier.

## Implemented adaptive-decision slice

- `AdaptationDecision`: append-only system recommendation or learner override, including actor, skill, previous/new duration, previous/new resource, reasons and timestamp.

## Implemented daily-planning slice

- `StudyPlan`: one immutable assignment boundary per learner/date, with source algorithm versions, assessment reference, total duration and plan-level explanation.
- `StudyPlanItem`: one independently completable skill module with system-recommended and current duration/resource fields, status, score, reasons, first-start time and current completion time.

The unique learner/date key makes normal generation idempotent. Separate system/current fields allow a later manual override without destroying the original recommendation. `LearningResource.priority` is explicit metadata; last-studied and last-assigned values remain derived from history instead of becoming duplicate sources of truth.

`StudyPlanItem.status` is updated independently. `StudyPlan.status` is derived on every status transition: all items completed means `completed`; otherwise it remains `active`. Completion does not create an adaptation decision because it records study progress, not a change to the recommendation.

`started_at` is set on the first transition into `in_progress` or `completed`. It is retained if the learner reopens the module. `completed_at` represents the current completed state and is cleared when the module is reopened. Immutable fine-grained activity events can be added later without changing this state contract.

An upgrade from the previous plan schema backfills one system decision for every existing plan item, so decision history does not silently start empty.

Today, History and Progress all read these models through services. History combines plans and sessions by Sydney calendar date. Progress keeps estimated completed-plan minutes separate from `StudySession.actual_duration_seconds`, which is the only source of real elapsed time.

## Implemented vocabulary and review slice

- `VocabularyItem`: learner-owned complete expression, meaning, example, learned date, personal note, difficulty, source resource/context, tags and normalized duplicate key.
- `ReviewItem`: current scheduler version, step, next due date, last reviewed time, review count and active state for one vocabulary item.
- `ReviewAttempt`: immutable rating with idempotency request ID, previous/new step, previous/new due date, interval, previous/new mastery and review time.

The library exposes `new`, `learning`, `familiar` and `mastered`. Current mastery and next-review state are updated atomically with the attempt that caused the transition. Review history is never reconstructed from only the latest state.

The initial configured gaps are 1, 2, 4, 7, 16 and then 30 days. Normal `Good` reviews therefore land at cumulative Day 1, 3, 7, 14 and 30; completing the Day 30 review marks the item mastered and schedules a later maintenance review. The policy is behind `ReviewScheduler`, so a future algorithm can replace it without changing routes or templates.
