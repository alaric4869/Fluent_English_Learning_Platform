# 0009 · Keep learner resource state separate from resource content

## Decision

`LearningResource` stores stable material content and optional ownership. `ResourceUserState` stores one learner's favorite, saved-for-later and archived values. Resource removal in the local product is a recoverable archive, not a hard delete.

## Context

IELTS resources are already referenced by attempts, plans and study sessions. The Library also needs personal resources and per-learner organization, while future authentication and synchronization must not turn one user's favorite or archive action into a global mutation.

## Alternatives

- Add favorite and archived booleans directly to `LearningResource`.
- Hard-delete resources from the database.
- Create a second unrelated table for personal resources.

## Reason

One content model lets built-in and personal materials use the same recommendation, history and Today interfaces. A user-state relation provides multi-user-safe organization. Recoverable archive preserves foreign-key history and removes the item from future recommendations without destructive data loss.
