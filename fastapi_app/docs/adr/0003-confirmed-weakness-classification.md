# ADR 0003: Confirm strong and weak classifications across profile history

## Decision

Classify each skill through a replaceable `WeaknessDetector`. The initial deterministic implementation smooths recent profile snapshots, requires a minimum of two scored snapshots, and requires two consecutive threshold-confirming snapshots before assigning `weak` or `strong`. Persist every materially different assessment with its source snapshot IDs and measurable reasons.

## Context

Adaptive planning needs a stable description of learner needs. Treating missing data as low ability would send the learner unnecessary work, while reacting to one unusually poor result would make daily plans change too aggressively. Planning decisions also need to remain explainable after the underlying profile has advanced.

## Alternatives

- Classify only the latest score: responsive, but too sensitive to one-off results.
- Use a large statistical or AI model immediately: more flexible, but not reproducible with the small amount of current evidence.
- Store only the latest classification: simpler, but loses the evidence behind historical plan changes.

## Reason

Confirmation rules provide a conservative, testable baseline and explicitly separate unknown ability from weakness. Immutable assessments make future recommendations auditable. The interface allows a more advanced statistical or AI detector to be introduced later without changing the learner-profile or presentation layers.
