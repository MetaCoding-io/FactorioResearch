# ADR 0004: Primitive Observations and Tick-Pipeline Semantics

- **Status:** Proposed
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

The accepted FISL design now has:

- a deterministic experiment clock and fixed-duration phases (ADR 0001);
- explicit systems/zones (ADR 0002);
- explicit material source/sink ports, demand ledgers, and source buffering/loss policies (ADR 0003).

The next question is foundational:

> What does FISL count as an authoritative primitive fact, when is that fact observed, and in what order does FISL turn Factorio runtime state into scientific data?

Factorio exposes event callbacks and queryable runtime state, but those are implementation primitives, not yet a scientific data model. A Factorio event such as `on_built_entity` tells a mod that something happened; it does not by itself define what FISL should record, how the fact should be timestamped, or what later metrics are allowed to conclude from it.

Likewise, some FISL facts are directly controlled transactions (for example items released by a source schedule), some are measured deltas (source withdrawal), and some are point samples of Factorio state (inventory count, entity status).

FISL needs one deterministic runtime pipeline so that ports, future WIP measurements, machine-state sampling, protocol validation, and later stochastic disturbances do not each invent their own ordering semantics.

## Decision

### 1. A primitive observation is a normalized FISL fact, not a metric

A **primitive observation** is the lowest-level scientific fact that FISL exposes to later metrics and reports.

A primitive observation must be either:

1. directly measured from declared Factorio state under an explicit method;
2. directly produced by a FISL-controlled action or scheduler;
3. normalized from a Factorio runtime notification under a documented mapping.

A primitive observation is **not** a derived analytical result such as:

- throughput;
- utilization;
- average WIP;
- service level;
- cycle time;
- percent supply loss.

Those are metrics derived from primitive observations.

Examples of primitive observations include:

```text
source_withdrawal
source_release
source_external_pending
source_supply_lost
sink_delivery
demand_created
demand_fulfilled
demand_backlog
surplus_delivery
inventory_count_sample
entity_status_sample
entity_position_sample
entity_created
entity_removed
protocol_violation
phase_transition
```

The exact vocabulary will grow, but the distinction between **primitive observation** and **derived metric** must remain stable.

### 2. Raw Factorio notifications are sensor inputs, not automatically scientific observations

Factorio event callbacks are implementation inputs to FISL.

Receiving `on_built_entity`, `on_player_mined_entity`, `on_object_destroyed`, or another event does not automatically make the Factorio event payload part of the FISL scientific schema.

Instead:

```text
Factorio event
    -> raw notification capture
    -> FISL normalization / registry update
    -> zero or more primitive observations
```

This prevents FISL's scientific contract from becoming accidentally coupled to Factorio's event table structure.

FISL may preserve raw event diagnostics separately for debugging, but later metrics MUST consume normalized primitive observations or explicitly declared state samples rather than arbitrary raw Factorio event payloads.

### 3. Factorio event handlers are sensors; the FISL tick coordinator is the single experiment-state writer

FISL uses a **single-writer runtime model**.

Factorio event handlers other than the authoritative per-tick coordinator SHOULD do only the minimum work needed to capture information that may otherwise disappear, for example:

- event type;
- Factorio event tick;
- stable entity identifier when available;
- prototype/type;
- surface;
- position;
- player/robot/force identity when relevant;
- other event-specific fields needed for later normalization.

These handlers append small raw notifications to an internal queue.

They MUST NOT independently:

- advance demand or supply schedules;
- settle ports;
- mutate experiment phases;
- compute metrics;
- update authoritative demand/source ledgers;
- emit competing scientific state transitions.

The FISL once-per-tick coordinator is the only component that mutates authoritative experiment state and emits the ordered primitive-observation stream.

This gives FISL a deterministic internal order even when Factorio generates multiple unrelated event notifications during one simulation tick.

### 4. `on_tick` is the authoritative runtime checkpoint; `on_nth_tick` is not used for scientific ordering

FISL v1 uses one `on_tick` coordinator invocation as its authoritative **observation checkpoint** for each executed map tick while a run is active.

`on_nth_tick` or other periodic callbacks may later be used for non-authoritative work such as UI refresh or maintenance, but MUST NOT define scientific observation timing or phase/schedule progression.

This keeps the scientific pipeline attached to the experiment clock accepted in ADR 0001.

Factorio's runtime API guarantees an `on_tick` event once per tick and exposes the event's map tick. FISL defines its own ordering *inside* that handler rather than relying on undocumented global ordering among unrelated Factorio events.

### 5. Primitive observations have three temporal classes

V1 distinguishes three broad temporal semantics.

#### A. Interval observations

An interval observation describes a quantity attributed to a simulation interval:

```text
[start_tick, end_tick)
```

Examples:

- source withdrawal during the interval;
- sink delivery settled for the interval;
- demand fulfillment allocated to that delivery;
- supply loss caused by arrivals scheduled for the upcoming interval, if represented as a transaction over that boundary step.

Interval observations must carry both start and end experiment ticks.

#### B. Point-state samples

A point-state sample records the value FISL observed at one canonical experiment boundary tick.

Examples:

- current demand backlog;
- current external source pending quantity;
- source staging quantity;
- entity status;
- inventory count;
- entity position.

A point-state sample says:

> this was the observed value when FISL sampled at boundary tick T.

It MUST NOT silently claim that the value remained constant throughout the preceding or following tick.

#### C. Instantaneous events/actions

An instantaneous observation records a discrete FISL semantic event at a boundary tick.

Examples:

- phase transition;
- demand creation;
- source release performed by FISL;
- source supply lost due to storage capacity;
- protocol violation detected;
- normalized entity creation/removal.

These events are assigned one experiment boundary tick and an explicit method/origin.

### 6. Every primitive observation carries measurement provenance

Every scientific primitive observation must carry enough metadata to understand how it was obtained.

At minimum, the logical record should be capable of carrying:

```text
run_id
sequence
observation_type
temporal_class
map_tick
experiment_tick / interval_start_tick / interval_end_tick
phase_id when applicable
subject identity
value / quantity / state
unit when numeric
method
origin
quality/validity metadata when needed
```

`method` is scientifically significant.

Examples include:

```text
fisl_controlled_transaction
net_inventory_delta
factorio_point_sample
factorio_event_normalized
ledger_state
```

A later metric must be able to state which primitive methods contributed to its result.

### 7. Primitive observations have a monotonic FISL sequence number

Every emitted primitive observation receives a run-local monotonically increasing `sequence` number.

The sequence defines **FISL emission order**.

It does not claim to reconstruct a hidden physical sub-tick order inside Factorio.

Therefore:

```text
(run_id, sequence)
```

is the canonical unique identity for an observation record.

This supports:

- deterministic replay of the FISL fact stream;
- append-only storage;
- de-duplication if observations are streamed externally;
- auditing of derived metrics.

### 8. FISL defines one canonical boundary-state sampling point

For v1, ordinary point-state observations are sampled at one canonical point in the tick pipeline: **after FISL has settled the completed interval, handled any phase transition, advanced external processes for the upcoming interval, applied its controlled boundary mutations, and run immediate integrity checks.**

Thus a point-state sample at experiment boundary tick `T` represents the prepared state at the start of interval:

```text
[T, T+1)
```

This gives state samples a consistent interpretation.

If a future experiment requires a scientifically meaningful state both before and after a FISL action at the same boundary, it must declare two explicitly named observation stages rather than relying on incidental callback timing.

### 9. The canonical v1 tick pipeline is ordered as follows

At observation checkpoint `T`, FISL processes one deterministic pipeline.

#### Step 1 — Ingest queued runtime notifications

Drain raw Factorio notifications captured since the prior checkpoint and use them to update internal registries / normalize any event observations required by the experiment.

Raw arrival order may be preserved for diagnostics, but scientific semantics MUST NOT rely on undocumented ordering among unrelated Factorio events.

#### Step 2 — Settle the completed interval `[T-1, T)`

If `T > 0`, settle observations attributable to the interval that just completed.

For v1 ports this includes, in deterministic FISL order:

1. measure source net withdrawals;
2. inspect source reverse-flow/contamination conditions;
3. read sink deliveries;
4. record sink delivery quantities;
5. allocate sink deliveries against demand that was outstanding during `[T-1, T)`;
6. record demand fulfillment and surplus delivery;
7. remove settled tracked output from sink staging.

The exact port implementation may optimize internal calls, but the scientific outcome must be equivalent to this ordering.

#### Step 3 — Close the completed interval

Emit/finalize all interval primitive observations for `[T-1, T)`.

Later metric accumulators may consume these observations, but metrics do not alter the primitive facts.

#### Step 4 — If `T` is the final experiment boundary, finalize rather than prepare another interval

At the exclusive end of the final phase:

- no new demand or supply is scheduled for a nonexistent next interval;
- terminal point-state observations required by the scenario are captured;
- completion/provenance state is finalized;
- the experiment transitions to completed according to ADR 0001.

#### Step 5 — Apply phase transition for boundary `T`, if any

If `T` begins a new phase, the active phase changes now.

Any phase-transition primitive event is emitted at boundary tick `T`.

This ensures all policy/schedule preparation for `[T, T+1)` uses the newly active phase.

#### Step 6 — Advance external processes for upcoming interval `[T, T+1)`

Advance deterministic scenario processes such as:

- scheduled external supply becoming available;
- external source-buffer accumulation;
- source overflow/loss policy;
- customer demand creation.

These are FISL-controlled events and therefore have exact known quantities.

#### Step 7 — Apply FISL-controlled apparatus mutations for the upcoming interval

Examples:

- release available material from external source storage into source staging;
- restore a replenishing source toward its target;
- enforce/restore standard port staging state;
- other future controlled experimental actions.

Every scientifically relevant mutation emits or updates the corresponding primitive fact rather than occurring invisibly.

#### Step 8 — Validate immediate protocol/integrity conditions

Run checks whose meaning is defined at the prepared boundary state, such as:

- port contamination;
- source reverse-flow evidence;
- port binding availability;
- zone/system containment violations that are configured for runtime checking;
- fixed-speed/pause protocol state when observable here.

A detected violation is an observation/validity fact, not a reason to silently alter previous measurements.

#### Step 9 — Capture declared canonical point-state samples at boundary `T`

Sample the configured primitive state observations after the upcoming interval has been prepared.

Examples may include:

- demand backlog;
- external source pending quantity;
- source staging quantity;
- selected inventory counts;
- raw Factorio entity statuses;
- selected entity positions.

#### Step 10 — Flush/commit the ordered observation batch

The runtime commits the ordered primitive-observation batch for this checkpoint to authoritative FISL storage/output.

Storage format is deferred, but the semantic stream is append-only and sequence-ordered.

### 10. Experiment start is checkpoint `T = 0` with no prior interval to settle

At experiment start boundary:

- there is no `[T-1, T)` interval;
- the first phase is active;
- initial external processes are advanced/prepared for interval `[0,1)` according to scenario initial conditions;
- FISL-controlled apparatus mutations establish the starting boundary state;
- canonical point-state samples at `experiment_tick = 0` may be recorded.

This is the temporal complement of ADR 0003's rule that the first interval must begin with already-defined supply and demand state.

### 11. Interval observations are attributed to the interval, not the checkpoint that discovers them

If source withdrawal is measured at checkpoint `T`, it describes the change observed since the prior source settlement.

Therefore it is recorded against:

```text
interval_start_tick = T - 1
interval_end_tick   = T
```

not merely as an undifferentiated event "at tick T".

This becomes especially important at phase boundaries.

For example, if warmup is `[0, 18000)`, the port settlement performed at boundary `18000` for interval `[17999, 18000)` still belongs to `warmup`, even though the next interval begins the `measured` phase.

### 12. Phase attribution for interval facts uses the interval start

Because v1 phases are contiguous and do not split a tick, every one-tick interval belongs to exactly one phase.

For interval `[T, T+1)`, the associated phase is the phase containing experiment tick `T`.

Point-state samples and instantaneous events at a boundary use the phase active **after** any phase transition at that boundary, unless the event type explicitly describes the transition itself.

This rule removes phase-boundary ambiguity.

### 13. FISL-controlled transactions are stronger observations than inferred changes

When FISL itself performs an action, such as:

```text
source_release = 20 items
source_supply_lost = 5 items
demand_created = 3 items
```

it knows the intended and actual affected quantity from the operation and should record that exact controlled transaction.

It should not later infer the same action by comparing snapshots.

By contrast, where Factorio's ordinary simulation moved material and no direct gross transaction event exists, FISL may use an explicitly weaker measurement such as ADR 0003's `net_inventory_delta` source-withdrawal method.

The method field preserves this epistemic difference.

### 14. Point samples do not become durations until a later metric defines the rule

An `entity_status_sample` is a primitive state observation.

It does not itself mean:

```text
machine was productive for one full tick
```

Likewise an `inventory_count_sample` is not automatically a time-weighted WIP contribution.

Later ADRs for machine state, WIP, and aggregation must explicitly define how sequences of point samples are converted into durations, integrals, or averages.

This prevents primitive collection from smuggling in unreviewed analytical assumptions.

### 15. Raw Factorio status values should be preserved before classification

When FISL samples an entity's runtime status, the primitive observation SHOULD preserve the native Factorio status identity/value available at that runtime version.

The later machine-state contract may map those raw statuses into categories such as:

```text
productive
starved
blocked
unavailable
disabled
idle_other
```

but that classification is not part of the primitive status sample.

This preserves auditability if classification rules change.

### 16. Missing observations are not zero

If FISL expected to sample a declared subject and cannot do so because, for example:

- an entity reference became invalid;
- a port endpoint disappeared;
- the surface is unavailable;
- a required inventory cannot be read;
- the observation method fails;

FISL MUST NOT silently emit zero or carry forward the prior value unless the measurement contract explicitly defines that behavior.

Instead it must record an observation/coverage error or protocol-validity condition.

A metric that encounters missing primitive coverage must follow an explicit missing-data policy rather than treating absence as measurement.

### 17. Observation collection is scenario-declared; FISL does not log the entire world by default

FISL v1 does not attempt to snapshot every entity, inventory, belt, inserter, train, and status every tick.

The scenario/metric compilation process determines an **observation plan** containing the primitive subjects needed for the declared measurements.

Examples:

- ports always register their required settlement observations;
- a WIP metric may register inventory/item observations for an entity set;
- a machine-state metric may register raw status sampling for selected machines;
- system-boundary integrity may register relevant entity geometry/position checks.

This keeps runtime cost proportional to the experiment rather than the entire Factorio world.

The resolved observation plan becomes part of run provenance.

### 18. Sampling cadence is explicit and scientifically visible

For state observations, the sample cadence is part of the measurement method.

A later contract may allow:

```text
every tick
every N ticks
on change
```

but the cadence must be explicit in the resolved observation plan and preserved with the observation method/provenance.

A derived metric MUST NOT claim tick-level knowledge if its primitive state source was only sampled every 60 ticks.

V1 metrics that require exact one-tick discrete integration SHOULD request every-tick primitive sampling unless a stronger event-driven method is defined.

### 19. Storage encoding may compress observations but must preserve their scientific semantics

The primitive stream is logically append-only and ordered.

The eventual telemetry implementation may use:

- JSONL;
- binary encoding;
- run-length compression;
- batched records;
- event-only compression for repeated states;
- external database storage.

Those are implementation choices.

Any authoritative encoding used for a run must be semantically lossless for the primitive observation plan needed to reproduce the declared metrics.

For example, a state that remains constant for 10,000 ticks may be run-length encoded instead of writing 10,000 identical JSON objects, provided the decoded observation semantics are identical.

### 20. The learner UI is not an independent measurement system

Live learner/instructor displays SHOULD consume the same FISL observation/metric state used for recorded results.

The UI must not independently query Factorio and show a subtly different definition of backlog, throughput, WIP, or machine state.

Presentation refresh frequency may be lower than scientific observation frequency, but the displayed value must be derived from the authoritative FISL state.

### 21. Observation errors and protocol violations are themselves first-class facts

FISL should preserve conditions that affect trust in a run, including:

```text
protocol_violation
observation_gap
port_binding_lost
port_contamination
boundary_integrity_violation
game_speed_violation
prohibited_pause
```

These facts belong in the run's ordered event/validity record.

They do not retroactively erase earlier valid primitive observations.

Later comparison/reporting logic decides whether a run remains admissible for a given analysis.

### 22. Primitive observation semantics are independent of final file format

This ADR intentionally does not choose the exact telemetry serialization.

The scientific model must be implementable in memory and testable before decisions such as JSONL vs another encoding are made.

File-format choices should receive their own ADR if they materially affect interoperability, performance, or durability.

## Illustrative primitive records

The exact schema is deferred, but the semantics should support records such as:

```json
{
  "sequence": 812,
  "observation_type": "source_withdrawal",
  "temporal_class": "interval",
  "interval_start_tick": 419,
  "interval_end_tick": 420,
  "phase_id": "measured",
  "subject": {"port": "iron_supply"},
  "quantity": 6,
  "unit": "item",
  "method": "net_inventory_delta",
  "origin": "factorio_state_measurement"
}
```

```json
{
  "sequence": 813,
  "observation_type": "source_external_pending",
  "temporal_class": "point_state",
  "experiment_tick": 420,
  "phase_id": "measured",
  "subject": {"port": "iron_supply"},
  "value": 140,
  "unit": "item",
  "method": "ledger_state",
  "origin": "fisl_runtime"
}
```

```json
{
  "sequence": 814,
  "observation_type": "entity_status_sample",
  "temporal_class": "point_state",
  "experiment_tick": 420,
  "subject": {"entity_id": 12345},
  "value": "waiting_for_source_items",
  "method": "factorio_point_sample",
  "origin": "factorio_runtime"
}
```

These examples are illustrative only; the eventual schema may use compact field names or typed records.

## Consequences

### Positive

- FISL gets one authoritative scientific fact stream instead of many ad hoc metric-specific queries.
- Factorio events remain useful without becoming the FISL public data model.
- The single-writer coordinator gives deterministic runtime ordering.
- Interval facts, point samples, and instantaneous events have distinct time semantics.
- Phase-boundary attribution is unambiguous.
- Controlled FISL actions are distinguished from weaker inferred measurements.
- Raw native entity status can be preserved before later classification.
- Missing-data conditions cannot silently masquerade as zero.
- UI and post-run analysis can consume the same authoritative data model.
- Later stochastic disturbances can enter the same pipeline as exact FISL-controlled transactions.

### Negative / trade-offs

- The runtime needs a deliberate observation-plan compiler/registry rather than simple direct metric queries.
- Per-tick scientific sampling may be expensive if scenarios register very large entity sets; later WIP work must consider efficient observation strategies.
- The model explicitly accepts that some Factorio-native physical activity is only point-sampled or net-measured rather than fully event-sourced.
- Implementers must maintain the boundary between raw notifications, primitive observations, and derived metrics.
- The pipeline order becomes part of the scientific contract and must therefore be tested carefully.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- the exact WIP entity/inventory observation strategy;
- whether WIP uses every-tick sampling, event-driven inventory deltas, or a hybrid;
- the exact mapping from Factorio entity statuses to productive/starved/blocked/etc.;
- throughput formulas and aggregation windows;
- service-level formulas;
- cycle-time measurement methods;
- the final metric observation-window syntax;
- exact telemetry serialization/file format;
- persistence/recovery of a partially completed observation batch across save/load;
- whether raw Factorio notification diagnostics are retained in normal student runs or only debug mode.

## Acceptance criteria for this decision

The primitive-observation portion of Issue #1 is complete when we agree that:

1. primitive observations are normalized lowest-level FISL facts, distinct from derived metrics;
2. raw Factorio events are sensor inputs rather than automatically becoming the scientific schema;
3. Factorio event handlers capture minimal notifications while one per-tick FISL coordinator is the authoritative experiment-state writer;
4. `on_tick` checkpoints define scientific runtime ordering;
5. primitive observations distinguish interval facts, point-state samples, and instantaneous events/actions;
6. every observation carries explicit method/provenance and a monotonic FISL sequence;
7. point-state samples have one canonical prepared-boundary sampling point in v1;
8. the accepted tick pipeline settles the prior interval before transitioning phase and preparing the next interval;
9. interval observations retain `[start_tick, end_tick)` semantics and are attributed to the phase containing their interval start;
10. exact FISL-controlled transactions remain distinguishable from inferred/net measurements;
11. point samples do not become durations or averages until later metric contracts define that transformation;
12. missing observations are never silently treated as zero;
13. collection is driven by an explicit resolved observation plan rather than global world logging;
14. UI/display data derive from the same authoritative observation/metric state;
15. storage format may optimize/compress the stream but must preserve the declared scientific semantics.
