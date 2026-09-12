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

## Planned adaptive slice

- `LearnerProfileSnapshot`: an immutable time-series view of four skill scores and supporting evidence.
- `AdaptationDecision`: a recommendation, its measurable reasons and any manual override.

The next conversion path is `SkillPerformance history → LearnerProfileSnapshot`.
