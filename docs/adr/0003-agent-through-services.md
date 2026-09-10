# ADR 0003: AI agents use application services

## Decision

Future agents receive narrow tools implemented by the application layer and never unrestricted table access.

## Context and alternatives

Direct database access is powerful but bypasses validation, explanations, ownership checks, and audit history.

## Reason

Service-backed tools are predictable, testable, provider-independent, and safe to replace.
