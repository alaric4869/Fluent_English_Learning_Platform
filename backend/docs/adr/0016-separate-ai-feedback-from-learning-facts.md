# 0016 · Separate AI feedback from learner work and measured facts

## Decision

Store AI Writing/Retelling feedback as an immutable `WorkEvaluation` linked to a
specific submission revision. Keep it out of learner-authored snapshots and the
deterministic learner profile. Record AI plan proposals as non-applied adaptation
decisions under a separate permission and actor.

## Context

Model feedback is useful but probabilistic. Treating it as an objective answer key,
overwriting the learner's response, or automatically changing tomorrow's plan would
make the feedback loop difficult to audit. Evaluation can also cost money and send
learner text to an external provider.

## Alternatives considered

- Write corrections back into the draft: convenient, but destroys authorship and
  revision history.
- Convert the model's coaching score directly into skill accuracy: simple, but mixes
  subjective provider output with objective question evidence.
- Run evaluation automatically on every submission: fast feedback, but creates a
  hidden external call and unexpected cost/data transfer.

## Reason

An explicit learner action makes the external call visible. Versioned, idempotent
evaluation records preserve provenance and can be compared or discarded later. The
deterministic plan remains the baseline; AI can explain a proposal, but only a
separate user action may apply plan changes.
