# Architectural Decision Records

FISL uses lightweight ADRs to preserve not just implementation choices, but the reasoning behind scientific and pedagogical contract decisions.

The architecture document records broad system design and rationale. ADRs record **specific decisions** that should remain understandable after the surrounding discussion has disappeared.

## Status values

- **Proposed** — under active discussion.
- **Accepted** — adopted for the current architecture/contract.
- **Superseded** — replaced by a later ADR.
- **Rejected** — considered but not adopted.

`Accepted` is a design status, not a claim that every Factorio-specific implementation hypothesis has been empirically exercised. Factorio-sensitive assumptions are tracked separately in [`../RUNTIME_VALIDATION.md`](../RUNTIME_VALIDATION.md). Individual ADRs may carry `Runtime validation: Pending/Confirmed` annotations.

## Accepted v1 decisions

- [ADR 0001: Experiment Time and Phase Semantics](0001-experiment-time-and-phases.md) — **Accepted**
- [ADR 0002: Zones and System Boundary Semantics](0002-zones-and-system-boundaries.md) — **Accepted**
- [ADR 0003: Material Ports, Supply, Demand, and Boundary Transactions](0003-material-ports-supply-demand.md) — **Accepted**
- [ADR 0004: Primitive Observations and Tick-Pipeline Semantics](0004-primitive-observations-and-tick-pipeline.md) — **Accepted**, runtime validation pending
- [ADR 0005: WIP, Inventory, and Flow-Unit Semantics](0005-wip-inventory-and-flow-unit-semantics.md) — **Accepted**, superseded in part by ADR 0017
- [ADR 0006: Throughput and Boundary Flow-Rate Semantics](0006-throughput-and-boundary-flow-rate-semantics.md) — **Accepted**
- [ADR 0007: Production Machine State Classification](0007-machine-state-classification.md) — **Accepted**, runtime validation pending (RV-006/RV-007)
- [ADR 0008: Service-Level and Demand-Cohort Semantics](0008-service-level-and-demand-cohort-semantics.md) — **Accepted**
- [ADR 0009: Cycle-Time and Flow-Time Measurement Methods](0009-cycle-time-and-flow-time-measurement.md) — **Accepted**
- [ADR 0010: Aggregation and Observation-Window Semantics](0010-aggregation-and-observation-windows.md) — **Accepted**
- [ADR 0011: Metric Visibility and Disclosure Semantics](0011-metric-visibility-and-disclosure.md) — **Accepted**
- [ADR 0012: Objectives and Evaluation Semantics](0012-objectives-and-evaluation-semantics.md) — **Accepted**
- [ADR 0013: Run Provenance and Reproducibility Semantics](0013-run-provenance-and-reproducibility.md) — **Accepted**, revised to separate `ResolvedScenario` from `RunConfiguration`
- [ADR 0014: Reset, Repeat, and Replay Semantics](0014-reset-repeat-and-replay-semantics.md) — **Accepted**
- [ADR 0015: Python Controller ↔ Factorio Runtime Transport](0015-controller-runtime-transport.md) — **Accepted**, runtime validation pending (RV-008/RV-009)
- [ADR 0016: Entity-Set Selection and Membership Semantics](0016-entity-set-membership.md) — **Accepted**, runtime validation pending (RV-012)
- [ADR 0017: Conservation-Ledger WIP and Physical Census Semantics](0017-conservation-ledger-wip.md) — **Accepted**, supersedes physical-census authority for conserved-flow total WIP
- [ADR 0018: Local-Server Pause and Disconnect Profile](0018-local-server-pause-and-disconnect-profile.md) — **Accepted**, canonical POC operational profile

## Empirical gate

Before substantial implementation, execute [`../RUNTIME_VALIDATION.md`](../RUNTIME_VALIDATION.md).

The preferred first fixture is the one-workpiece vertical slice because it validates source/sink accounting, conserved-ledger WIP, census cross-checking, belt/craft adapter behavior, machine progress evidence, telemetry, and reset behavior in one small real Factorio scenario.

If a Factorio-specific assumption fails, preserve the evidence and either choose another implementation or propose a superseding ADR. Do not silently weaken measurement semantics.

## Implementation handoff

The accepted ADR set is consolidated for implementation in:

- [`../FISL_V1_PRD.md`](../FISL_V1_PRD.md) — full v1 product/runtime requirements.
- [`../FISL_V1_SCHEMA.md`](../FISL_V1_SCHEMA.md) — authoring + `ResolvedScenario` + `RunConfiguration` schema contract.
- [`../FACTORY_PHYSICS_LABS_V1.md`](../FACTORY_PHYSICS_LABS_V1.md) — Labs 0–6 contract validation and integration fixtures.
- [`../RUNTIME_VALIDATION.md`](../RUNTIME_VALIDATION.md) — empirical assumptions and spike tests required against Factorio 2.0.77.
- [`../DESIGN_REVIEW.md`](../DESIGN_REVIEW.md) — independent pre-implementation critique that motivated ADRs 0017–0018 and the revision pass.

The immediate POC scope is tracked by GitHub Issue #2 and is intentionally narrower than full v1: validate the runtime assumptions, prove a real conserved-workpiece vertical slice, and get Lab 3 / Little's Law working before implementing later-course service/visibility/objective features.

Future implementation decisions that materially change scientific behavior should receive new/superseding ADRs rather than silently changing these accepted semantics.

Likely future ADR topics include stochastic RNG/distribution semantics, reliability/failure processes, economics/cost functions, role-specific information enforcement, Factorio-version support policy, and whether/how Factorio Learning Environment code is reused.

Keep ADRs focused. Their purpose is durable reasoning, not bureaucracy.
