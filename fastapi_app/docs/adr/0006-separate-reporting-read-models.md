# 0006 · Separate reporting read models

## Decision

History and Progress use focused application services and domain read models over existing repository interfaces. Templates do not query SQLAlchemy models, and reporting does not create a second learner-profile algorithm.

Estimated completed-plan minutes and measured session duration are separate fields and separate UI metrics.

## Context

The same persisted plans and learning evidence serve daily operation, historical recall and long-term analytics. Mixing reporting queries into routes or recomputing skill scores in a page would create competing sources of truth. Treating planned minutes as elapsed time would also make early progress charts look more precise than the collected evidence allows.

## Alternatives

- Query tables directly in each History/Progress route.
- Store precomputed dashboard counters on the learner record.
- Treat the duration assigned to every completed module as actual study time.

## Reason

Read-model services keep presentation simple, let SQL queries evolve independently, and reuse the established profile/weakness services. Honest time semantics make future timers additive: real duration coverage can improve gradually without migrating or reinterpreting earlier estimates.
