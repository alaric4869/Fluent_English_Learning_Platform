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

## Planned adaptive-decision slice

- `AdaptationDecision`: a recommendation, its measurable reasons and any manual override.
- `StudyPlan` and `StudyPlanItem`: the date-persisted plan and its independently completable modules.

The next conversion path is `WeaknessAssessmentRun + available resources → explainable StudyPlan`.
