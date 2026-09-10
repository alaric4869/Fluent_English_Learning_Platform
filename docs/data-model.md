# Data model

The schema separates catalog content, dated assignments, actual study, captured artifacts, reviews, and performance evidence.

- `learning_resources` stores reusable catalog material and validated JSON lesson content.
- `resource_user_states` stores learner-specific favorites separately from shared seed content.
- `study_days` is unique by learner and local date.
- `study_plan_items` stores the assignment, status, instructions, ratings, and a resource snapshot.
- `study_sessions` stores actual start/completion time and active seconds.
- `vocabulary_items`, `saved_sentences`, and `notebook_entries` preserve learner-created artifacts with source links.
- `review_items` stores the current schedule; `review_attempts` is append-only history.
- `performance_signals` stores structured difficulty and confidence observations for later skill analysis.

All persistent learner records carry a `user_id`. Seed resources have no owner; manually added resources belong to the current learner. Referenced user resources are archived instead of hard-deleted.

Indexes reflect actual application queries: daily plan uniqueness, resources by module, reviews by due date, user history, and performance by skill.
