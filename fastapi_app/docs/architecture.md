# Adaptive English Learning Agent architecture

## Product boundary

The product is the adaptive loop, not an IELTS question bank:

```text
Study → Learning evidence → Learner profile → Weakness detection
      → Recommended plan + explanation → Study again
```

The current G20 practice workspace is a content adapter and evidence producer. Bulk content import is intentionally paused until the loop can consume its results.

## Dependency direction

```text
Jinja pages / small browser interactions
        ↓
Application services (currently IeltsPracticeService)
        ↓
Domain rules + repository protocols
        ↓
SQLAlchemy repository
        ↓
SQLite (local) / PostgreSQL (later)
```

Templates never query the database and JavaScript never contains answer keys. Both HTML routes and API routes use the same application service. Domain rules have no FastAPI or SQLAlchemy dependency, so they can be tested independently.

## Current modules

- `api/routes/practice.py`: translates HTTP requests into use-case calls and safely streams approved local audio files.
- `presenters/ielts.py`: creates an IELTS workspace read model, including native table blocks, figure blocks, and grouped multi-answer questions.
- `domain/ielts/`: question types, grading result types, answer normalization and repository contract.
- `services/ielts_practice.py`: load practice, save an answer, require completion, grade and submit.
- `repositories/sqlalchemy_ielts.py`: the only place that reads and writes IELTS database tables.
- `models/ielts.py`: stable relational persistence concepts.
- `seed/g20_test1.json`: versioned, structured web content imported into SQLite.
- `templates/` and `static/`: accessible server-rendered screens plus small progressive JavaScript interactions.
- `migrations/`: Alembic schema history and the adopted pre-Alembic baseline.

## Persistence safety

- Startup runs Alembic before importing content.
- A legacy database is stamped at the baseline only after its expected tables and columns are validated.
- Seed version changes update practice sets, sections, and questions in place. They do not delete learner attempts.
- Learner answers are serialized through one browser save queue because the current attempt schema stores an answer map as one JSON value.
- Future schema changes require a migration; `Base.metadata.create_all()` is not an application migration mechanism.

## Presentation boundary

Structured content contains semantic blocks such as `table`, `figure`, and question groups. The presenter turns those blocks into a rendering model. Jinja templates preserve the source layout using native HTML tables or approved source images, while answer inputs remain normal accessible form controls. Grading still works from question IDs and is independent of layout.

## Current limits

- A single local learner key is used until authentication is added.
- One working attempt is stored per learner and practice set. Attempt history and retakes will change this to multiple immutable submissions.
- Only G20 Test 1 Listening and Reading have been curated and quality checked.
- G20 Test 1 has no map question. The figure block preserves a verified crop and answer association; coordinate overlays should be added and visually checked when a real map resource is curated.

## Next domain boundary

The next milestone adds an explicit learning-data pipeline without changing the IELTS grader:

```text
Submitted ExerciseAttempt
        ↓
StudySession (what the learner did)
        ↓
SkillPerformance (normalized evidence)
        ↓
LearnerProfileSnapshot (later milestone)
```

The conversion belongs in an application service and repository abstraction, not in a route, template, or JavaScript event handler.
