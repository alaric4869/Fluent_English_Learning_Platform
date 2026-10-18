# Active architecture

Fluent is a React + FastAPI + PostgreSQL modular monolith. The browser owns presentation and local interaction state; Python owns validation, learning rules, persistence, analytics, adaptation and authorized AI Agent tools.

## Repository shape

```text
english_tool/
├── frontend/        # React + TypeScript + Vite
├── backend/         # FastAPI + Pydantic + SQLAlchemy + Alembic
├── resources/       # private, git-ignored IELTS books and audio
├── docs/            # cross-stack architecture and migration status
└── compose.yaml     # React, FastAPI and PostgreSQL local stack
```

Detailed backend boundaries live in [`../backend/docs/architecture.md`](../backend/docs/architecture.md). The active frontend migration sequence lives in [`react-fastapi-postgresql-migration.md`](react-fastapi-postgresql-migration.md).

## Dependency direction

```text
React pages and feature components
  -> typed /api/v1 request and response contracts
  -> FastAPI route layer
  -> focused application services
  -> deterministic domain policies and repository protocols
  -> SQLAlchemy repository adapters
  -> PostgreSQL
```

React components do not query database tables or implement authoritative grading, review scheduling or adaptation rules. FastAPI routes validate transport input and delegate to services. Application services remain independent of HTTP and call repository interfaces rather than provider-specific database APIs.

## Frontend

`frontend/src/pages` contains route-level screens. `frontend/src/components` contains reusable presentation components, while `frontend/src/lib` owns the typed HTTP client and browser helpers. Server state stays behind API query boundaries; temporary visual state stays inside the relevant React feature.

Dashboard, Today, Library, Review, Notebook, History, Progress, Weekly Review, IELTS Listening/Reading, Writing, Speaking/Retelling and intensive Listening are React vertical slices backed by typed JSON APIs. Authoritative grading, autosave validation, submission evidence and sentence-state transitions remain in Python services. The remaining presentation migration is limited to AI feedback, coaching and approval-gated adaptive-plan controls.

## Backend

The backend is organized by responsibility:

- `app/api`: FastAPI presentation and learner identity boundary
- `app/schemas`: explicit Pydantic API contracts
- `app/services`: application use cases
- `app/domain`: deterministic learning policies and repository ports
- `app/repositories`: SQLAlchemy persistence adapters
- `app/models`: relational persistence models
- `app/ai_agent`: provider-neutral tools and authorization
- `app/integrations`: replaceable external provider adapters
- `migrations`: Alembic schema history

SQLite remains available for isolated tests. PostgreSQL is the primary local integration and deployment database.

## AI boundary

The Agent is not allowed unrestricted database access. It calls typed tools backed by application services, such as reading learner context, finding due reviews, searching resources and proposing a plan. Plan-changing recommendations require explicit learner approval and retain an audit trail.

## Migration status

The superseded root Vinext/D1 application has been removed. Jinja2 now exists only as a temporary rollback presentation inside `backend/`; it is not the target frontend architecture and will be deleted after the remaining AI controls reach React parity and the complete user flow passes end-to-end tests.
