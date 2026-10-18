# ADR 0005: Audit manual overrides without replacing system recommendations

## Decision

Store both the system-recommended and current duration/resource on each plan item. Append one system decision at plan creation and one user decision for every effective manual change. Validate changes in `AdaptationDecisionService`, then update the item and insert its audit record in one repository transaction.

## Context

Explainable adaptation requires the application to show what it recommended, what the learner chose instead, and why. Overwriting the original fields would erase that comparison. Separate commits for the current value and audit row could also leave contradictory state after a failure.

## Alternatives

- Overwrite the plan item and rely on logs: loses product-visible history and is difficult to query.
- Store only a boolean override flag: cannot explain what changed or reconstruct learner preferences.
- Let the browser update the row directly: bypasses duration and resource-skill validation.

## Reason

System/current fields make the active plan simple to read, while append-only decisions retain the full explanation history. Service validation keeps business rules outside the UI, and a single persistence transaction prevents partial overrides. The same decision boundary can later accept a distinct, typed AI recommendation without giving an agent raw database access.
