# FISL Scenario and Measurement Contract

**Status:** Working design document  
**Depends on:** [`ARCHITECTURE.md`](ARCHITECTURE.md)  

This document is the next major design artifact for FISL.

Its purpose is to define the **scientific API** between scenario authors, the Factorio runtime, the external controller, and the resulting run dataset.

Implementation should not begin in earnest until the core semantics here are sufficiently precise.

---

## 1. Contract goals

The contract must make it possible to answer, unambiguously:

- What world is being used?
- What counts as the system?
- What enters and leaves it?
- What does the experiment control?
- What is measured?
- How is each metric defined?
- Over what time interval is it measured?
- What can the learner see during the run?
- What objective is being evaluated?
- What run conditions are required for reproducibility?

---

## 2. Accepted decisions

### 2.1 Experiment time and phases

Accepted in [`adr/0001-experiment-time-and-phases.md`](adr/0001-experiment-time-and-phases.md).

Key consequences:

- Factorio map ticks are the authoritative experiment clock.
- Simulation seconds/minutes compile to exact integer ticks.
- Wall time and game speed do not define simulation-time metrics.
- Pause behavior is a protocol concern and does not advance experiment time.
- V1 phases are ordered, contiguous, fixed-duration half-open intervals.
- Warm-up is an ordinary phase rather than a hidden clock mode.
- Metrics explicitly select their observation windows.

### 2.2 Zones and system boundaries

Accepted in [`adr/0002-zones-and-system-boundaries.md`](adr/0002-zones-and-system-boundaries.md).

Key consequences:

- A zone is a spatial selector, not the complete accounting boundary.
- V1 zones are static, rectangular, surface-qualified and tile-aligned.
- Canonical entity membership uses entity position; collision bounding boxes are for containment/integrity checks.
- A v1 system references one primary zone.
- FISL-owned boundary apparatus may be geometrically inside while semantically outside internal accounting.
- Material flow is not inferred from raw geometric crossing; explicit ports define authoritative boundary transactions.

### 2.3 Material ports, supply, and demand

Accepted in [`adr/0003-material-ports-supply-demand.md`](adr/0003-material-ports-supply-demand.md).

Key consequences:

- Ports are explicit logical system-boundary interfaces, with `source` and `sink` directions.
- Demand is an external process attached to a sink, not a port direction.
- Port staging apparatus is external to normal WIP accounting.
- V1 port accounting uses deterministic per-tick settlement.
- Sources support replenish and scheduled modes.
- Scheduled supply may use zero, finite, or unbounded external storage, preserving backlog/loss observability.
- Sink delivery and demand fulfillment remain distinct facts.

### 2.4 Primitive observations and tick pipeline

Accepted in [`adr/0004-primitive-observations-and-tick-pipeline.md`](adr/0004-primitive-observations-and-tick-pipeline.md).

Key consequences:

- Factorio event callbacks are sensor inputs; FISL primitive observations are normalized scientific facts.
- One `on_tick` coordinator is the single writer of authoritative experiment state.
- Primitive facts distinguish interval observations, point-state samples, and instantaneous events/actions.
- Point samples represent the prepared state for the upcoming interval.
- Observation methods/provenance travel with primitive data.
- Missing observations are never silently interpreted as zero.

### 2.5 WIP, inventory, and flow units

Accepted in [`adr/0005-wip-inventory-and-flow-unit-semantics.md`](adr/0005-wip-inventory-and-flow-unit-semantics.md).

Key consequences:

- Physical inventory vectors and scalar WIP are distinct concepts.
- Scalar WIP requires an explicit common flow-unit basis.
- Canonical Little's Law labs use conserved workpiece families where appropriate.
- WIP begins at source admission and ends at sink delivery.
- Supported holder coverage includes process inventories, active crafts, belts, inserter hands, buffers, and internal dropped work.
- Unsupported carriers produce coverage/protocol problems rather than silent undercounting.
- Conserved work-unit flows support WIP balance diagnostics.

### 2.6 Throughput and flow rates

Accepted in [`adr/0006-throughput-and-boundary-flow-rate-semantics.md`](adr/0006-throughput-and-boundary-flow-rate-semantics.md).

Key consequences:

- Throughput is a derived rate over an explicit simulation-time window.
- Completion sink `sink_delivery` observations provide the authoritative numerator.
- Input rate, output rate, fulfillment rate, and system throughput are distinct.
- Surplus completed output still counts as throughput; scrap/loss does not by default.
- A `flow` concept ties WIP/throughput/cycle-time compatibility to common work units and boundaries.
- FISL does not expose an unqualified instantaneous-throughput metric.

### 2.7 Production machine state classification

Accepted in [`adr/0007-machine-state-classification.md`](adr/0007-machine-state-classification.md).

Key consequences:

- Raw Factorio status remains an auditable primitive observation.
- Production-state classification is derived and entity-family-aware.
- Classification separates actual activity/progress from constraint/cause and a convenience headline.
- Productive operation is established from actual process progress rather than `working`/`is_crafting` labels alone.
- Starved, blocked, unavailable, disabled, idle-other, and unclassified remain mechanistically distinct.
- Brownout/low-power conditions may coexist with productive operation.

### 2.8 Service level and demand cohorts

Accepted in [`adr/0008-service-level-and-demand-cohort-semantics.md`](adr/0008-service-level-and-demand-cohort-semantics.md).

Key consequences:

- FISL does not expose a bare ambiguous `service_level` metric.
- V1's canonical service measure is quantity-based `on_time_item_rate` with an explicit maximum wait.
- Demand uses FIFO age cohorts for timing/provenance without pretending cohorts are orders.
- Service metrics select demand by creation cohort and observe fulfillment through the relevant deadline horizon.
- Unobserved deadlines are unresolved/censored, not automatically late.
- Backlog metrics remain distinct from customer service rate.

---

## 3. Core concepts to define

The contract must define at least:

1. `scenario`
2. `experiment`
3. `phase`
4. `zone`
5. `entity_set`
6. `port`
7. `source`
8. `demand` / `sink`
9. `observation`
10. `flow`
11. `metric`
12. `aggregation`
13. `objective`
14. `visibility`
15. `run`
16. `provenance`
17. `reset` / `replay`

---

## 4. Measurement terms requiring explicit semantics

The first pass must define the meaning and admissible measurement methods for:

- throughput;
- input rate;
- output rate;
- WIP;
- inventory;
- productive time;
- starved time;
- blocked time;
- unavailable time;
- utilization;
- demand;
- fulfillment;
- backlog;
- service level;
- cycle time / flow time;
- order response time.

No metric should exist in the runtime only as an informal label.

---

## 5. Design questions to resolve

### 5.1 Scenario identity and versioning

- Is a scenario version SemVer?
- What exactly is hashed for provenance?
- Does changing only prose/learning metadata change the experiment identity?
- How are schema versions distinguished from scenario versions?

### 5.2 Time — ACCEPTED

See ADR 0001.

### 5.3 System boundaries — ACCEPTED

See ADR 0002.

### 5.4 Ports — ACCEPTED

See ADR 0003.

### 5.5 Primitive observations — ACCEPTED

See ADR 0004.

### 5.6 WIP — ACCEPTED

See ADR 0005.

### 5.7 Throughput — ACCEPTED

See ADR 0006.

### 5.8 Machine state — ACCEPTED

See ADR 0007.

### 5.9 Service level — ACCEPTED

See ADR 0008.

### 5.10 Cycle time

Because normal Factorio materials are fungible and transformations generally do not preserve unique part identity, direct end-to-end item cycle time is not universally observable.

Potential allowed methods:

- `cohort_completion_time`
- `transport_traversal_time`
- `little_law_derived`
- future genuinely identity-tracked work-unit methods where the apparatus supports them

Each reported result must retain the measurement method and cannot imply stronger observability than the method provides.

### 5.11 Aggregation

For time-varying values such as WIP:

- sample every N ticks?
- event-based integration?
- time-weighted mean?
- min/max/percentile?

The authoritative semantics must not depend accidentally on UI refresh frequency.

### 5.12 Visibility

Need at least these conceptual audiences:

- learner live;
- learner post-run;
- instructor;
- debug/internal.

Later organizational work should extend this model to named roles rather than replacing it.

### 5.13 Objectives

Need separation among:

- measured values;
- constraints/requirements;
- scalar score;
- Pareto/multi-objective comparisons.

V1 may support only simple thresholds and minimize/maximize objectives, but the data model should not assume every experiment reduces naturally to one score.

### 5.14 Reset and replay

- What exactly returns to baseline on reset?
- Is resetting implemented by reloading the baseline save rather than trying to undo player actions?
- Are run IDs always unique even with identical scenario/seed?
- What guarantees can be made about a repeated deterministic run?

---

## 6. Initial scenario shape under discussion

This remains illustrative until the final schema pass. The accepted ADRs increasingly suggest `flow` as a shared object for WIP/throughput/cycle-time compatibility.

---

## 7. Contract design principles

The contract should satisfy these rules:

1. **Explicit beats inferred.** Do not guess system boundaries or metric intent from arbitrary factory geometry.
2. **Primitive observations before derived metrics.** Preserve enough raw data to audit derived values.
3. **Measurement method travels with the result.** A number without semantics is not a scientific measurement.
4. **Experiment time is simulation time.** UI/render/network timing must not define experiment behavior.
5. **Student visibility is separate from collection.** A metric may be recorded without being shown live.
6. **Scenario and world are separable.** A single baseline factory can support multiple experiments.
7. **Future stochastic behavior must fit the same interfaces.** Constant schedules are v1 policies, not hard-coded assumptions.
8. **Future role-based information control must extend visibility.** Do not bake single-player omniscience into the schema.
9. **Run provenance is mandatory.** Every result should be traceable to a scenario, world, software configuration, and seed.
10. **The schema should reject ambiguity early.** Invalid measurement definitions should fail validation before Factorio starts.

---

## 8. Recommended order for the next design session

Work through the contract in this sequence:

1. **Time and experiment phases** — accepted in ADR 0001.
2. **Zones/system boundaries** — accepted in ADR 0002.
3. **Ports/source/demand** — accepted in ADR 0003.
4. **Primitive observations** — accepted in ADR 0004.
5. **WIP** — accepted in ADR 0005.
6. **Throughput** — accepted in ADR 0006.
7. **Machine-state classification** — accepted in ADR 0007.
8. **Service level** — accepted in ADR 0008.
9. **Cycle-time methods** — explicitly address fungibility/observability.
10. **Aggregation/windows** — make time-varying metrics rigorous.
11. **Visibility/objectives** — pedagogical presentation and evaluation.
12. **Run provenance/reset/replay** — reproducibility contract.
13. **Draft `fisl/v1` schema** — only after semantics are agreed.

---

## 9. Definition of done for this contract

This document is ready to become an implementation specification when we can take each of Labs 0–6 from the architecture document and answer all of the following without informal interpretation:

- what the starting world is;
- where its system boundary lies;
- what FISL controls;
- what Factorio controls;
- exactly what is measured;
- how each number is calculated;
- when measurement begins and ends;
- which measurements the student can see;
- what constitutes success;
- what files/data make the run reproducible.

At that point, the first Lua and Python modules should become largely mechanical implementations of the agreed contract.
