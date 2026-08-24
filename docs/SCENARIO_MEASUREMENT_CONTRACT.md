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

## 2. Core concepts to define

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

## 3. Measurement terms requiring explicit semantics

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

## 4. Design questions to resolve

### 4.1 Scenario identity and versioning

- Is a scenario version SemVer?
- What exactly is hashed for provenance?
- Does changing only prose/learning metadata change the experiment identity?
- How are schema versions distinguished from scenario versions?

### 4.2 Time

- Canonical internal unit: Factorio tick?
- How are human-friendly seconds/minutes compiled to ticks?
- How do pause and game-speed changes affect experiment time?
- Does warm-up contribute to metrics?
- Can metrics declare different observation windows?

### 4.3 System boundaries

- Are v1 zones strictly rectangular?
- Can an entity belong to multiple zones?
- What happens when a student moves an entity across a zone boundary?
- How are belts/inventories crossing the boundary classified?

### 4.4 Ports

- How does a scenario bind a logical port to a Factorio entity?
- Does FISL use tagged native chests, custom entities, coordinates, or stable identifiers?
- What are the semantics of source replenishment?
- What exactly does a demand port do when demand cannot be satisfied?
- Must shortage behavior support backlog vs lost demand in v1?

### 4.5 WIP

- Is WIP every declared tracked item within a zone?
- Does WIP include material in machines, belts, inserter hands, trains, bots, and chests?
- How are raw material, intermediate goods, and finished goods treated?
- Can scenarios define a whitelist of WIP items?
- How do we avoid double-counting transient entity inventories?

### 4.6 Throughput

- Is throughput measured only at a declared output/demand boundary?
- Is it an event count divided by an observation window?
- Do we support rolling and whole-run throughput separately?

### 4.7 Machine state

- Which Factorio statuses map to productive, starved, blocked, unavailable, disabled, idle-other?
- Are these mappings machine-type dependent?
- How are machines that are intentionally not scheduled interpreted?

### 4.8 Utilization

The contract should likely forbid bare `utilization` and require an explicit denominator, e.g.:

- `effective_utilization = productive_time / scheduled_experiment_time`
- `available_utilization = productive_time / available_time`

The exact vocabulary remains to be settled.

### 4.9 Cycle time

Because items are fungible, direct item-level flow time is not generally observable.

Potential allowed methods:

- `order_response_time`
- `cohort_completion_time`
- `transport_traversal_time`
- `little_law_derived`

Each reported result must retain the measurement method.

### 4.10 Service level

Possible definitions include:

- item fill rate;
- order fill rate;
- on-time item rate;
- on-time order rate;
- fraction of demand fulfilled within tolerance.

A scenario must choose one explicitly.

### 4.11 Aggregation

For time-varying values such as WIP:

- sample every N ticks?
- event-based integration?
- time-weighted mean?
- min/max/percentile?

The authoritative semantics must not depend accidentally on UI refresh frequency.

### 4.12 Visibility

Need at least these conceptual audiences:

- learner live;
- learner post-run;
- instructor;
- debug/internal.

Later organizational work should extend this model to named roles rather than replacing it.

### 4.13 Objectives

Need separation among:

- measured values;
- constraints/requirements;
- scalar score;
- Pareto/multi-objective comparisons.

V1 may support only simple thresholds and minimize/maximize objectives, but the data model should not assume every experiment reduces naturally to one score.

### 4.14 Reset and replay

- What exactly returns to baseline on reset?
- Is resetting implemented by reloading the baseline save rather than trying to undo player actions?
- Are run IDs always unique even with identical scenario/seed?
- What guarantees can be made about a repeated deterministic run?

---

## 5. Initial scenario shape under discussion

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
  warmup_seconds: 300
  duration_seconds: 1200

system:
  zones:
    factory:
      area:
        left_top: [-50, -30]
        right_bottom: [50, 30]

ports:
  iron_supply:
    type: source
    item: iron-plate
    schedule:
      type: constant
      rate_per_minute: 180

  customer:
    type: demand
    item: electronic-circuit
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
    zone: factory
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

## 6. Contract design principles

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

## 7. Recommended order for the next design session

Work through the contract in this sequence:

1. **Time and experiment phases** — establishes the common temporal model.
2. **Zones/system boundaries** — establishes what is being observed.
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

## 8. Definition of done for this contract

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
