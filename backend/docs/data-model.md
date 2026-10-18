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
- `StudySession`: one revision of a skill/resource activity. Daily modules are mutable only while `in_progress`; completion freezes their duration, notes and self-ratings. Submitted IELTS revisions are created directly as completed immutable sessions.
- `ExerciseAttempt`: one immutable question result with answer, correctness, score and prompt/answer/explanation snapshots.
- `SkillPerformance`: normalized session evidence such as accuracy and correct/incorrect counts. Unknown ratings remain `NULL`; the system does not invent confidence or difficulty values.

`StudySession.accuracy` and `SkillPerformance.accuracy` are nullable by design. A question-based exercise writes objective accuracy; a timed module writes difficulty/confidence evidence and leaves accuracy unknown. `PracticeAttempt.submission_revision` identifies each completed IELTS version. The same submission can safely be retried without duplicating evidence; changing an answer and submitting again creates a new historical session.

## Implemented learner-profile slice

- `LearnerProfile`: stable local learner identity for profile history.
- `LearnerProfileSnapshot`: immutable calculation timestamp, algorithm version and evidence fingerprint.
- `LearnerSkillSnapshot`: one row per skill with score, evidence status, averages, trend, calculation weights, evidence IDs and explanation.

A snapshot always contains Listening, Speaking, Reading, Writing and Vocabulary. A skill with no evidence stores `NULL` as its score and `no_data` as its status. This distinguishes unknown ability from poor ability.

## Implemented weakness-assessment slice

- `WeaknessAssessmentRun`: immutable learner-wide assessment time, detector version and evidence fingerprint.
- `WeaknessSkillAssessment`: one classification per skill, its smoothed/latest scores, observed metrics, evidence snapshot IDs and measurable reasons.

The detector distinguishes `insufficient_evidence`, `weak`, `developing`, `stable`, and `strong`. It needs at least two scored snapshots, and weak/strong classifications require confirmation rather than reacting to one outlier.

## Implemented adaptive-decision slice

- `AdaptationDecision`: append-only system recommendation, learner override, non-applied AI proposal, or learner response to that proposal, including actor, skill, previous/new duration, previous/new resource, reasons and timestamp.

An AI proposal never changes `StudyPlanItem`. Accepting or dismissing it appends a second learner-authored decision whose nullable `source_decision_id` points to the proposal. The link is unique, so one proposal can receive only one response. Acceptance updates the current plan values in the same transaction; dismissal leaves them untouched. Superseded, stale, completed-module and unavailable-resource proposals cannot be applied.

## Implemented AI-evaluation slice

- `WorkEvaluation`: one immutable provider result for a specific Writing/Retelling submission revision, evaluator version and input fingerprint.

The row stores the exact task/text/context sent for evaluation, provider/model identifiers, a 0–100 coaching score, per-criterion evidence, strengths, priorities, corrections and suggested revision. It is separate from `WritingSubmission`, `RetellingSubmission`, `SkillPerformance` and `StudyPlan`, so provider feedback cannot overwrite learner work or become objective performance accidentally. Repeating the same request returns the existing row.

## Implemented daily-planning slice

- `StudyPlan`: one immutable assignment boundary per learner/date, with source algorithm versions, assessment reference, total duration and plan-level explanation.
- `StudyPlanItem`: one independently completable skill module with system-recommended and current duration/resource fields, status, score, reasons, first-start time and current completion time.

The unique learner/date key makes normal generation idempotent. Separate system/current fields allow a later manual override without destroying the original recommendation. `LearningResource.priority` is explicit metadata; last-studied and last-assigned values remain derived from history instead of becoming duplicate sources of truth.

`StudyPlanItem.status` is updated independently. `StudyPlan.status` is derived on every status transition: all items completed means `completed`; otherwise it remains `active`. Completion does not create an adaptation decision because it records study progress, not a change to the recommendation.

`started_at` is set on the first transition into `in_progress` or `completed`. It is retained if the learner reopens the module. `completed_at` represents the current completed state and is cleared when the module is reopened. Immutable fine-grained activity events can be added later without changing this state contract.

An upgrade from the previous plan schema backfills one system decision for every existing plan item, so decision history does not silently start empty.

Today, History and Progress all read these models through services. History combines plans and sessions by Sydney calendar date. Progress keeps estimated completed-plan minutes separate from `StudySession.actual_duration_seconds`, which is the only source of real elapsed time.

Each Today module uses `source_type=study_plan_item`, the plan-item ID as `source_id`, and an increasing revision. Only the latest in-progress revision is editable. Duration saves are monotonic, so a stale browser request cannot reduce already recorded time. Completed revisions feed one normalized `SkillPerformance`; retries do not duplicate it.

## Implemented vocabulary and review slice

- `VocabularyItem`: learner-owned complete expression, meaning, example, learned date, personal note, difficulty, source resource/context, tags and normalized duplicate key.
- `SavedSentence`: learner-owned listening sentence, hearing-practice state, source and optional review link.
- `ReviewItem`: current scheduler version, step, next due date, last reviewed time, review count, mastery and exactly one vocabulary/saved-sentence target.
- `ReviewAttempt`: immutable rating with idempotency request ID, previous/new step, previous/new due date, interval, previous/new mastery and review time.

The library exposes `new`, `learning`, `familiar` and `mastered`. Current mastery and next-review state are updated atomically with the attempt that caused the transition. Review history is never reconstructed from only the latest state. Listening hearing status remains independent from review mastery.

The initial configured gaps are 1, 2, 4, 7, 16 and then 30 days. Normal `Good` reviews therefore land at cumulative Day 1, 3, 7, 14 and 30; completing the Day 30 review marks the item mastered and schedules a later maintenance review. The policy is behind `ReviewScheduler`, so a future algorithm can replace it without changing routes or templates.

## Implemented Notebook slice

- `NotebookNote`: typed personal note or mistake with source and tags.
- `RetellingRecord`: speaking prompt, current outline, intended chunks, optional written retelling, mistakes, improved version, active time, self-ratings, submission state and nullable future recording reference.

Notebook content remains separated by domain responsibility instead of being stored in one arbitrary JSON document.

## Implemented Speaking slice

- `SpeakingSentenceProgress`: learner/resource/sentence state (`need_practice`, `good`, `mastered`) plus an explicit practice count.
- `RetellingSubmission`: immutable snapshot of the learner-authored retelling fields, active duration and self-ratings for one revision.

One workspace-managed `RetellingRecord` holds the current editable state for a source resource. Older manual Notebook records remain valid and are not converted into workspace drafts. A submission creates generic `StudySession` and `SkillPerformance` evidence with `NULL` accuracy; marked-sentence counts, intended-chunk count, time, confidence and perceived difficulty are stored as measurable signals. Text evaluation is now a separate explicit adapter; voice recording/transcription remains future work.

## Implemented Writing slice

- `WritingDraft`: the learner's current response, outline, word count, active time, self-ratings and latest submission revision for one resource.
- `WritingSubmission`: an immutable response/outline snapshot for one explicit submission revision.

The writing task itself remains a `LearningResource` with structured task metadata. A submission produces a generic `StudySession` and `SkillPerformance` with `NULL` accuracy plus word-count, duration and self-assessment signals. No rule-based code invents IELTS rubric scores; optional structured AI coaching is written to `WorkEvaluation` through an application service.

## Implemented permanent Resource Library slice

- `LearningResource`: stable built-in or learner-owned material with URL, article text, transcript, notes, tags, duration and priority.
- `ResourceUserState`: per-learner favorite, saved-for-later and recoverable archive state.

Built-in resources have no owner; personal resources belong to one learner. Archiving changes only `ResourceUserState`, so plans, sessions and IELTS content keep their existing resource references. Last-studied time and completion count are derived from `StudySession`, not duplicated on the resource row.

## Dashboard and Weekly Review read models

Dashboard and Weekly Review add no database tables. They aggregate the existing dated plan items, completed study sessions, learned dates, saved sentences and immutable review attempts through repository interfaces. In-progress timers are deliberately excluded from completed-resource/history counts. This avoids a second stored total that could drift from the source records. If weekly reports later need immutable publication or AI commentary, that output can be stored as a versioned report while keeping the measured inputs unchanged.

## Validated content catalogue

Content files are not database migrations and do not contain learner state. `seed/manifest.json` provides a deterministic import order, while strict Pydantic contracts reject unknown fields, unsafe paths, duplicate slugs, malformed semantic blocks, incomplete IELTS 40-question sets and inconsistent grouped answers before importing any payload.

`PracticeSet.content_version` controls in-place content synchronization. Existing `PracticeSet`, `PracticeQuestion` and `LearningResource` IDs are retained when a version changes, so saved attempts and learning evidence keep stable references. Source-page layout is stored as semantic `table`, `flowchart`, `passage`, `notice` or `figure` blocks; answer identity remains in `PracticeQuestion`, which avoids embedding scoring rules inside HTML.

## AI coaching output

`WeeklyCoachingReport` stores an explicitly requested Agent response for one learner and
week. It records provider identity, provider response ID, the allow-listed tools actually
used, final plain text and creation time. Multiple generations are retained; the page
shows the latest. These reports are explanatory artifacts and are never treated as
measured `SkillPerformance`, review results or plan decisions.
