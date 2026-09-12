# Roadmap

## M0 · Architecture and persistence correction

- Make FastAPI the target architecture while retaining legacy code for migration audit.
- Introduce Alembic and safely adopt existing local databases.
- Preserve attempts when seed content changes.
- Restore the established calm green/cream UI.
- Render structured table questions as native HTML and fix grouped multi-answer behavior.

## M1 · Learning data pipeline (next)

- Add `LearningResource`, `StudySession`, and `SkillPerformance` domain concepts.
- Convert a submitted G20 attempt into normalized performance evidence.
- Preserve attempt history and support clean retakes.
- Test the full `ExerciseAttempt → StudySession → SkillPerformance` path.

## M2–M6 · Adaptive loop

1. Learner profile and immutable profile snapshots.
2. Deterministic skill evaluator.
3. Weakness detector based on recent evidence.
4. Rule-based resource recommender and study-plan generator.
5. Adaptation decisions with measurable explanations and manual overrides.
6. Today/Progress integration with historical trends.

## Later, after the rule-based loop works

- Expose stable application services as provider-neutral AI agent tools; the agent never gets raw database access.
- Add AI evaluation and planning behind replaceable interfaces.
- Expand curated IELTS, PTE, podcast, article, Australian English and custom-resource content.
- Add authentication, PostgreSQL and synchronization without rewriting domain logic.

Do not bulk-import more IELTS tests before M1–M6 establish the adaptive feedback loop.
