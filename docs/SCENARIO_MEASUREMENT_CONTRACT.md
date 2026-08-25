# FISL Scenario and Measurement Contract

**Status:** Accepted / implementation-ready, subject to runtime-validation gate  
**Spec:** `fisl/v1`  
**Depends on:** [`ARCHITECTURE.md`](ARCHITECTURE.md)  
**Immediate handoff:** [`POST_REVIEW_REVISIONS.md`](POST_REVIEW_REVISIONS.md), [`RUNTIME_VALIDATION.md`](RUNTIME_VALIDATION.md), GitHub Issue #2  
**Full-v1 handoff:** [`FISL_V1_PRD.md`](FISL_V1_PRD.md) and [`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md)

This document is the index/summary for the **scientific API** between scenario authors, the Factorio runtime, the Python controller, and the resulting run dataset.

The detailed normative reasoning lives in the accepted ADRs. `Accepted` is a design status; Factorio-specific implementation hypotheses still requiring empirical proof are tracked in [`RUNTIME_VALIDATION.md`](RUNTIME_VALIDATION.md).

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
- What run/protocol/coverage/validity conditions apply?
- Which artifacts/software/seed make the run reproducible?
- What exactly happens on reset/retry?

---

## 2. Accepted decision map

### 2.1 Experiment time and phases — ADR 0001

- Factorio simulation ticks are authoritative.
- Simulation seconds/minutes compile exactly to ticks.
- V1 phases are fixed-duration, ordered, contiguous, half-open intervals.
- Warmup is an ordinary phase.
- Starts/transitions/end happen on clean tick boundaries.
- Pause does not advance experiment time; the canonical local-server POC operational policy is further constrained by ADR 0018.

### 2.2 Zones and system boundaries — ADR 0002

- Zones are spatial selectors, not complete accounting boundaries.
- V1 zones are static rectangular surface-qualified regions.
- Entity position determines spatial membership; collision box supports containment diagnostics.
- V1 system references one primary zone.
- Material crossing is not inferred from arbitrary geometry.

### 2.3 Ports, supply, demand — ADR 0003

- Ports are explicit one-way source/sink accounting interfaces.
- Demand is a process attached to a sink, not a port direction.
- Source withdrawal and sink delivery are authoritative boundary facts.
- Sources support replenish and exact scheduled modes.
- Scheduled supply has zero/finite/unbounded external storage with observable backlog/loss.
- For conservation-ledger WIP, one-way port integrity is strengthened by ADR 0017.

### 2.4 Primitive observations and tick pipeline — ADR 0004

- Factorio callbacks are sensor inputs; normalized FISL facts are scientific observations.
- One simulation-tick coordinator is the authoritative experiment-state writer.
- Facts distinguish interval observations, point-state samples, and instantaneous events/actions.
- Point state at `T` represents prepared state for `[T,T+1)`.
- Missing observations are never silently zero.
- Factorio-specific assumptions remain subject to the runtime validation matrix.

### 2.5 WIP and flow units — ADR 0005, superseded in part by ADR 0017

The durable semantics from ADR 0005 remain:

- Physical inventory and scalar WIP are distinct.
- Scalar WIP needs an explicit common flow-unit basis.
- Canonical Little's Law labs use conserved workpiece families.
- WIP lifetime begins after source admission and ends at declared completion/loss exit.
- Arbitrary unlike Factorio items are not summed into fake scalar WIP.

ADR 0017 changes the authoritative implementation for validated conserved flows:

```text
WIP(T)
  = initial_WIP
  + cumulative admissions
  - cumulative completions
  - cumulative declared losses
```

Consequences:

- the conservation ledger is authoritative for whole-flow total WIP;
- exact tick-resolution total WIP does not require a full physical-holder scan every tick;
- physical census remains required at READY, final boundary, and a declared coarse cadence (initially 60 ticks) as an independent validation/decomposition measurement;
- census disagreement never silently reconciles the ledger and creates an explicit conservative WIP-validity interval;
- admitted player-held work remains WIP; transient redesign carriage is diagnostic, while final residual player-held work produces a validity flag;
- belt/active-craft adapters remain important for census/decomposition and runtime validation rather than being every-tick total-WIP authority.

### 2.6 Throughput — ADR 0006

- Throughput is a derived rate over an explicit simulation-time window.
- Completion `sink_delivery` is the authoritative numerator.
- Input rate, output rate, fulfillment rate, and system throughput are distinct.
- Surplus completed output counts as throughput; scrap/loss does not by default.
- No unqualified instantaneous throughput.
- `flow` is the compatibility anchor for WIP/TH/CT.

### 2.7 Production-machine state — ADR 0007

- Raw Factorio status is retained.
- Classification is derived and entity-family/version aware.
- Actual activity/progress is separate from cause/constraint and headline state.
- Productive is based on actual craft progress/completion evidence rather than `working` or `is_crafting` alone.
- Low power may coexist with productive progress.
- Craft-progress/completion/brownout assumptions must be validated against supported Factorio versions.

### 2.8 Customer service — ADR 0008

- No ambiguous bare `service_level` metric.
- Canonical v1 service is `on_time_item_rate` with explicit maximum wait.
- Demand uses FIFO age cohorts without pretending they are customer orders.
- Cohort-selection window is distinct from fulfillment observation horizon.
- Unobserved deadlines are unresolved/censored, not automatically late.
- Compiler validation checks the direct property that the observation horizon reaches the latest selected cohort deadline.

### 2.9 Cycle time — ADR 0009

- Production cycle time is residence from declared flow admission through completion.
- Process time, transport time, customer wait, cohort response, and production cycle time are distinct.
- Every result carries its method/directness class.
- Canonical continuous-flow v1 method is `little_law_derived = average WIP / throughput` using the same flow and window.
- Controlled isolated probes may provide direct residence measurements under explicit guarantees.

### 2.10 Aggregation and observation windows — ADR 0010

- Ordinary windows are explicit contiguous half-open intervals.
- State `X(T)` integrates over `[T,T+1)` using left-boundary occupancy.
- WIP/backlog unit-ticks are first-class exact quantities.
- No bare utilization without an explicit denominator.
- Missing/invalid coverage does not silently shrink denominators.
- Time percentiles are time-weighted; demand waits are quantity-weighted.
- V1 quantiles use deterministic weighted nearest rank.
- Rolling window at `T` is `[T-L,T)`.
- ADR 0017 ledger-validity uncertainty intervals participate in strict WIP coverage.

### 2.11 Metric visibility — ADR 0011

- Collection, evaluation, and disclosure are independent.
- V1 audiences: learner-live, learner-post-run, instructor, debug.
- Hidden values may still be collected/evaluated.
- Visibility is part of the experimental condition/provenance.
- Full visibility enforcement remains a full-v1 requirement, deliberately deferred from the first Lab 3 POC.

### 2.12 Objectives — ADR 0012

- Metrics state facts; objectives evaluate named metrics.
- V1 supports threshold requirements and minimize/maximize preferences.
- No implicit weighted scalar score.
- Incomplete/no-data dependencies yield undetermined.
- Protocol/measurement validity is separate from objective outcome.
- Full objective machinery is deliberately deferred from the first Lab 3 POC.

### 2.13 Run provenance — revised ADR 0013

FISL distinguishes:

```text
scenario package/source identity
ResolvedScenario
RunConfiguration
run artifacts/results
```

- `ResolvedScenario` is canonical and run-independent.
- `resolved_scenario_hash` excludes `run_id` and actual execution seed.
- `RunConfiguration` contains per-attempt `run_id`, actual seed, resolved-hash reference, and behavior-affecting run profile.
- Reproducibility fingerprint includes resolved scenario identity + actual seed + baseline/software/mod/run-profile inputs while excluding run ID.
- Every run stores both `scenario.resolved.json` and `run-config.json`.
- Authoritative telemetry is durable and may use scientifically lossless batching/change/run-length encoding.

### 2.14 Reset/repeat/replay — ADR 0014

- Reset reloads the immutable baseline; no arbitrary undo engine.
- Every retry is a new run.
- Reset, repeat, and replay are distinct concepts.
- Same controlled condition does not imply same learner actions.
- Canonical measured v1 runs avoid mid-run save/load.
- Final saves are outputs, never implicit baselines.

### 2.15 Python ↔ Factorio transport — ADR 0015

- Canonical runtime is a controller-launched local Factorio server.
- Learner uses a normal graphical Factorio client.
- RCON is low-volume configuration/lifecycle control only.
- Lua remains authoritative for clean tick start/phases/runtime behavior.
- Authoritative telemetry is file-backed/losslessly durable rather than RCON-only.
- RCON chunking must be empirically validated; a generated companion configuration mod is an explicit fallback, not the current default.

### 2.16 Entity sets — ADR 0016

- Entity sets are analytical selectors distinct from system boundaries.
- Production sets can be dynamically maintained as learners redesign factories.
- Membership follows canonical prepared-boundary semantics.
- Pooled machine-time uses explicit subject eligibility intervals.
- New/removed machines do not retroactively distort denominators.

### 2.17 Conservation-ledger WIP — ADR 0017

ADR 0017 is the post-review implementation authority for whole-flow WIP in canonical conserved-work-unit experiments. It also defines:

- mandatory independent physical census validation;
- discrepancy/coverage policy;
- player-carriage semantics;
- stronger one-way boundary apparatus requirements;
- loss/destruction validity behavior;
- WIP method/census provenance.

### 2.18 Local-server pause/disconnect profile — ADR 0018

For the canonical interactive POC:

```text
pause_policy = prohibited
incidental/zero-player server auto-pause = disabled
unexpected required learner disconnect during RUNNING = abort + preserve data
```

READY lifecycle holding and post-completion hold are not experiment pauses. Headless fixtures explicitly do not require a learner connection.

---

## 3. Implementation representations

The current schema is defined in [`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md):

```text
AuthorScenario YAML
        |
        v
strict Python compiler
        |
        v
stable canonical ResolvedScenario
        |
        +--> resolved_scenario_hash
        |
        v
per-attempt RunConfiguration
        |
        v
Factorio Lua runtime
```

Lua never interprets authoring shortcuts or independently invents measurement semantics.

---

## 4. Core v1 concepts

The implementation provides typed concepts for at least:

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
ResolvedScenario
RunConfiguration
run
provenance
reset/repeat
```

`flow` is the shared compatibility object for system-level WIP, throughput, and cycle time.

---

## 5. Validity model

FISL retains distinct dimensions:

```text
measurement coverage/completeness
measurement validity/integrity
objective result
experiment/protocol validity
interpretation/suitability where relevant
```

Examples:

- a run may be protocol-clean but have a census discrepancy that makes WIP incomplete for strict analysis;
- a transient player-carriage diagnostic may leave ledger WIP valid, while residual player-carried work at the final boundary can flag the run for canonical comparison;
- a run may pass an objective while carrying a separate protocol-validity flag.

Data is preserved in all cases.

---

## 6. Runtime validation is an explicit implementation gate

[`RUNTIME_VALIDATION.md`](RUNTIME_VALIDATION.md) records the Factorio 2.0.77 assumptions that must be demonstrated empirically.

The preferred first fixture is:

```text
source -> inserter -> belt/underground/splitter -> inserter
       -> assembler 1:1 recipe -> inserter -> sink
```

It should validate, among other things:

- tick coordinator/event behavior;
- hardened source/sink accounting;
- physical census belt deduplication;
- active-craft census continuity;
- craft-progress evidence;
- RCON configuration transfer;
- telemetry volume/write behavior;
- server pause/disconnect behavior.

A failed runtime hypothesis does not silently rewrite this contract.

---

## 7. Labs 0–6 and implementation sequencing

The generic contract remains sufficient to express Labs 0–6; see [`FACTORY_PHYSICS_LABS_V1.md`](FACTORY_PHYSICS_LABS_V1.md).

However, implementation is intentionally sequenced:

```text
runtime-validation spike
        ↓
Lab 3 / Little's Law vertical slice
        ↓
human exercise of Lab 3
        ↓
remaining full-v1 course/platform features
```

The immediate Issue #2 therefore defers service, full visibility enforcement, objective machinery, external-storage variants and polished later labs until the core laboratory has been demonstrated against the real runtime.

---

## 8. Implementation start order

Start from:

1. [`POST_REVIEW_REVISIONS.md`](POST_REVIEW_REVISIONS.md)
2. [`RUNTIME_VALIDATION.md`](RUNTIME_VALIDATION.md)
3. GitHub Issue #2
4. [`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md)
5. [`adr/README.md`](adr/README.md)
6. [`FISL_V1_PRD.md`](FISL_V1_PRD.md) for the full-v1 destination
7. [`FACTORY_PHYSICS_LABS_V1.md`](FACTORY_PHYSICS_LABS_V1.md)

If implementation discovers that an accepted semantic is impossible or materially wrong against the pinned Factorio runtime, preserve the evidence and propose a superseding ADR rather than silently changing behavior.
