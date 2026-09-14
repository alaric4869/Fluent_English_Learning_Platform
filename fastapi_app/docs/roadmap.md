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
- Persist immutable `LearnerProfileSnapshot` history for the tracked skill set (expanded to include Writing in M13).
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

## M10 · Permanent Resource Library

- Add/edit/recoverably archive personal resources with URL, text, transcript, notes, tags, priority and duration.
- Search and filter by skill, type, topic, difficulty and completion; sort by addition, study recency, title or priority.
- Keep favorites, saved-for-later and archive state user-scoped while preserving built-in resources and study history.
- Feed non-archived personal resources into the existing recommendation pipeline through `ResourceService`.

## M11 · Dashboard and Weekly Review

- Focused Dashboard with today summary, review queue, streak, weekly time and quick actions.
- Weekly Review with strongest/weakest area, retention and explicit “review next week” material.
- Keep actual tracked time separate from completed planned minutes.
- Generate the report from persisted learning facts without a duplicate weekly-summary table.

## M12 · Timed study sessions and intensive listening

- Add real per-module study sessions with timer, notes, difficulty and confidence to Today.
- Build the intensive-listening sentence workflow around real audio/video resources and transcripts.
- Feed those new signals into the existing learner profile without changing Dashboard contracts.

## M13 · IELTS G Writing foundation

- Promote Writing to a first-class profile, weakness, resource and planning skill.
- Alternate Reading and Writing by date while keeping four daily modules and the same baseline time.
- Convert G20 Test 1 Writing Tasks 1–2 into web text with timer, outline, word count, autosave and explicit submission.
- Preserve immutable submission revisions and record subjective evidence without fabricating a Band score.

## M14 · Speaking and retelling workspace

- Add a focused Speaking / retelling workspace around the existing typed record.
- Guide Listen → Pause → Repeat → Hide transcript → Retell without adding AI evaluation yet.
- Save outline, intended chunks, mistakes and improved version against the source resource.
- Keep `voice_recording_reference` as the stable seam for a later recording adapter.

## M15 · Content import and expansion

- Build repeatable, validated imports for G20 Test 2–4 Listening, Reading and Writing.
- Preserve native tables, maps and figures while keeping all answers web-interactive.
- Add curated real-world Australian audio/video, articles and speaking prompts.

## M16 · Provider-neutral AI Agent tool layer

- Expose stable application services as typed agent tools; never expose raw tables.
- Add provider, tool authorization, recommendation and report interfaces with a mock implementation.

## M17 · AI evaluation and adaptive planning

- Add Writing/retelling evaluation behind replaceable interfaces.
- Store rubric evidence and explanations separately from learner-authored work.
- Let AI recommendations supplement, not silently replace, deterministic planning and manual overrides.

## M18 · Reading split layout and product polish

- Refine Reading into a responsive source-left/questions-right workspace.
- Finish keyboard, accessibility, empty-state and cross-page consistency passes.
- Prepare optional authentication, PostgreSQL and synchronization adapters without rewriting domain logic.

Do not bulk-import more IELTS tests before M1–M6 establish the adaptive feedback loop.
