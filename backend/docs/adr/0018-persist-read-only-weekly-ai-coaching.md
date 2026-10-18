# 0018 · Persist read-only weekly AI coaching

## Decision

Expose the existing provider-neutral Agent through one explicit Weekly Review action.
Restrict its principal to four read-only evidence tools, require all four tools to be
used, and persist the final plain-text report as a separate append-only artifact.

## Context

The backend already supports typed Agent tools and an optional OpenAI Responses
adapter, but the learner could not invoke it from the product. A useful first surface
must be explainable, survive refresh, remain safe when the API is unconfigured, and
must not turn model prose into measured performance or automatic plan mutations.

## Alternatives

- Add a free-form chatbot: rejected because its purpose, data access and expected
  actions would be unclear.
- Generate on every page load: rejected because it creates hidden cost, latency and
  network dependence.
- Store AI output as skill evidence: rejected because generated interpretation is not
  an observed learner result.
- Let the Agent save plan changes: rejected because plan overrides require explicit
  learner control.

## Reason

A fixed, explicit weekly coaching use case has a narrow permission boundary and an
auditable evidence trail. Required-tool verification prevents unsupported prose, while
append-only persistence preserves prior output without changing source learning facts.
