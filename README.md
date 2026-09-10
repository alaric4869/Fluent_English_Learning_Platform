# Fluent — Daily English

Fluent is a persistent personal English learning dashboard for an IELTS 5–5.5 learner. It creates a date-specific daily plan, guides listening/speaking/reading/chunk practice, schedules reviews, preserves history, and turns performance signals into conservative plan adjustments.

## Product areas

- Dashboard and date-persisted daily plan
- Intensive listening sentence practice
- Shadowing and written retelling
- Focused reading and chunk capture
- Spaced review with Again / Hard / Good / Easy
- Resource library, history, progress, and notebook

## Local development

Use the project scripts to install dependencies, start the local preview, generate D1 migrations, and build the deployable worker. The local Sites runtime supplies a D1 binding declared in `.openai/hosting.json`.

## Architecture

The project is a modular monolith. UI routes call typed application services; domain strategies contain planning and review rules; repositories isolate D1 access. Future agent tools must call the same application services rather than database tables.

See `docs/architecture.md`, `docs/data-model.md`, `docs/adaptive-learning.md`, and `docs/ai-agent-architecture.md`.
