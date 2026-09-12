# Current and planned data model

## Implemented IELTS resource slice

- `PracticeSet`: one book/test/skill combination, such as G20 Test 1 Listening.
- `PracticeSection`: one Listening Part or Reading Section; owns instructions, passage blocks and an optional private audio path.
- `PracticeQuestion`: prompt, type, choices, accepted answers, unordered-pair group and inline explanation.
- `PracticeAttempt`: learner answers, status, submitted score and a snapshot of per-question results.

The practice content and learner attempt are separate sources of truth. Answer keys remain on the server and are never embedded in the page before submission.

Content synchronization preserves stable IDs and existing attempts. Database shape is managed by Alembic migrations.

## Next learning-evidence slice

These concepts are planned, not yet implemented:

- `LearningResource`: provider-neutral material metadata; an IELTS `PracticeSet` can reference one resource.
- `StudySession`: one bounded learner activity with skill, timing, completion and self-ratings.
- `SkillPerformance`: normalized evidence derived from a session, such as accuracy, difficulty, confidence and error counts.
- `LearnerProfileSnapshot`: an immutable time-series view of skill scores and supporting evidence.
- `AdaptationDecision`: a recommendation, its measurable reasons and any manual override.

The first conversion path will be `submitted PracticeAttempt → StudySession → SkillPerformance`. It will use the existing G20 Test 1 content before any bulk resource import.
