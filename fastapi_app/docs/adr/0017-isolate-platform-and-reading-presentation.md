# 0017 · Isolate reading presentation and platform seams

## Decision

Split IELTS Reading presentation into source blocks and answer-bearing question
blocks in the presenter, then render them in responsive independent panes. Keep the
existing answer controls, autosave queue and Python grader unchanged. Resolve learner
identity through one FastAPI dependency, construct database engines from a provider-
neutral SQLAlchemy URL, and define cloud synchronization behind a small domain port.

## Context

Reading requires simultaneous access to long passages and questions, but Listening
must retain native tables, flowcharts and verified figures. The local application also
needs credible extension points for authentication, PostgreSQL and device sync without
making those hosted concerns mandatory or leaking them into learning rules.

## Alternatives

- Duplicate a separate Reading grader and answer form: rejected because it creates two
  sources of truth for saving and scoring.
- Rebuild the workspace as a client-side single-page app: rejected because the current
  server-rendered model already provides accessible, persistent interactions.
- Pass a learner key from browser requests: rejected because it permits identity
  spoofing and couples every endpoint to a future auth provider.
- Add background sync now: rejected because conflict resolution and remote identity are
  not yet product requirements.

## Reason

The presenter owns layout classification while domain answer identity remains stable.
Dependency-injected identity, SQLAlchemy URLs and a dormant sync port create narrow,
testable replacement points. The local SQLite application keeps identical behavior and
no database migration is required.
