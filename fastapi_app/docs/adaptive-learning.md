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

IELTS currently produces the evidence, but every stage after the IELTS adapter uses generic skills, resources, sessions and repository contracts.

## Skill evaluation and classification

The first profile evaluator uses the latest five performance records per skill. Missing optional signals are removed and the remaining configured weights are normalized. No evidence produces no score, one sample is provisional, and two samples establish a baseline.

The weakness detector smooths up to four recent profile snapshots. It needs at least two scored snapshots and requires two consecutive threshold-confirming snapshots before calling a skill weak or strong. This prevents missing data and one unusual result from causing large plan changes.

## Daily planning

Default minutes are Listening 30, Speaking 25, Reading 30 and Vocabulary/Review 25. Weak skills gain 10 minutes, developing skills gain 5, and strong skills lose 5. Per-skill limits and a 120-minute daily cap are centralized in configuration. If the cap applies, only adaptive increments are reduced; base practice is preserved.

Resources are scored from explicit priority, target difficulty, completed-study recency and earlier plan assignment. Recently assigned material is penalized even if it was not completed, which produces date rotation when alternatives exist. A single available resource may still be reused, with the reason retained.

## Explainability and history

Profile snapshots, weakness assessments and daily plans store their algorithm versions, source IDs and reasons. A plan stores both its system-recommended values and current values. Each initial recommendation and validated learner override is also stored as an append-only adaptation decision. Repeating identical values does not add noise; returning to the original recommendation remains visible as a learner decision.

## Known limits

- Only Listening and Reading currently have curated real resources; missing Speaking or Vocabulary resources stay explicit rather than being fabricated.
- Planning and overrides are backend services and are not yet connected to the Today page.
- Weekly aggregation, review retention and topic balancing are later inputs.
- Rule thresholds require tuning after enough real usage data exists.
