# FastAPI edition architecture

## Dependency direction

```text
Jinja pages / JSON API
        ↓
IeltsPracticeService
        ↓
IELTS grading rules + repository protocol
        ↓
SQLAlchemy repository
        ↓
SQLite (local) / PostgreSQL (later)
```

Templates never query the database and JavaScript never contains answer keys. Both HTML routes and API routes use the same application service. The domain grader has no FastAPI or SQLAlchemy dependency, so it can be tested and replaced independently.

## Current modules

- `api/routes/practice.py`: translates HTTP requests into use-case calls and safely streams approved local audio files.
- `domain/ielts/`: question types, grading result types, answer normalization and repository contract.
- `services/ielts_practice.py`: load practice, save an answer, require completion, grade and submit.
- `repositories/sqlalchemy_ielts.py`: the only place that reads and writes IELTS database tables.
- `models/ielts.py`: stable relational persistence concepts.
- `seed/g20_test1.json`: versioned, structured web content imported into SQLite.
- `templates/` and `static/`: accessible server-rendered screens plus small progressive JavaScript interactions.

## Deliberate first-version limits

- A single local learner key is used until authentication is added.
- Tables are created automatically for the first local schema. Alembic migrations should be introduced before the first schema change.
- One working attempt is stored per learner and practice set. Attempt history and retakes will change this to multiple immutable submissions.
- Only G20 Test 1 Listening and Reading have been curated and quality checked.

