# 0015 · Authorize typed Agent tools at the application boundary

## Decision

Give AI providers only an allow-listed catalogue of strict Pydantic tools. Resolve
learner identity from an authorized execution context and dispatch every tool through
an existing application service. Start with read-only permissions and an offline mock
provider.

## Context

The future learning Agent needs profile, history, review, plan and resource evidence.
Passing a database session or accepting a model-supplied learner key would bypass the
domain rules, make authorization unreliable and tightly couple the system to one AI
runtime. Networked model behavior also needs deterministic tests before it can affect
plans or learner-authored work.

## Alternatives considered

- Give the model SQL or ORM access: flexible, but unsafe, difficult to audit and able
  to bypass application invariants.
- Put provider calls inside each feature service: expedient, but spreads vendor types
  through the learning domain and makes replacement expensive.
- Accept arbitrary dictionaries in one generic tool: small surface area, but weak
  validation and an unstable contract.

## Reason

Typed contracts make the tool surface inspectable and testable. Authorization is
enforced both when publishing the catalogue and again at execution. The provider loop
can change independently, while deterministic services remain the explainable
baseline. Separate future write permissions make plan changes explicit rather than a
hidden consequence of reading evidence.
