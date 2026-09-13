# Adaptive English Learning Agent

This repository is becoming a Python-first adaptive English learning system. Its product loop is:

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

## Current implementation direction

The formal target architecture is the local-first FastAPI application in `fastapi_app/`: FastAPI, SQLAlchemy, Pydantic, SQLite, Jinja2, HTML/CSS, and only the JavaScript required for browser interaction. Scoring, persistence, validation, learner modelling, and future adaptation stay in Python.

The previous Sites/Vinext application is retained temporarily for migration audit only. Do not delete it until its useful UI, content-processing logic, data, and assets have been accounted for. It must not become a second long-term product architecture.

## Local resources

Copyrighted books and audio remain in the git-ignored `resources/` directory. The FastAPI app serves only approved local media and structured, proofread web content; it never publishes source PDFs.

## Architecture status

The application remains a modular monolith. Presentation calls application services, application services call domain policies and repository protocols, and SQLAlchemy implements persistence. Future agent tools must call stable services rather than database tables.

The current FastAPI slice covers Cambridge G20 Test 1 Listening and Reading, converts submitted work into the learning-data pipeline, maintains deterministic Learner Profile history, records explainable strong/weak skill assessments, and serves a date-persisted Today plan with rotating resources. System recommendations and learner overrides are retained as an audit history. The next milestone is progress/history read models and broader real learning content, not bulk unverified IELTS import.

## Run the FastAPI edition

See [`fastapi_app/README.md`](fastapi_app/README.md). The existing deployed Sites application remains unchanged while the Python edition is developed and verified locally.
