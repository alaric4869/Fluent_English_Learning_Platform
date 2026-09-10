# ADR 0001: Use a modular monolith

## Decision

Deploy one application while separating code by learning domain and enforcing one-way dependencies.

## Context and alternatives

The product has many related workflows but one learner and one operational boundary. Microservices would increase deployment and consistency costs; an unstructured single layer would make future adaptation risky.

## Reason

A modular monolith keeps transactions and iteration simple while preserving clear extension points.
