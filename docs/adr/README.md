# Architectural Decision Records

FISL uses lightweight ADRs to preserve not just implementation choices, but the reasoning behind scientific and pedagogical contract decisions.

The architecture document records the current system design and rationale. ADRs record **specific decisions** that should remain understandable after the surrounding discussion has disappeared.

## Status values

- **Proposed** — under active discussion.
- **Accepted** — adopted for the current architecture/contract.
- **Superseded** — replaced by a later ADR.
- **Rejected** — considered but not adopted.

## Current decisions

- [ADR 0001: Experiment Time and Phase Semantics](0001-experiment-time-and-phases.md) — **Accepted**
- [ADR 0002: Zones and System Boundary Semantics](0002-zones-and-system-boundaries.md) — **Accepted**
- [ADR 0003: Material Ports, Supply, Demand, and Boundary Transactions](0003-material-ports-supply-demand.md) — **Accepted**
- [ADR 0004: Primitive Observations and Tick-Pipeline Semantics](0004-primitive-observations-and-tick-pipeline.md) — **Accepted**
- [ADR 0005: WIP, Inventory, and Flow-Unit Semantics](0005-wip-inventory-and-flow-unit-semantics.md) — **Accepted**
- [ADR 0006: Throughput and Boundary Flow-Rate Semantics](0006-throughput-and-boundary-flow-rate-semantics.md) — **Accepted**
- [ADR 0007: Production Machine State Classification](0007-machine-state-classification.md) — **Accepted**

Additional implementation choices likely to deserve ADRs include scenario serialization/schema technology, telemetry format, Python ↔ Factorio control channels, WIP integration implementation, save/reset strategy, Factorio version/expansion support, and whether/how FLE code is reused.

Keep ADRs focused. Their purpose is durable reasoning, not bureaucracy.
