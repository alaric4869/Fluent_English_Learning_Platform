# Adaptive English Learning Agent · FastAPI edition

This directory is the target Python-first application. Its current usable slice is G20 Test 1 Listening and Reading. Every completed submission now produces immutable question-level attempts, a study session, and normalized skill performance for the future learner profile.

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
- `services/`: application use cases plus the IELTS-to-learning-evidence adapter.
- `repositories/`: SQLAlchemy persistence adapter.
- `models/`: database tables only.
- `api/routes/`: HTTP transport and validation.
- `presenters/`: converts structured exercise content into a page-specific read model; it does not grade or persist.
- `templates/` and `static/`: light server-rendered UI and browser interactions.
- `seed/`: structured practice content imported into SQLite.
- `migrations/`: Alembic schema history; schema changes must never rely on `create_all`.

JavaScript only manages browser concerns such as section switching, autosave requests, multi-select limits, and timer display. Answer keys, scoring, submission validation, and persistence stay in Python.
