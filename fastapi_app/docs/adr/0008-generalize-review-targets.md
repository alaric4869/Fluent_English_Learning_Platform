# 0008 · Generalize review targets without generic content records

## Decision

`ReviewItem` owns scheduling and mastery state and references exactly one reviewable target. The first target types are `vocabulary` and `saved_sentence`. Vocabulary, listening, speaking and Notebook content remain separate domain concepts and services.

## Context

The fixed-interval scheduler initially returned complete vocabulary records. Difficult listening sentences need the same Again / Hard / Good / Easy behavior, and future pronunciation or mistake items may also become reviewable. Copying the scheduler and attempt tables per content type would fragment retention history; merging all content into one polymorphic text table would weaken domain validation.

## Alternatives

- Add a second listening-only scheduler and attempt history.
- Put all chunks, sentences, notes and future content in one generic item table.
- Keep mastery duplicated on every content record and synchronize it with the review item.

## Reason

A small typed target union keeps one deterministic review policy and one immutable attempt stream while preserving feature boundaries. The application resolves target content through its owning service; neither the review engine nor a future AI agent gets direct access to unrelated tables. Moving mastery to `ReviewItem` also removes a duplicate source of truth.
