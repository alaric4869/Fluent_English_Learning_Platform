# Fluent — Daily English

Fluent is a persistent personal English learning dashboard for an IELTS 5–5.5 learner preparing for IELTS General Training Band 6.5. It creates a date-specific daily plan, guides listening/speaking/reading/chunk practice, schedules reviews, preserves history, and turns performance signals into conservative plan adjustments.

## Product areas

- Dashboard and date-persisted daily plan
- Intensive listening sentence practice
- Shadowing and written retelling
- Focused reading and chunk capture
- Spaced review with Again / Hard / Good / Easy
- Resource library, history, progress, and notebook
- IELTS General Training workspace for Cambridge G4–G20 books, matching local audio, persistent 40-question answer sheets, automatic Listening/Reading marking, and local 精讲 links under wrong answers
- Persistent IELTS goal, countdown, attempt history, raw scores, estimated bands, and mistake notes

## Local IELTS resources

The deployed private site does not upload or bundle the learner's copyrighted books and audio. From the IELTS G page, the learner grants read access to the local `resources` directory. The browser indexes filenames, opens the selected PDF through a temporary object URL, and matches Book / Test / Part to the corresponding audio. A directory handle may be remembered in browser IndexedDB as a device-local access preference; all authoritative learning records remain in D1.

`resources/` is deliberately git-ignored and must never be included in a deployment.

## Local development

Use the project scripts to install dependencies, start the local preview, generate D1 migrations, and build the deployable worker. The local Sites runtime supplies a D1 binding declared in `.openai/hosting.json`.

## Architecture

The project is a modular monolith. UI routes call typed application services; domain strategies contain planning and review rules; repositories isolate D1 access. Future agent tools must call the same application services rather than database tables.

See `docs/architecture.md`, `docs/data-model.md`, `docs/adaptive-learning.md`, and `docs/ai-agent-architecture.md`.

## Local-first FastAPI edition

The new Python-first implementation lives in [`fastapi_app/`](fastapi_app/README.md). It currently provides web-native Cambridge G20 Test 1 Listening and Reading practice with SQLite persistence, real local audio, automatic grading, and inline Chinese explanations. The existing deployed Sites application remains unchanged while this edition is developed locally.
