# ADR 0021: Split React presentation from FastAPI and use PostgreSQL for development

## Decision

The target application is a modular monolith with two deployable processes:

- `frontend/`: React and TypeScript presentation code.
- `backend/`: FastAPI HTTP API, application services, domain policies, SQLAlchemy repositories and Alembic migrations.

React communicates with FastAPI through versioned, typed `/api/v1` contracts. It never imports Python domain code or accesses the database. PostgreSQL is the primary development and deployment database. SQLite remains available for fast isolated automated tests.

## Context

The first Python-first edition used server-rendered Jinja2 templates. That kept the MVP small, but the learner now wants a frontend stack they can maintain and explain confidently. At the time of this decision, a previous Vinext/D1 prototype also remained in the repository and created a second source of truth.

## Alternatives

- Keep Jinja2 permanently: lower migration cost, but does not match the selected frontend skill set.
- Return to the previous Vinext/D1 application: preserves React, but duplicates the mature Python learning domain and persistence logic.
- Rewrite the whole system at once: gives a clean folder tree immediately, but creates unacceptable regression risk across grading, study history and adaptive-learning behavior.

## Consequences

Migration proceeds by vertical slice. New JSON contracts and React pages are added while the matching Jinja2 page remains as a fallback. The superseded Vinext/D1 implementation was removed after the M20 React/FastAPI/PostgreSQL stack passed its first end-to-end checks. Once every remaining user flow has parity and end-to-end tests pass, the temporary Jinja templates are removed in an explicit cleanup milestone.

PostgreSQL runs through Docker Compose for local development. Repository interfaces and application services remain database-agnostic, and tests may continue to use in-memory SQLite where vendor behavior is irrelevant.
