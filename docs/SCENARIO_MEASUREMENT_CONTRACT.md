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
- Material flow is not inferred from raw geometric crossing; explicit ports will define authoritative boundary transactions.

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
10. `metric`
11. `aggregation`
12. `objective`
13. `visibility`
14. `run`
15. `provenance`
16. `reset` / `replay`

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

### 5.4 Ports

- What exactly is a logical material port?
- Should v1 distinguish `source` and `sink`, with demand attached to a sink, instead of making `demand` itself a port type?
- How does a scenario bind a logical port to Factorio apparatus?
- Should the standard v1 apparatus be a FISL-owned custom container while the contract remains binding-agnostic?
- At what exact settlement point does material become internal/external?
- Are v1 authoritative boundary flows gross transactions or net per-tick inventory changes at the port?
- How is reverse flow handled?
- What source policies are needed for Factory Physics: unlimited/replenishing, rate-limited, both?
- How are fractional rates converted into deterministic discrete item releases without floating-point drift?
- What happens if a source staging buffer is full?
- Does v1 demand support backlog only, or also lost demand?
- How are deliveries before demand treated?
- How are surplus/unsolicited output and wrong-item contamination recorded?

### 5.5 WIP

- Is WIP every declared tracked item within a zone?
- Does WIP include material in machines, belts, inserter hands, trains, bots, and chests?
- How are raw material, intermediate goods, and finished goods treated?
- Can scenarios define a whitelist of WIP items?
- How do we avoid double-counting transient entity inventories?

### 5.6 Throughput

- Is throughput measured only at a declared output/sink boundary?
- Is it an event count divided by an observation window?
- Do we support rolling and whole-run throughput separately?

### 5.7 Machine state

- Which Factorio statuses map to productive, starved, blocked, unavailable, disabled, idle-other?
- Are these mappings machine-type dependent?
- How are machines that are intentionally not scheduled interpreted?

### 5.8 Utilization

The contract should likely forbid bare `utilization` and require an explicit denominator, e.g.:

- `effective_utilization = productive_time / scheduled_experiment_time`
- `available_utilization = productive_time / available_time`

The exact vocabulary remains to be settled.

### 5.9 Cycle time

Because items are fungible, direct item-level flow time is not generally observable.

Potential allowed methods:

- `order_response_time`
- `cohort_completion_time`
- `transport_traversal_time`
- `little_law_derived`

Each reported result must retain the measurement method.

### 5.10 Service level

Possible definitions include:

- item fill rate;
- order fill rate;
- on-time item rate;
- on-time order rate;
- fraction of demand fulfilled within tolerance.

A scenario must choose one explicitly.

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

This is illustrative only:

```yaml
spec: fisl/v1

scenario:
  id: fp-05-pull-production
  version: 1.0.0
  title: Production to Demand

factorio:
  baseline_save: fp-05.zip
  version: 2.0.x

experiment:
  time:
    game_speed:
      policy: fixed
      value: 1.0
    pause_policy: allowed
  phases:
    - id: warmup
      duration: 5m
    - id: measured
      duration: 20m

zones:
  factory_floor:
    surface: nauvis
    area:
      left_top: [-50, -30]
      right_bottom: [50, 30]

system:
  id: factory
  primary_zone: factory_floor
  boundary_integrity:
    entity_containment: contained

ports:
  iron_supply:
    type: source
    item: iron-plate
    schedule:
      type: constant
      rate_per_minute: 180

  customer:
    type: sink
    item: electronic-circuit
    demand:
      schedule:
        type: constant
        rate_per_minute: 60
      shortage_policy: backlog

metrics:
  - id: output_throughput
    type: throughput
    boundary: customer

  - id: average_wip
    type: wip
    zone: factory_floor
    aggregation: time_weighted_mean

objectives:
  - metric: service_level
    operator: gte
    value: 0.95

visibility:
  learner_live:
    - output_throughput
    - service_level
  learner_post_run:
    - average_wip
    - productive_time
    - starved_time
    - blocked_time
```

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
3. **Ports/source/demand** — establishes controlled boundary flows.
4. **Primitive observations** — establishes what FISL can honestly know.
5. **WIP and throughput** — first major Factory Physics measurements.
6. **Machine-state classification** — productive/starved/blocked semantics.
7. **Service level** — connects factory output to external demand.
8. **Cycle-time methods** — explicitly address fungibility/observability.
9. **Aggregation/windows** — make time-varying metrics rigorous.
10. **Visibility/objectives** — pedagogical presentation and evaluation.
11. **Run provenance/reset/replay** — reproducibility contract.
12. **Draft `fisl/v1` schema** — only after semantics are agreed.

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
