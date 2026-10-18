# 0013 · Version Speaking practice without fake scoring

## Decision

Keep the existing typed `RetellingRecord` as the current learner-authored state. Distinguish workspace-managed records from earlier manual Notebook entries, store learner/resource/sentence progress separately, and create an immutable `RetellingSubmission` for every explicit completion revision. Emit a generic Speaking session with `NULL` accuracy and structured observable/self-rated signals.

## Context

Shadowing needs fast mutable actions: a learner may relabel the same sentence many times and continuously edit an outline or improved version. History, Progress and later AI evaluation need stable evidence that cannot change when the current draft changes. The first version has no recorded voice or valid IELTS Speaking evaluator, so an objective score would be misleading.

## Alternatives

- Store all workspace state in resource JSON: rejected because learner state would mutate shared content and could not support history.
- Create a second unrelated retelling-draft concept: rejected because it would duplicate the existing Notebook domain record.
- Convert every sentence click into a scored exercise attempt: rejected because `need_practice`, `good` and `mastered` are learner practice states, not objective correctness.

## Reason

Mutable current state plus immutable submissions matches Writing's evidence boundary while preserving the earlier Notebook API. Stable sentence keys allow repeat counts without copying source text into every click. A later voice recorder can populate the existing recording reference, and a provider-neutral evaluator can attach separate rubric evidence without overwriting learner-authored work or changing the UI-to-service dependency direction.
