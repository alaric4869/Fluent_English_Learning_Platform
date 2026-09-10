# AI agent architecture

An AI agent is an application client, not a database administrator.

Future agent tools will call narrow services such as `getTodayPlan`, `getRecentStudyHistory`, `getSkillProfile`, `getDueReviews`, `searchResources`, `recommendResources`, `createDailyPlan`, `updateDailyPlan`, `getRecentMistakes`, and `saveRecommendation`.

Inputs and outputs must use validated, versioned contracts. Authorization, limits, audit data, and manual-override rules remain in the application layer. Provider adapters implement a future `AIProvider` interface; OpenAI, Anthropic, Gemini, or a mock provider must not leak SDK types into learning modules.

Generated recommendations must include measurable evidence and must be reviewable by the learner before consequential plan changes.
