# ADR 0019: Require learner approval for AI plan changes

## Decision

AI-generated duration or resource changes are stored as append-only proposals. They do not update a study plan until the learner explicitly accepts them. Acceptance or dismissal creates one uniquely linked learner-response decision.

## Context

The Agent can inspect measured learning evidence and produce useful recommendations, but model output must not silently override deterministic planning or a learner's own choices. The system also needs to explain later which suggestion was accepted or ignored.

## Alternatives

- Let the Agent update `StudyPlanItem` directly.
- Treat clicking “accept” as an ordinary manual override without linking it to the proposal.
- Store mutable accepted/dismissed status on the original AI row.

## Reason

Separate append-only proposal and response rows preserve authorship, evidence and history. A unique source link prevents conflicting responses, while applying the accepted values and writing the response in one repository transaction avoids partial state. The model retains no unrestricted database or plan-mutation access.
