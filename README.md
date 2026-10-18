# Adaptive English Learning Agent

This repository is an adaptive English learning system. Its product loop is:

```text
Study → Collect performance → Update learner profile → Detect weaknesses
      → Generate and explain the next plan → Study again
```

IELTS General Training is one learning-resource type and the first source of structured performance evidence. It is not the product boundary.

## Target product areas

- Dashboard and date-persisted daily plan
- Intensive listening sentence practice
- Shadowing and written retelling
- Focused reading and chunk capture
- Spaced review with Again / Hard / Good / Easy
- Resource library, history, progress, and notebook
- IELTS General Training workspace with real local audio, persistent answer sheets, automatic Listening/Reading marking, and web-native explanations
- Persistent IELTS goal, countdown, attempt history, raw scores, estimated bands, and mistake notes

## Target architecture

The target is a React + TypeScript frontend in `frontend/` and a Python FastAPI backend in `backend/`. The browser calls versioned, typed JSON endpoints; scoring, persistence, validation, learner modelling, adaptation and AI Agent tools remain in Python. PostgreSQL is the primary development/deployment database, while SQLite remains useful for isolated tests.

Dashboard, Today, Library, Review, Notebook, History, Progress, Weekly Review, IELTS Listening/Reading, Writing, Speaking/Retelling and intensive Listening now use typed `/api/v1` contracts and React pages. The superseded Sites/Vinext/D1 application has been removed. Jinja2 remains temporarily inside the FastAPI app only as a rollback path while AI/adaptive controls and final end-to-end coverage are completed; it will be removed at the verified cutover recorded in [`docs/react-fastapi-postgresql-migration.md`](docs/react-fastapi-postgresql-migration.md).

## Local resources

Copyrighted books and audio remain in the git-ignored `resources/` directory. The FastAPI app serves only approved local media and structured, proofread web content; it never publishes source PDFs.

## Architecture status

The application remains a modular monolith. Presentation calls application services, application services call domain policies and repository protocols, and SQLAlchemy implements persistence. Future agent tools must call stable services rather than database tables.

The current stack covers Cambridge G20 Tests 1–4 Listening and Reading, web-native Writing and Speaking/Retelling practice, real audio/video intensive listening, deterministic learner-profile history, explainable weakness detection and date-persisted rotating study plans. System recommendations and learner overrides are retained as an audit history. Dashboard, Weekly Review, History and Progress read persisted evidence without inventing missing study time; the permanent Library, Notebook and configurable multi-target spaced-review queue are also usable. The next milestone is migrating the existing AI feedback, weekly coaching and approval-gated adaptive-plan controls into React before removing the Jinja rollback path.

## Run the split application

Run PostgreSQL, FastAPI and the React production build together:

```bash
docker compose up --build
```

Then open <http://127.0.0.1:5173>. FastAPI remains available at <http://127.0.0.1:8000>.

For separate development servers, see [`backend/README.md`](backend/README.md) and run `npm install && npm run dev` inside `frontend/`.
