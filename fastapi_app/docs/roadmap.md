# Roadmap

## M0 · Architecture and persistence correction

- Make FastAPI the target architecture while retaining legacy code for migration audit.
- Introduce Alembic and safely adopt existing local databases.
- Preserve attempts when seed content changes.
- Restore the established calm green/cream UI.
- Render structured table questions as native HTML and fix grouped multi-answer behavior.

## M1 · Learning data pipeline

- Add provider-neutral `LearningResource`, `StudySession`, `ExerciseAttempt`, and `SkillPerformance` concepts.
- Convert every submitted G20 result into normalized, immutable performance evidence.
- Preserve submission history using idempotent attempt revisions.
- Test the complete `PracticeAttempt → StudySession → ExerciseAttempt + SkillPerformance` path.

## M2 · Learner profile

- Read recent performance through a repository/service boundary.
- Add deterministic, configurable `SkillEvaluator` logic.
- Persist immutable `LearnerProfileSnapshot` history for Listening, Speaking, Reading and Vocabulary.
- Explain how every score was derived and handle insufficient evidence explicitly.

## M3 · Weakness detection (next)

- Add configurable `WeaknessDetector` rules over multiple recent snapshots.
- Distinguish insufficient evidence from weak performance.
- Return structured reasons using real accuracy, confidence, hard-item and trend values.
- Add tests that prevent one poor session from immediately changing a skill classification.

## M4–M6 · Adaptive loop

1. Rule-based resource recommender and study-plan generator.
2. Adaptation decisions with measurable explanations and manual overrides.
3. Today/Progress integration with historical trends.

## Later, after the rule-based loop works

- Expose stable application services as provider-neutral AI agent tools; the agent never gets raw database access.
- Add AI evaluation and planning behind replaceable interfaces.
- Expand curated IELTS, PTE, podcast, article, Australian English and custom-resource content.
- Add authentication, PostgreSQL and synchronization without rewriting domain logic.
- After AI Agent integration, refine the Reading workspace into a responsive source-left/questions-right split view.

Do not bulk-import more IELTS tests before M1–M6 establish the adaptive feedback loop.
