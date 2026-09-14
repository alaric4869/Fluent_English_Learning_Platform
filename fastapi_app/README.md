# Adaptive English Learning Agent · FastAPI edition

This directory is the target Python-first application. Its usable UI contains a focused Dashboard, a date-persisted Today plan with timed study records, an intensive-listening workspace for real audio/video and sentence marking, a real-audio Speaking/Shadowing/Retelling workspace, a generated Weekly Review, a permanent user-managed Resource Library, a mixed chunk/listening-sentence review loop, a searchable Notebook and mistake book, persistent History and evidence-based Progress, plus G20 Test 1 Listening, Reading and web-native Writing. Objective IELTS submissions produce question-level evidence; Speaking, Writing and completed daily modules produce duration/difficulty/confidence evidence without inventing an accuracy. All refresh the provider-neutral Learner Profile and explainable skill assessment.

## Run locally

```bash
cd fastapi_app
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/dashboard>. Today is at <http://127.0.0.1:8000/today>, Weekly Review at <http://127.0.0.1:8000/weekly-review>, Library at <http://127.0.0.1:8000/library>, Review at <http://127.0.0.1:8000/review>, Notebook at <http://127.0.0.1:8000/notebook>, History at <http://127.0.0.1:8000/history>, Progress at <http://127.0.0.1:8000/progress>, and IELTS practice remains available at <http://127.0.0.1:8000/ielts>. Listening resources open at `/listening/{resource_id}`, Speaking practices at `/speaking/{resource_id}`, and Writing tasks at `/writing/{resource_id}`.

The app also runs pending migrations safely at startup. A pre-Alembic database is adopted only when all expected baseline tables and columns are present. Seed changes synchronize content in place so existing attempt IDs and learner answers are preserved.

IELTS audio is streamed from the repository's private, git-ignored `resources/listening` directory. Curated figures can be served from `data/imported/assets`; source PDFs themselves are never exposed to the browser.

`scripts/extract_pdf_text.py` is the repeatable OCR helper for future book imports. Its output stays in ignored local working directories and must be proofread before becoming practice content.

## Boundaries

- `domain/`: deterministic IELTS rules and repository contracts.
- `domain/learning_evidence/`: provider-neutral session, exercise-attempt, skill and evidence contracts.
- `domain/learner_profile/`: configurable rule-based scoring with explicit evidence sufficiency and trends.
- `domain/weakness_detection/`: replaceable, configurable classification over profile history.
- `domain/resources/`: provider-neutral resource candidates and replaceable recommendation policy.
- `domain/study_plan/`: configurable time allocation and a replaceable plan-generator contract.
- `domain/study_session/`: timed daily-module lifecycle and persistence contract.
- `domain/writing/`: web-native writing draft/submission contracts, separate from objective grading.
- `domain/adaptive_learning/`: typed system/manual decisions and append-only override history.
- `domain/history/` and `domain/analytics/`: reporting contracts and deterministic progress calculations.
- `domain/dashboard/` and `domain/weekly_review/`: composed read models and deterministic week calculations.
- `domain/vocabulary/` and `domain/review/`: reusable chunks, typed review state and a replaceable scheduler.
- `domain/listening/`, `domain/speaking/` and `domain/notebook/`: difficult sentences, revisioned shadowing/retelling practice and typed mistake-book notes.
- `services/`: application use cases plus the IELTS-to-learning-evidence adapter.
- `repositories/`: SQLAlchemy persistence adapter.
- `models/`: database tables only.
- `api/routes/`: HTTP transport and validation.
- `presenters/`: converts structured exercise content into a page-specific read model; it does not grade or persist.
- `templates/` and `static/`: light server-rendered UI and browser interactions.
- `composition.py`: the explicit application-service composition root shared by routes.
- `seed/`: structured practice content imported into SQLite.
- `migrations/`: Alembic schema history; schema changes must never rely on `create_all`.

The profile algorithm uses the latest five sessions per skill. Objective evidence keeps the accuracy/confidence/hard-item weighting. A daily module without questions has `NULL` accuracy and is scored only from explicitly provided confidence and perceived difficulty; its explanation says that this is subjective evidence. Missing signals are excluded and weights are normalized. With no evidence, a skill has no score; one sample is provisional; two or more samples establish the current baseline.

The initial weakness detector examines the latest four profile snapshots. It requires at least two scored snapshots and two consecutive threshold-confirming snapshots before labelling a skill `weak` or `strong`; missing evidence is recorded as `insufficient_evidence`, never as weakness. Each assessment stores the evidence snapshot IDs and measurable reasons that produced it.

The planner keeps four modules: Listening 30, Speaking 25, Vocabulary/Review 25, plus a 30-minute Reading or Writing module that alternates deterministically by date. Confirmed weak/developing skills receive gradual increases, confirmed strong skills receive only a small reduction, and the result is capped at 120 minutes. Resource selection prefers unused, appropriately difficult material and penalizes recently studied or recently assigned material so adjacent dates rotate when alternatives exist.

Every initial plan item creates a `system_recommendation` decision. A learner override changes only the current resource/duration, retains the system values, recalculates the plan total, and appends a `manual_override` decision. Repeating the same request is a no-op; incompatible resources and out-of-range durations are rejected.

The Today page is intentionally server-rendered. A small script starts a module session, accumulates active timer seconds, autosaves notes and self-ratings, and completes the session through typed endpoints. Refreshing restores saved progress. Only all four completed items complete the plan; undoing one reopens it and a later start creates a new session revision. Replacing a resource is blocked while its session is active or the module is still completed.

History can return to any saved date, using a recent timeline, an arbitrary-month calendar, or a single-day detail page. Progress derives streaks and completion metrics from saved plans and submitted sessions. It labels completed plan minutes as estimates and reports real tracked time separately; missing timer data is never inferred.

Review stores complete expressions rather than forcing isolated words, and can schedule difficult listening sentences through the same stable contract. New review items become due one day after their learned date. The initial scheduler follows cumulative Day 1, 3, 7, 14 and 30 checkpoints for `Good`; `Again`, `Hard` and `Easy` adjust the next step deterministically. Every rating is stored as an immutable attempt and client request IDs make retries idempotent.

Notebook keeps free-form typed notes, listening sentences and speaking retellings as separate domain records. Listening practice status (`could_not_hear`, `difficult`, `understood`, `mastered`) is intentionally independent from review mastery. Speaking uses a real local G20 conversation, learner-specific sentence states, one autosaved retelling record and immutable submission revisions. It stores the outline, intended chunks, optional written retelling, mistakes, improved version, timer and self-ratings. A nullable recording reference remains the seam for a later recording adapter; this milestone does not fabricate an IELTS Speaking score.

Library treats resource content and learner-specific state separately. Built-in IELTS resources and personal URL/text/transcript resources share the same read model and recommendation pipeline. Favorites, saved-for-later and recoverable archives live in `ResourceUserState`, so one learner's organization does not mutate global content. Archived resources leave future recommendation candidates but remain referenced by existing plans and history.

Dashboard composes existing service results; it does not query tables or own a second copy of plan/progress state. Weekly Review is calculated from persisted plans, submitted sessions, vocabulary, difficult sentences and immutable review attempts. Its retention percentage is explicitly `Good + Easy` divided by this week's review ratings. Historical due-queue completion cannot be reconstructed from the current schema and is therefore not invented.

JavaScript only manages browser concerns such as section switching, autosave requests, multi-select limits, and timer display. Answer keys, scoring, submission validation, and persistence stay in Python.
