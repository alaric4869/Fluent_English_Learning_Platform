# ADR 0002: Use deterministic, immutable learner profile snapshots

## Decision

Calculate the four initial skill scores with a replaceable rule-based evaluator. Persist every materially different result as an immutable profile snapshot containing its algorithm version, evidence IDs, normalized component weights and human-readable explanation.

## Context

Adaptive planning needs a current learner profile and historical trends. A mutable score alone cannot explain earlier decisions, and an LLM-generated score would not provide a stable baseline for tests or future model comparison.

## Alternatives

- Store only four mutable score columns: simple, but destroys history and does not scale to additional skills.
- Let an AI model assign scores immediately: flexible, but difficult to reproduce, test and audit.
- Treat missing signals as average values: produces apparently complete profiles by inventing evidence.

## Reason

The deterministic evaluator is testable, configurable and explainable. Skill rows allow later expansion without changing a four-column profile schema. Missing confidence, difficulty or hard-item data stays missing and does not contribute weight, so every score is grounded in actual learning behaviour.
