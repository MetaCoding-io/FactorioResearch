# FISL Scenario and Measurement Contract

**Status:** Accepted / implementation-ready  
**Spec:** `fisl/v1`  
**Depends on:** [`ARCHITECTURE.md`](ARCHITECTURE.md)  
**Implementation handoff:** [`FISL_V1_PRD.md`](FISL_V1_PRD.md) and [`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md)

This document is the index/summary for the **scientific API** between scenario authors, the Factorio runtime, the Python controller, and the resulting run dataset.

The detailed normative reasoning lives in the accepted ADRs. The schema document turns those decisions into the authoring/resolved data model. The PRD turns them into implementation requirements.

The guiding rule remains:

> **Measurement semantics must be settled before implementation makes them implicit.**

---

## 1. Contract goals

A FISL v1 scenario/run must be able to answer unambiguously:

- What baseline Factorio world is being used?
- What counts as the production system?
- What enters and leaves it?
- What does FISL control versus ordinary Factorio?
- What is measured?
- How is each number calculated?
- What is the measurement method and unit?
- Over what simulation-time interval/population is it measured?
- What can the learner see live/post-run?
- What objective is being evaluated?
- What run/protocol/coverage conditions apply?
- Which artifacts/software/seed make the run reproducible?
- What exactly happens on reset/retry?

---

## 2. Accepted decision map

### 2.1 Experiment time and phases

[`adr/0001-experiment-time-and-phases.md`](adr/0001-experiment-time-and-phases.md)

- Factorio simulation ticks are authoritative.
- Simulation seconds/minutes compile exactly to ticks.
- V1 phases are fixed-duration, ordered, contiguous, half-open intervals.
- Warmup is an ordinary phase.
- Pause does not advance experiment time.
- Starts/transitions/end happen on clean tick boundaries.

### 2.2 Zones and system boundaries

[`adr/0002-zones-and-system-boundaries.md`](adr/0002-zones-and-system-boundaries.md)

- Zones are spatial selectors, not complete accounting boundaries.
- V1 zones are static rectangular surface-qualified regions.
- Entity position determines spatial membership; collision box supports containment diagnostics.
- V1 system references one primary zone.
- Material crossing is not inferred from arbitrary geometry.

### 2.3 Ports, supply, demand

[`adr/0003-material-ports-supply-demand.md`](adr/0003-material-ports-supply-demand.md)

- Ports are explicit one-way source/sink accounting interfaces.
- Demand is a process attached to a sink, not a port direction.
- Source withdrawal and sink delivery are authoritative boundary facts.
- Sources support replenish and exact scheduled modes.
- Scheduled supply has zero/finite/unbounded external storage with observable backlog/loss.
- Customer shortages use FIFO backlog semantics in v1.

### 2.4 Primitive observations and tick pipeline

[`adr/0004-primitive-observations-and-tick-pipeline.md`](adr/0004-primitive-observations-and-tick-pipeline.md)

- Factorio callbacks are sensor inputs; normalized FISL facts are the scientific observations.
- One simulation-tick coordinator is the authoritative experiment-state writer.
- Facts distinguish interval observations, point-state samples, and instantaneous events/actions.
- Point sample at `T` represents prepared state for `[T,T+1)`.
- Missing observations are never silently zero.

### 2.5 WIP and flow units

[`adr/0005-wip-inventory-and-flow-unit-semantics.md`](adr/0005-wip-inventory-and-flow-unit-semantics.md)

- Physical inventory and scalar WIP are distinct.
- Scalar WIP needs an explicit common flow-unit basis.
- Canonical Little's Law labs use conserved workpiece families.
- WIP lifetime begins after source admission and ends at completion-sink delivery.
- V1 holder coverage includes process inventories, active crafts, unique belt lines, inserter hands, buffers, and internal dropped work.
- Unsupported carriers create coverage/protocol conditions rather than silent undercounting.
- Conserved flows support WIP balance diagnostics.

### 2.6 Throughput

[`adr/0006-throughput-and-boundary-flow-rate-semantics.md`](adr/0006-throughput-and-boundary-flow-rate-semantics.md)

- Throughput is a derived rate over an explicit simulation-time window.
- Completion `sink_delivery` is the authoritative numerator.
- Input rate, output rate, fulfillment rate, and system throughput are distinct.
- Surplus completed output counts as throughput; scrap/loss does not by default.
- No unqualified instantaneous throughput.
- `flow` is the compatibility anchor for WIP/TH/CT.

### 2.7 Production-machine state

[`adr/0007-machine-state-classification.md`](adr/0007-machine-state-classification.md)

- Raw Factorio status is retained.
- Classification is derived and entity-family/version aware.
- Separate actual activity/progress from cause/constraint and headline state.
- Headline states include productive, starved, blocked, unavailable, disabled, idle-other, unclassified.
- Productive is based on actual craft progress/completion evidence.
- Low power may coexist with productive progress.

### 2.8 Customer service

[`adr/0008-service-level-and-demand-cohort-semantics.md`](adr/0008-service-level-and-demand-cohort-semantics.md)

- No ambiguous bare `service_level` metric.
- Canonical v1 service is `on_time_item_rate` with explicit maximum wait.
- Demand uses FIFO age cohorts without pretending they are customer orders.
- Cohort-selection window is distinct from fulfillment observation horizon.
- Unobserved deadlines are unresolved/censored, not automatically late.
- Backlog magnitude/time remains separate from service rate.

### 2.9 Cycle time

[`adr/0009-cycle-time-and-flow-time-measurement.md`](adr/0009-cycle-time-and-flow-time-measurement.md)

- Production cycle time is residence from declared flow admission through completion.
- Process time, transport time, customer wait, cohort response, and production cycle time are distinct.
- Every result carries its measurement method/directness class.
- Generic fungible Factorio production does not receive fictitious per-item identity.
- Canonical continuous-flow v1 method is `little_law_derived = average WIP / throughput`.
- Controlled isolated probes can provide direct residence time under explicit guarantees.
- Finite-window interpretation remains qualified/auditable.

### 2.10 Aggregation and observation windows

[`adr/0010-aggregation-and-observation-windows.md`](adr/0010-aggregation-and-observation-windows.md)

- Ordinary windows are explicit contiguous half-open intervals.
- State `X(T)` integrates over `[T,T+1)` using left-boundary occupancy.
- WIP/backlog unit-ticks are first-class exact quantities.
- Machine-state duration uses classified intervals.
- No bare utilization without an explicit denominator.
- Missing coverage does not silently shrink denominators.
- Time percentiles are time-weighted; demand waits are quantity-weighted.
- V1 quantiles use deterministic weighted nearest rank.
- Rolling window at `T` is `[T-L,T)`.

### 2.11 Metric visibility

[`adr/0011-metric-visibility-and-disclosure.md`](adr/0011-metric-visibility-and-disclosure.md)

- Collection, evaluation, and disclosure are independent.
- V1 audiences: learner-live, learner-post-run, instructor, debug.
- Learner disclosure is allowlist-based.
- Hidden values may still be collected/evaluated.
- Objective rule/status/value disclosure can differ.
- Visibility is part of the experimental condition/provenance.

### 2.12 Objectives

[`adr/0012-objectives-and-evaluation-semantics.md`](adr/0012-objectives-and-evaluation-semantics.md)

- Metrics state facts; objectives evaluate named metrics.
- V1 supports threshold requirements and minimize/maximize preferences.
- No implicit weighted scalar score.
- Incomplete/no-data objective dependencies yield undetermined.
- Protocol validity is separate from objective outcome.
- Multiple preferences remain an explicit comparison vector.

### 2.13 Run provenance

[`adr/0013-run-provenance-and-reproducibility.md`](adr/0013-run-provenance-and-reproducibility.md)

- Every attempt has a unique run ID.
- Scenario version is human metadata; hashes provide exact identity.
- Store source/package identity and canonical resolved experiment identity.
- Baseline save is immutable and cryptographically hashed.
- Record Factorio/FISL/controller/mod/compiler identity and seed.
- Reproducibility fingerprint identifies controlled input condition, not player actions.
- Authoritative telemetry is durable file-backed data.

### 2.14 Reset/repeat/replay

[`adr/0014-reset-repeat-and-replay-semantics.md`](adr/0014-reset-repeat-and-replay-semantics.md)

- Reset reloads the immutable baseline; no arbitrary undo engine.
- Every retry is a new run.
- Reset, repeat, and replay are distinct concepts.
- Same controlled condition does not imply same learner actions.
- Canonical measured v1 runs avoid mid-run save/load.
- Final saves are outputs, never implicit baselines.

### 2.15 Python ↔ Factorio transport

[`adr/0015-controller-runtime-transport.md`](adr/0015-controller-runtime-transport.md)

- Canonical runtime is a controller-launched local Factorio server.
- Learner uses a normal graphical Factorio client.
- RCON is low-volume configuration/lifecycle control only.
- Lua receives resolved canonical JSON via a versioned chunked protocol.
- Lua remains authoritative for clean tick start/phases/runtime behavior.
- Authoritative telemetry is file-backed through Factorio `script-output`.
- Same topology supports headless integration tests.

### 2.16 Entity sets

[`adr/0016-entity-set-membership.md`](adr/0016-entity-set-membership.md)

- Entity sets are analytical selectors distinct from system boundaries.
- Production sets are dynamically maintained as learners redesign factories.
- Membership follows canonical prepared-boundary semantics.
- Pooled machine-time uses explicit subject eligibility intervals.
- New/removed machines do not retroactively distort denominators.
- Overlapping analytical sets are allowed.

---

## 3. Implementation schema

The accepted authoring/runtime schema is defined in:

[`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md)

Key implementation distinction:

```text
human authoring YAML
        |
        v
Python strict typed compiler
        |
        v
canonical resolved JSON
        |
        v
Factorio Lua runtime
```

Lua never needs to interpret authoring shortcuts or independently invent measurement semantics.

---

## 4. Core v1 concepts

The implementation must provide typed concepts for at least:

```text
scenario
experiment
phase
zone
system
entity_set
port
supply
demand
observation
flow
metric
aggregation
objective
visibility
run
provenance
reset/repeat
```

`flow` is the shared compatibility object for system-level WIP, throughput, and cycle time.

---

## 5. Measurement vocabulary

The initial implementation must distinguish explicitly among:

```text
physical inventory
WIP
input rate
output rate
throughput
productive/starved/blocked/unavailable/disabled time
state fractions with declared denominator
demand created/fulfilled/backlog
on-time item rate
customer wait
production flow cycle time
transport/process/probe/cohort times
upstream supply pending/loss
```

No runtime metric should exist only as an informal dashboard label.

---

## 6. Validity model

FISL retains distinct dimensions:

```text
measurement coverage/completeness
objective result
experiment/protocol validity
interpretation/suitability where relevant
```

A run can pass an objective yet be protocol-flagged, or be protocol-clean while a metric is incomplete.

Data is preserved in either case.

---

## 7. Labs 0–6 validation

The contract has been validated against the first course in:

[`FACTORY_PHYSICS_LABS_V1.md`](FACTORY_PHYSICS_LABS_V1.md)

The important conclusion is:

> Factory Physics Labs 0–6 can be expressed through the generic `fisl/v1` mechanisms without lab-ID-specific runtime code.

That document also defines the deterministic integration fixture suite required during implementation.

---

## 8. Definition of done

The contract-definition issue is complete because we can now answer for each Lab 0–6:

- starting world/baseline;
- system boundary;
- FISL-controlled inputs;
- ordinary Factorio-controlled mechanics;
- exact measurements/methods;
- exact measurement windows/populations;
- learner disclosure;
- objective evaluation;
- reproducibility/reset artifacts.

Implementation should proceed from:

1. [`FISL_V1_PRD.md`](FISL_V1_PRD.md)
2. [`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md)
3. accepted ADRs
4. [`FACTORY_PHYSICS_LABS_V1.md`](FACTORY_PHYSICS_LABS_V1.md)

If implementation discovers that an accepted semantic is impossible or materially wrong against the pinned Factorio runtime, write a superseding ADR rather than silently changing the contract.
