# ADR 0011: Separate objective and subjective session evidence

## Decision

Allow `StudySession.accuracy` and `SkillPerformance.accuracy` to be `NULL`. IELTS submissions write objective accuracy; completed Today modules write duration, difficulty and confidence without inventing a score. The profile evaluator uses a separately versioned subjective weighting only when objective accuracy is absent.

## Context

M12 adds timed Listening, Speaking, Reading and Vocabulary sessions. Most of these modules do not yet contain automatically graded questions. Storing `0`, `1`, or a value derived from confidence as accuracy would corrupt History, Weekly Review and later AI analysis.

## Alternatives

- Store a fake accuracy inferred from the learner's difficulty rating.
- Keep daily module state outside the learning-evidence pipeline.
- Add separate session/performance tables for every exercise type.

## Reason

Nullable objective measures preserve their meaning while the shared evidence model remains extensible. Reporting can count completed sessions and tracked time while averaging accuracy only over measured exercises. The profile explanation can still use explicit self-assessment signals and clearly label them as subjective.

Migration `0011_module_sessions` also adds `StudySession.updated_at` for recoverable autosave. Downgrading removes module-session rows because the previous schema cannot represent their unknown accuracy without falsifying data.
