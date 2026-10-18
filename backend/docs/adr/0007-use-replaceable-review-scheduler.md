# 0007 · Use a replaceable review scheduler

## Decision

Spaced-review transitions are calculated through the provider-neutral `ReviewScheduler` interface. The first implementation is deterministic and configuration-driven. Current review state and immutable attempts are persisted separately.

## Context

The first product version needs an understandable Day 1 / 3 / 7 / 14 / 30 rhythm, but retention data may later justify FSRS or an AI-assisted strategy. Routes, templates and database adapters must not contain interval decisions.

## Alternatives

- Hard-code the next dates in the Review route.
- Store only the latest date without attempt history.
- Adopt a sophisticated retention algorithm before enough learner evidence exists.

## Reason

A small deterministic policy is testable and explainable now. The stable scheduler contract allows a later algorithm to consume richer retention evidence without changing the Review UI or granting an AI agent raw database access. Immutable attempts preserve the evidence needed to evaluate that future change.
