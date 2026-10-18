# ADR 0001: Persist immutable learning evidence per submission revision

## Decision

Translate each completed practice submission into one generic `StudySession`, its question-level `ExerciseAttempt` records, and one or more `SkillPerformance` records. Identify the source with a stable type, ID, and revision so retries are idempotent and later submissions create new history.

## Context

The original IELTS attempt table stores the current answer sheet and grading snapshot. It is useful for continuing a practice page, but editing and resubmitting it can replace the latest result. Learner profiles need historical evidence that never changes underneath an earlier calculation.

## Alternatives

- Calculate profiles directly from the mutable IELTS table: simpler now, but loses history and couples adaptation to IELTS.
- Copy only an overall score: insufficient for mistake review and future question-level analysis.
- Build an event-bus infrastructure first: unnecessary for the current local modular monolith.

## Reason

The evidence model works for future IELTS, podcast, reading, vocabulary, speaking, and AI-generated activities. The small application-level recorder is explicit and testable, while stable revision keys provide retry safety without introducing distributed infrastructure.
