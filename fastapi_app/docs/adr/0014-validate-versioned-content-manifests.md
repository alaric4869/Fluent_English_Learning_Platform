# 0014 · Validate versioned content manifests

## Decision

Import built-in learning content through an ordered JSON manifest and strict Pydantic schemas before applying any database writes. Keep each Cambridge test and the Australian real-world catalogue in separate versioned files.

## Context

The initial single seed file was safe for one test but did not scale to complete books. A malformed table, duplicate slug, partial IELTS set or inconsistent multi-answer group could otherwise fail midway through startup or create an unusable exercise. Source content also needs stable semantic blocks so tables, flowcharts and figures can preserve their layout without exposing whole PDFs.

## Alternatives considered

- One very large JSON file: simple at first, but hard to review and easy to conflict with during later imports.
- Direct SQL or ORM import scripts: flexible, but bypass typed content contracts and couple curation to persistence.
- Store page screenshots only: visually faithful, but inaccessible, unsearchable and incompatible with direct web answering.

## Reason

The manifest keeps imports repeatable and reviewable. Validation fails before persistence, while the existing upsert path retains stable IDs and learner attempts. Semantic blocks preserve source structure and keep grading independent from presentation. A future importer can produce the same contract without changing services, repositories or the IELTS workspace.
