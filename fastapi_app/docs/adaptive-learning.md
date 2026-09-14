# Adaptive learning baseline

## Current feedback loop

The implemented backend path is deterministic and provider-neutral:

```text
Submitted activity
→ immutable learning evidence
→ immutable learner profile snapshot
→ confirmed skill assessment
→ resource recommendation
→ date-persisted study plan
```

IELTS produces objective evidence. Completed Today modules and submitted Speaking/Writing workspaces additionally produce duration, perceived-difficulty and confidence evidence with no fabricated accuracy. Every stage after these producers uses generic skills, resources, sessions and repository contracts.

## Skill evaluation and classification

The profile evaluator uses the latest five performance records per skill. Objective accuracy takes priority when present. Without objective questions, the rule-based baseline can use confidence and the inverse of perceived difficulty, and its explanation identifies the result as subjective. Missing optional signals are removed and the remaining configured weights are normalized. No evidence produces no score, one sample is provisional, and two samples establish a baseline.

The weakness detector smooths up to four recent profile snapshots. It needs at least two scored snapshots and requires two consecutive threshold-confirming snapshots before calling a skill weak or strong. This prevents missing data and one unusual result from causing large plan changes.

## Daily planning

The four-module baseline is Listening 30, Speaking 25, Vocabulary/Review 25 and either Reading 30 or Writing 30. Reading/Writing alternation is deterministic by calendar date. Weak skills gain 10 minutes, developing skills gain 5, and strong skills lose 5. Per-skill limits and a 120-minute daily cap are centralized in configuration. If the cap applies, only adaptive increments are reduced; base practice is preserved.

Resources are scored from explicit priority, target difficulty, completed-study recency and earlier plan assignment. Recently assigned material is penalized even if it was not completed, which produces date rotation when alternatives exist. A single available resource may still be reused, with the reason retained.

## Explainability and history

Profile snapshots, weakness assessments and daily plans store their algorithm versions, source IDs and reasons. A plan stores both its system-recommended values and current values. Each initial recommendation and validated learner override is also stored as an append-only adaptation decision. Repeating identical values does not add noise; returning to the original recommendation remains visible as a learner decision. Today presents these reasons directly instead of hiding them behind a black box.

## Known limits

- Listening, Reading, Writing and one G20 Test 1 real-audio Speaking practice currently have curated resources; missing Vocabulary resources stay explicit rather than being fabricated.
- Speaking evidence currently uses marked-sentence counts, time, intended chunks, difficulty and confidence. Fluency, pronunciation and lexical scores remain unknown until a later recording/transcription evaluator is explicitly invoked.
- Writing evidence currently uses word count, time, difficulty and confidence. IELTS Band criteria remain unknown until M17 adds an evaluator; the profile explanation must keep that distinction visible.
- Topic balancing and richer comprehension/listening measurements remain later inputs.
- Rule thresholds require tuning after enough real usage data exists.
