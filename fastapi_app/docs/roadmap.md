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

- Added a focused Speaking / retelling workspace around the existing typed record.
- Uses G20 Test 1 Part 1 real audio and proofread script excerpts for Listen → Pause → Repeat → Imitate → Hide transcript → Retell.
- Persists per-sentence practice state/count, autosaved current work and immutable submission revisions.
- Emits subjective learning evidence without a fabricated score and keeps `voice_recording_reference` as the stable seam for a later recording adapter.

## M15 · Content import and expansion

- **Completed.** Added a strict, ordered manifest importer for G20 Test 1–4 and curated external resources.
- Test 2–4 Listening and Reading each contain all 40 answerable questions; all six new Writing tasks render as web-native workspaces.
- Native tables and flowcharts render as HTML with inline inputs. Test 3's map remains a verified source image with four autosaved web answers.
- Grouped multi-answer questions use bounded checkboxes, preserve order-independent grading and no longer behave like single-choice questions.
- Added official ABC/SBS real-world audio/video, articles, chunks and speaking prompts to the normal resource catalogue.

## M16 · Provider-neutral AI Agent tool layer

- **Completed.** Exposed nine strict read tools over stable application services; raw tables, repositories and database sessions remain inaccessible.
- Added per-tool permission/allow-list authorization, a bounded provider loop, recommendation/report protocols and deterministic mock implementations.
- Kept learner identity outside model-generated arguments and added security tests for injected identity and unauthorized calls.

## M17 · AI evaluation and adaptive planning

- **Completed.** Added optional OpenAI Responses adapters behind provider-neutral interfaces, while keeping offline mocks and a disabled-by-default configuration.
- Writing and text retelling feedback use strict structured output and persist rubric evidence separately from immutable learner submissions; the UI requires an explicit request and never calls AI on submit.
- Added a separately authorized `save_ai_recommendation` tool that appends explainable suggestions without changing deterministic plans or learner overrides.

## M18 · Reading split layout and product polish

- **Completed.** Reading now uses a responsive source-left/questions-right workspace with independent desktop scrolling and a small-screen single-column fallback.
- Added keyboard-operable section tabs and question jumps, visible focus, progress/status semantics, skip navigation, reduced-motion support and honest empty states.
- Added one replaceable learner-context dependency, an optional PostgreSQL driver/engine seam and a provider-neutral synchronization port without changing domain services or the local-first default.

## M19 · Test 1 source-fidelity audit

- **Completed.** Verified all 80 Test 1 Listening and Reading answer keys against the learner-owned G20 source answer pages.
- Restored Listening Part 4's original hierarchical notes layout with ten inline web answer fields.
- Restored Reading Section 2's “Creating a successful business” notes layout with six inline web answer fields.
- Added content-schema, presenter and rendered-page regression tests so embedded answers appear exactly once and still use the existing autosave/grading path.

Additional IELTS books should use the same manifest, source verification and validation tests rather than adding hard-coded page data.

## Post-roadmap · User-facing AI coach

- **Completed.** Weekly Review now exposes an explicit, persisted AI coaching action backed by the existing provider-neutral Agent tools.
- The Agent is restricted to four read-only evidence tools and the service rejects reports that omit any required evidence source.
- Disabled or incomplete OpenAI configuration produces setup guidance; no learning page depends on network availability.

## Post-roadmap · Learner-approved AI plan proposals

- **Completed.** Today can explicitly ask the Agent to inspect the existing plan through a bounded evidence-tool allow-list.
- Duration/resource suggestions remain non-applied proposals until the learner accepts them; dismissal is also preserved as linked audit history.
- Applying a proposal revalidates plan state, skill limits, resource availability and module lifecycle, then commits the change and learner response atomically.
