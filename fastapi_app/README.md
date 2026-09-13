# Adaptive English Learning Agent · FastAPI edition

This directory is the target Python-first application. Its current usable UI slice is G20 Test 1 Listening and Reading. Every completed submission produces immutable question-level attempts, a study session, normalized skill performance, a Learner Profile snapshot when the evidence changes, and an explainable skill assessment when the profile history changes. The backend can also create one persistent, explainable study plan per learner/date and preserve validated learner overrides; Today-page integration comes in the next milestone.

## Run locally

```bash
cd fastapi_app
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/ielts>.

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
- `domain/adaptive_learning/`: typed system/manual decisions and append-only override history.
- `services/`: application use cases plus the IELTS-to-learning-evidence adapter.
- `repositories/`: SQLAlchemy persistence adapter.
- `models/`: database tables only.
- `api/routes/`: HTTP transport and validation.
- `presenters/`: converts structured exercise content into a page-specific read model; it does not grade or persist.
- `templates/` and `static/`: light server-rendered UI and browser interactions.
- `seed/`: structured practice content imported into SQLite.
- `migrations/`: Alembic schema history; schema changes must never rely on `create_all`.

The first profile algorithm uses the latest five sessions per skill. Accuracy carries 75% of the configured weight, confidence 15%, and hard-item resilience 10%. Missing optional signals are excluded and the remaining weights are normalized. With no evidence, a skill has no score; one sample is provisional; two or more samples establish the current baseline.

The initial weakness detector examines the latest four profile snapshots. It requires at least two scored snapshots and two consecutive threshold-confirming snapshots before labelling a skill `weak` or `strong`; missing evidence is recorded as `insufficient_evidence`, never as weakness. Each assessment stores the evidence snapshot IDs and measurable reasons that produced it.

The initial planner starts from Listening 30, Speaking 25, Reading 30, and Vocabulary/Review 25 minutes. Confirmed weak/developing skills receive gradual increases, confirmed strong skills receive only a small reduction, and the result is capped at 120 minutes. Resource selection prefers unused, appropriately difficult material and penalizes recently studied or recently assigned material so adjacent dates rotate when alternatives exist.

Every initial plan item creates a `system_recommendation` decision. A learner override changes only the current resource/duration, retains the system values, recalculates the plan total, and appends a `manual_override` decision. Repeating the same request is a no-op; incompatible resources and out-of-range durations are rejected.

JavaScript only manages browser concerns such as section switching, autosave requests, multi-select limits, and timer display. Answer keys, scoring, submission validation, and persistence stay in Python.
