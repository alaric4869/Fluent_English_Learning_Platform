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

## M3 · Weakness detection

- Add configurable `WeaknessDetector` rules over multiple recent snapshots.
- Distinguish insufficient evidence from weak performance.
- Return structured reasons using real accuracy, confidence, hard-item and trend values.
- Add tests that prevent one poor session from immediately changing a skill classification.

## M4 · Rule-based daily planning

- Rank active resources using priority, target difficulty, study recency and assignment recency.
- Generate gradual skill-time changes from the current weakness assessment.
- Persist one plan per learner/date with four independent plan items.
- Preserve both system-recommended and current values for future overrides.

## M5 · Explainable decisions and overrides

- Append an initial system decision for every generated plan item.
- Validate manual duration and replacement-resource changes in an application service.
- Preserve the system recommendation while changing current values and plan total.
- Keep idempotent, append-only decision history, including reset-to-system actions.

## M6 · Today UI integration

- Connect the date-persisted plan to the FastAPI Today page.
- Show resource title, duration, module progress and measurable reasons.
- Add manual duration/resource controls using typed HTTP schemas.
- Complete/reopen individual modules and derive whole-plan status.
- Keep the established calm green/cream visual system and responsive shell.

## M7 · History and Progress

- Add persisted first-start/current-completion timestamps to plan items through migration `0007`.
- Add a timeline, arbitrary-month calendar and single-day History detail.
- Add deterministic streaks, plan completion metrics, real tracked time, 28-day activity and current skill profile.
- Keep estimated workload and actual elapsed time visibly separate.

## M8 · Vocabulary chunks and spaced review

- Add complete chunks with meaning, example, source, notes, difficulty and tags.
- Schedule new items and persist every Again / Hard / Good / Easy attempt.
- Add a searchable/filterable chunk library and a focused due-today queue.
- Surface the due count in Today and completed reviews in Progress.
- Keep scheduling rules configurable and replaceable through `ReviewScheduler`.

## M9 · Notebook and practice records

- Save listening sentences with explicit hearing states and optional spaced review.
- Store speaking/retelling prompts, outlines, intended chunks, mistakes and improved versions.
- Add typed, searchable personal notes and mistake-book entries with source links.
- Generalize review scheduling so chunks and difficult sentences share one replaceable scheduler.

## M10 · Next product slice

- Permanent Resource Library with add/edit/archive, search, skill/topic/difficulty filters, favorites and saved-for-later state.
- Keep content management behind `ResourceService`; do not hard-code resources into templates.

## Later, after the rule-based loop works

- Expose stable application services as provider-neutral AI agent tools; the agent never gets raw database access.
- Add AI evaluation and planning behind replaceable interfaces.
- Expand curated IELTS, PTE, podcast, article, Australian English and custom-resource content.
- Add authentication, PostgreSQL and synchronization without rewriting domain logic.
- After AI Agent integration, refine the Reading workspace into a responsive source-left/questions-right split view.

Do not bulk-import more IELTS tests before M1–M6 establish the adaptive feedback loop.
