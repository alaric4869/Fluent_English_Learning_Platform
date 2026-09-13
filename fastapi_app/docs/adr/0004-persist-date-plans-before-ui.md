# ADR 0004: Persist date plans and system recommendations before UI integration

## Decision

Generate daily plans through replaceable resource-recommendation and plan-generation policies, then persist one plan per learner/date before exposing it in Today UI. Store the system duration/resource separately from the current duration/resource on every item. Include both completed-study history and prior plan assignments in resource rotation.

## Context

The adaptive loop needs a stable answer to “what was assigned on this date?” Recomputing whenever the page opens would make history change as learner evidence changes and could erase future manual overrides. Considering only completed sessions would also repeat unfinished material on adjacent days.

## Alternatives

- Generate the plan entirely in the page: fast to display, but couples policy to UI and loses audit history.
- Recalculate on every read: always current, but destroys date stability and override intent.
- Rotate only after completion: simpler queries, but can assign the same unfinished resource on many consecutive dates.

## Reason

A date-persisted plan is predictable, testable and suitable for history. Separate system/current values make later overrides explainable. Assignment-aware rotation meets the daily-content requirement without duplicating a mutable `last_studied` field on resources.
