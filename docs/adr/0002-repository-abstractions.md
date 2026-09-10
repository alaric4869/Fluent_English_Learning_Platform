# ADR 0002: Isolate D1 behind repositories

## Decision

Application services depend on focused resource, study-plan, and review repository interfaces.

## Context and alternatives

Direct queries in UI or route handlers would couple learning behavior to Cloudflare D1. A fully generic persistence framework would add unnecessary indirection.

## Reason

Focused repositories support testing and a future PostgreSQL or synchronization adapter without hiding domain-specific queries.
