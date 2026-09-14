# ADR 0010: Derive Weekly Review from learning facts

## Decision

Generate the current Weekly Review from persisted plans, sessions, learned items and review attempts. Do not add a weekly-summary table in this milestone.

## Context

Dashboard and weekly feedback need totals, skill highlights and next-review guidance. Those values already have authoritative sources. Persisting another mutable total would create synchronization and correction problems.

The current review table stores each completed rating and the latest schedule, but not a daily snapshot of everything that was due. We therefore report completed review actions and `Good/Easy` retention, not an unprovable historical due-item completion rate.

## Alternatives

- Store one mutable weekly aggregate and update it after every activity.
- Add full due-queue snapshots before building the report.
- Derive the measurable report now and add versioned published/AI reports later.

## Reason

Derivation preserves one source of truth, keeps writes unchanged and makes the first report deterministic. A later immutable report or AI narrative can reference the same structured evidence without altering the calculations.
