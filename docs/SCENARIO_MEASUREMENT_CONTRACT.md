# FISL Scenario and Measurement Contract

**Status:** Working design document  
**Depends on:** [`ARCHITECTURE.md`](ARCHITECTURE.md)

This document is the working specification for the **scientific API** between scenario authors, the Factorio runtime, the external controller, and resulting run datasets.

Implementation should not make measurement semantics implicit. Major settled portions are captured as ADRs.

## Accepted contract decisions

- [`ADR 0001`](adr/0001-experiment-time-and-phases.md) — experiment time and phase semantics.
- [`ADR 0002`](adr/0002-zones-and-system-boundaries.md) — zones and system-boundary semantics.
- [`ADR 0003`](adr/0003-material-ports-supply-demand.md) — material ports, supply, external supply buffering/loss, sink output, demand, and backlog.

## Contract goals

The contract must make it possible to answer unambiguously:

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

## Core concepts

The contract must define at least:

1. `scenario`
2. `experiment`
3. `phase`
4. `zone`
5. `system`
6. `entity_set`
7. `port`
8. `source`
9. `sink`
10. `demand`
11. `observation`
12. `metric`
13. `aggregation`
14. `objective`
15. `visibility`
16. `run`
17. `provenance`
18. `reset` / `replay`

## Measurement terms still requiring explicit semantics

- primitive observation/event model;
- WIP and inventory;
- throughput, input rate, and output rate;
- productive/starved/blocked/unavailable time;
- utilization denominators;
- service-level definitions;
- cycle time / flow time / response time;
- aggregation and observation windows;
- learner/instructor metric visibility;
- objectives and multi-objective comparison.

Port-side upstream state now also includes explicit primitive concepts for external supply pending and lost supply. ADR 0003 requires enough underlying observations to derive current/peak/time-integrated upstream backlog and cumulative/loss-rate measures.

## Accepted temporal model

See ADR 0001. In summary:

- simulation ticks are authoritative experiment time;
- a simulation second is exactly 60 ticks;
- phases are named, contiguous, fixed-duration half-open intervals in v1;
- warm-up is an ordinary phase;
- metric windows explicitly select intervals;
- wall time, game speed, and pause behavior do not redefine simulation-time measurement semantics.

## Accepted spatial/system model

See ADR 0002. In summary:

- a zone is a spatial selector, not the accounting boundary itself;
- v1 zones are static, rectangular, surface-qualified and tile-aligned;
- canonical entity zone membership uses entity position;
- collision footprints are used separately for boundary-integrity checks;
- a v1 system references one primary zone;
- material throughput is not inferred from geometric crossing;
- explicit ports define material boundary transactions.

## Accepted material boundary model

See ADR 0003. In summary:

- v1 material ports are one-way `source` or `sink` interfaces;
- demand is an external process attached to a sink, not a port direction;
- authoritative port accounting uses deterministic per-tick settlement;
- source input is a documented net-withdrawal measurement;
- sink delivery is distinct from customer demand fulfillment;
- customer shortage semantics use backlog in v1;
- source supply can be `replenish` or `scheduled`;
- scheduled supply has an explicit external buffer with zero, finite, or unbounded capacity;
- blocked supply beyond external-buffer capacity is recorded as lost, never silently discarded;
- upstream pending supply and loss must have primitive data sufficient for current, peak, cumulative, and time-integrated measures;
- port apparatus and external upstream buffers are outside normal internal WIP.

## Illustrative scenario shape

```yaml
spec: fisl/v1

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

ports:
  iron_supply:
    system: factory
    direction: source
    material:
      item: iron-plate
    supply:
      mode: scheduled
      schedule:
        type: constant
        rate: 180/min
      external_buffer:
        capacity: 2000

  customer_shipments:
    system: factory
    direction: sink
    material:
      item: electronic-circuit
    demand:
      shortage_policy: backlog
      schedule:
        type: constant
        rate: 60/min
```

The exact final schema remains intentionally unsettled until the scientific semantics are complete.

## Contract design principles

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

## Recommended remaining design order

1. **Primitive observations** — establish what FISL can honestly know and the authoritative per-tick pipeline.
2. **WIP and throughput** — first major Factory Physics measurements.
3. **Machine-state classification** — productive/starved/blocked semantics.
4. **Service level** — connect output to external demand.
5. **Cycle-time methods** — address fungibility and observability explicitly.
6. **Aggregation/windows** — rigorous semantics for time-varying measurements, including item-ticks.
7. **Visibility/objectives** — pedagogical presentation and evaluation.
8. **Run provenance/reset/replay** — reproducibility contract.
9. **Draft `fisl/v1` schema** — after semantic decisions are settled.
10. **Validate against Factory Physics Labs 0–6.**

## Definition of done

The contract is ready to become an implementation specification when each initial lab can answer without informal interpretation:

- what the starting world is;
- where the system boundary lies;
- what FISL controls;
- what Factorio controls;
- exactly what is observed and measured;
- how each reported number is calculated;
- when measurement begins and ends;
- which measurements the learner can see;
- what constitutes success;
- what data make the run reproducible.

At that point the first Lua and Python modules should be largely mechanical implementations of the agreed scientific contract.
