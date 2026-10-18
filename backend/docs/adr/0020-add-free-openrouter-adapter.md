# ADR 0020: Add a free-only OpenRouter adapter

## Decision

Add OpenRouter as a second implementation of the existing provider-neutral Agent and
work-evaluation ports. The adapter accepts only model identifiers ending in `:free`
or OpenRouter's `openrouter/free` route and uses the OpenAI-compatible Chat
Completions API. It tries the selected Qwen model first and uses the free router once
for transient availability failures. Keep OpenAI available as a separate adapter
selected through configuration.

## Context

The local learner needs optional AI coaching without a prepaid OpenAI API balance and
may access the application from outside mainland China. Provider SDK objects and
billing rules must not leak into learning services or browser code.

## Alternatives

- Replace OpenAI throughout the application. Rejected because the existing adapter is
  working and provider replacement should be configuration-driven.
- Route through a generic model alias. Rejected because it could select a paid or
  unsuitable model without an explicit learner decision.
- Run a local model only. Retained as a future offline option, but it would impose
  hardware and installation requirements now.

## Reason

The existing `AIProvider` and `WorkEvaluator` ports already isolate model access.
Adding a free-only adapter is a localized change, preserves tests and stored results,
and prevents an accidental paid fallback while retaining future provider choice.
