# ADR 0012: Model Writing as revisioned subjective work

## Decision

Represent an IELTS Writing task as a structured `LearningResource`, keep one autosaved `WritingDraft` per learner/resource, and create an immutable `WritingSubmission` for every explicit submission. Each submission emits generic learning evidence with nullable accuracy and measurable word-count, duration, difficulty and confidence signals.

Daily planning remains a four-module experience. Listening, Speaking and Vocabulary are stable; Reading and Writing alternate deterministically by date instead of adding a permanent fifth module.

## Context

Writing was absent from the original four-value skill enum. Reusing the objective IELTS question model would require a fake accepted answer and fake auto-grading. Adding Writing as a fifth daily module would also push the baseline from 110 to 140 minutes and violate the product's 1.5–2 hour study target.

## Alternatives

- Treat Writing as a generic text note with no submission history.
- Reuse `PracticeQuestion` and mark every essay correct after submission.
- Add Writing to every day as a fifth plan item.
- Delay all Writing work until AI scoring exists.

## Reason

Revisioned drafts preserve learner work now and give a later AI evaluator stable snapshots to assess. Nullable accuracy protects analytics from fabricated scores. Date rotation introduces IELTS output practice without increasing daily cognitive load, and the policy remains a small deterministic function that a later adaptive planner can replace.
