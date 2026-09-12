# Fluent Daily English · FastAPI edition

This directory contains the local-first Python version of the IELTS practice workspace. It is intentionally separate from the existing Vinext/Sites application in the repository root.

## Run locally

```bash
cd fastapi_app
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/ielts>.

The app creates `data/english_learning.db` on first start and imports the committed structured seed data. IELTS audio is streamed from the repository's private, git-ignored `resources/listening` directory; source PDFs are never served to the browser.

`scripts/extract_pdf_text.py` is the repeatable OCR helper for future book imports. Its output stays in ignored local working directories and must be proofread before becoming practice content.

## Boundaries

- `domain/`: deterministic IELTS rules and repository contracts.
- `services/`: application use cases used by both the HTML pages and JSON API.
- `repositories/`: SQLAlchemy persistence adapter.
- `models/`: database tables only.
- `api/routes/`: HTTP transport and validation.
- `templates/` and `static/`: light server-rendered UI and browser interactions.
- `seed/`: structured practice content imported into SQLite.
