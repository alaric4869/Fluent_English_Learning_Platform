# Adaptive learning

The first implementation is deterministic and conservative.

The baseline allocation is Listening 30, Speaking 25, Reading 30, and Vocabulary/Review 25 minutes. The planner needs at least two rated samples in at least two modules before adapting. It compares recent difficulty and confidence, transfers at most five minutes from the strongest to the weakest module, and preserves the total daily budget.

Every generated plan stores its explanation. If evidence is insufficient, the baseline remains unchanged. Resource selection scores topic fit, priority, freshness, favorites, and a penalty for recent repetition. The chosen plan is persisted once per local date and is not regenerated on refresh.

Future versions can replace `RuleBasedStudyPlanGenerator` with an AI-backed generator without changing the dashboard or plan repository. Weekly smoothing, richer subskills, comprehension accuracy, retention, and pronunciation evidence can be added as new signals.
