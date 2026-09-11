# Architecture

## Shape

Fluent is a feature-oriented modular monolith deployed as one Cloudflare-compatible worker. Dependency direction is presentation → application services → domain policies → repository interfaces → D1 adapters.

The UI never accesses D1. Route handlers validate transport input and dispatch explicit use cases. Planning, resource selection, review scheduling, progress calculation, and adaptation remain deterministic domain logic.

## Modules

- `resources`: catalog operations and D1 resource repository
- `study-plan`: plan generator, plan service, configuration, and persistence
- `review`: scheduler strategy, queue service, and review history
- `learning-artifacts`: vocabulary and sentence capture
- `notebook`: personal notes and mistakes
- `analytics`: history, streaks, skill scores, and activity
- `ielts`: General Training goal, attempt lifecycle, score conversion, and local resource indexing
- `app-state`: composition root and read-model assembly

## Important boundaries

`StudyPlanGenerator`, `ReviewScheduler`, `ResourceRepository`, `StudyPlanRepository`, and `ReviewRepository` are stable replacement points. AI implementations can be introduced alongside rule-based implementations without changing React components.

Study plans are generated once per learner-local date and persisted. A plan item contains a resource snapshot so later resource changes cannot erase what was assigned historically.

Domain events can be added after the first release; current writes already use explicit application-service transitions, leaving a clear publishing point.

## IELTS local-media boundary

IELTS books and audio remain on the learner's device. The client-side local-resource adapter classifies file paths and exposes temporary `blob:` URLs to the PDF and audio players. It never posts file bytes or local paths to application APIs. D1 stores only stable study evidence such as book number, test number, skill, result, timestamps, and notes.

`IeltsView` calls the typed `/api/ielts` route, which dispatches to `IeltsService` and `IeltsRepository`. Band estimation is deterministic domain logic and remains independent from React and D1.
