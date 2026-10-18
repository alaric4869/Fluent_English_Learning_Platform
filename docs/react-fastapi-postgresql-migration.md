# React + FastAPI + PostgreSQL migration

## Target structure

```text
english_tool/
├── frontend/
│   ├── src/
│   │   ├── components/       # reusable presentation components
│   │   ├── lib/              # HTTP client and browser-only helpers
│   │   ├── pages/            # route-level React pages
│   │   └── types/            # API response/request contracts
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes and learner identity boundary
│   │   ├── schemas/          # Pydantic HTTP contracts
│   │   ├── services/         # application use cases
│   │   ├── domain/           # deterministic learning rules and ports
│   │   ├── repositories/     # SQLAlchemy persistence adapters
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── ai_agent/         # provider-neutral agent loop and tools
│   │   └── integrations/     # OpenAI/OpenRouter adapters
│   ├── migrations/           # Alembic migration history
│   └── tests/
├── resources/                # private, git-ignored source material
└── compose.yaml              # React, FastAPI and PostgreSQL development stack
```

## Dependency direction

```text
React UI
  -> typed /api/v1 contracts
  -> FastAPI presentation layer
  -> application services
  -> domain policies and repository ports
  -> SQLAlchemy repositories
  -> PostgreSQL
```

The AI Agent calls authorized application tools. It never receives a SQLAlchemy session or unrestricted table access.

## Migration milestones

1. **M20 — foundation (complete):** create the React workspace, versioned JSON API, CORS boundary, PostgreSQL Compose stack and first Dashboard/Today vertical slice; remove the superseded root Vinext/D1 application.
2. **M21 — core learning UI (complete):** migrate Library, Review, Notebook, History, Progress and Weekly Review, including resource writes, review ratings, vocabulary capture, notebook notes and sentence-status updates.
3. **M22 — IELTS workspaces (complete):** migrated Listening, Reading, Writing, Speaking/Retelling and intensive Listening with real audio/video, autosave, grading, source-faithful tables/maps/flowcharts, grouped multi-answer checkboxes and per-question explanations. Reading uses a responsive source-left/questions-right layout.
4. **M23 — AI and adaptive controls:** migrate AI feedback, weekly coach and approval-gated plan recommendation interactions.
5. **M24 — cutover:** add end-to-end coverage and remove the temporary Jinja2 presentation fallback after every user flow has React parity.
6. **M25 — deployment and résumé:** verify PostgreSQL deployment, document the live architecture and update résumé claims to the implemented stack.

The obsolete Vinext/D1 implementation was deleted after the M20 stack and database checks passed. Jinja2 deletion intentionally occurs at M24: M22 practice parity is complete, but the server-rendered UI remains a rollback path until M23 AI controls and end-to-end verification are complete.
