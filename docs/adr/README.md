# Architectural Decision Records

FISL will use lightweight Architectural Decision Records (ADRs) for implementation choices that should remain understandable after the surrounding discussion has disappeared.

The architecture document records the current system design and rationale. ADRs record **specific decisions made while implementing that design**, especially when reasonable alternatives exist.

Examples likely to deserve ADRs:

- scenario serialization/schema technology;
- how scenario ports bind to Factorio entities;
- telemetry file format;
- exact Python ↔ Factorio control channel;
- WIP sampling/integration implementation;
- save/reset strategy;
- Factorio version/expansion support policy;
- whether and how FLE code is reused.

Suggested format:

```text
# ADR-NNN: Title

Status: proposed | accepted | superseded
Date: YYYY-MM-DD

## Context

What problem requires a decision?

## Decision

What are we choosing?

## Alternatives considered

What else was plausible?

## Consequences

What becomes easier, harder, required, or forbidden because of this decision?
```

Keep ADRs short. The purpose is durable reasoning, not bureaucracy.
