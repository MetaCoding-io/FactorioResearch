# ADR 0009: Cycle-Time and Flow-Time Measurement Methods

- **Status:** Proposed
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

ADRs 0002–0008 now give FISL explicit production-system boundaries, material admission/completion ports, primitive observations, conserved work-unit WIP, throughput, machine-state classification, and customer-demand waiting-time semantics.

The next problem is **cycle time**.

In Factory Physics, the core relationship is:

```text
WIP = TH × CT
```

where cycle time is the elapsed time a flow unit spends in the production system. For a compatible flow it is therefore possible to write:

```text
CT = WIP / TH
```

However, there is an important measurement distinction between:

- directly observing how long a particular work unit spent in the system;
- measuring a controlled probe/cohort response;
- deriving an aggregate cycle-time value from average WIP and throughput.

Factorio makes that distinction unavoidable. Ordinary production materials are fungible and stackable. Runtime item-stack structures do not provide a universal persistent identifier for every commodity item, and recipe transformations consume input items and produce new output items. A normal `iron-plate -> gear -> ...` production chain therefore does not give FISL a trustworthy end-to-end per-item identity that can simply be timestamped at entry and looked up at exit.

ADR 0005 already rejected fake scalar WIP constructed from unlike items. The same scientific principle applies here: FISL must not pretend to have directly measured individual residence times when it only has aggregate flow observations.

A second complication is finite-window interpretation. The ratio of average WIP to throughput is a legitimate Little's-Law-derived quantity, but on a short or strongly transient finite run it must not be silently described as if it were the directly observed mean residence time of the particular items that happened to complete during that same window. Opening WIP, closing WIP, censoring, startup, and drain-down can make those populations differ.

FISL therefore needs multiple explicitly named cycle/response-time methods, each carrying its measurement provenance and limits.

## Decision

### 1. FISL uses `cycle_time` for end-to-end residence time inside a declared production flow

For a declared FISL `flow`, **cycle time** means the elapsed simulation time between the flow's authoritative admission boundary and its authoritative completion boundary.

For the canonical port-backed flow:

```text
source withdrawal / admitted work
        |
        v
================ ENTRY ================
        |
        | wait / move / process / buffer
        |
================ EXIT =================
        |
        v
completion sink delivery
```

Conceptually, for one directly traceable flow unit:

```text
cycle_time_ticks = completion_tick - admission_tick
```

The admission/completion semantics must be the same ones used by compatible WIP and throughput metrics.

FISL SHOULD use `flow_cycle_time` or equivalent explanatory UI text where necessary to distinguish this system-level concept from a machine's recipe/craft duration.

### 2. Machine process time, transport time, demand waiting time, and production cycle time are distinct

FISL MUST NOT use one generic `cycle_time` label for several different clocks.

At minimum, the model distinguishes:

- **production flow cycle time** — admission into the measured flow through completion exit;
- **process time** — time a machine/resource spends processing work;
- **transport traversal time** — elapsed time across a declared transport segment;
- **customer demand wait** — demand creation through demand fulfillment (ADR 0008);
- **cohort/batch response time** — elapsed time from an experimental cohort trigger/release through a defined response/completion criterion.

These may be related but are not interchangeable.

For example, customer demand might wait zero seconds because finished goods already exist while the production cycle time of those goods was several minutes.

### 3. Every cycle/response-time result declares a measurement method

A time result must carry a method identity rather than only a label and number.

V1 recognizes at least these conceptual method families:

```text
little_law_derived
single_work_unit_probe
transport_traversal_probe
cohort_response
```

Future apparatus may add genuinely identity-tracked production work units, but FISL v1 does not assume generic commodity items have that capability.

A result should also classify whether it is:

```text
direct
controlled_probe
derived
```

so the strength of the measurement claim remains visible.

### 4. Generic per-item end-to-end cycle time is not available for ordinary fungible Factorio production

FISL v1 MUST NOT claim that ordinary stackable production items have persistent end-to-end identities through arbitrary recipes.

In particular, it MUST NOT create fictitious item identity by:

- assigning output items to input timestamps merely because quantities match;
- assuming FIFO throughout an arbitrary multi-machine factory;
- assuming belt ordering implies end-to-end ordering through buffers and parallel paths;
- matching the oldest admission to the next completion without an explicit FIFO flow contract;
- treating stack-slot identity as individual physical-item identity;
- relying on optional runtime item identifiers that are not universally available or preserved through recipe transformations.

If FISL cannot unambiguously pair an admission and completion, it cannot call the result a direct per-item cycle time.

### 5. `little_law_derived` is the canonical v1 method for continuous Factory Physics flows

For a flow with compatible scalar WIP and throughput, FISL may derive:

```text
CT_LL = average_WIP / throughput
```

For an observation window `[A,B)`:

```text
average_WIP = time-weighted average work units in the flow
throughput  = completed work units / simulation time
```

therefore:

```text
CT_LL
= work_units / (work_units / tick)
= ticks
```

Human-facing seconds/minutes are exact conversions from simulation ticks.

The precise time-weighted WIP aggregation rule will be finalized in the aggregation/window ADR; this ADR fixes the dimensional/flow compatibility requirements.

### 6. `little_law_derived` is explicitly an aggregate derived measurement, not direct item tracking

A result using `little_law_derived` must retain semantics such as:

```text
method: little_law_derived
measurement_class: derived
```

FISL MUST NOT describe it as:

```text
mean of individually tracked item cycle times
```

unless an independent direct measurement actually exists.

This distinction is scientifically important even when the numerical values agree.

### 7. Little's-Law-derived cycle time requires the same flow, work unit, boundary, and compatible window

FISL may only mark a WIP/throughput pair as compatible for `little_law_derived` when:

- both reference the same declared `flow`;
- both use the same common work unit;
- WIP lifetime begins at that flow's admission boundary;
- throughput counts completion through that flow's completion boundary;
- neither measurement silently omits relevant work/loss pathways;
- their observation coverage is complete for the requested analysis;
- their windows are compatible under the aggregation contract.

FISL MUST reject calculations such as:

```text
whole-factory WIP / one-machine output rate
```

or:

```text
stage inventory / customer completion throughput
```

merely because the units look numerically compatible.

### 8. A finite-window Little's-Law ratio does not automatically prove the mean residence time of completions within that same window

For a finite run, the populations contributing to WIP occupancy and completion events can span the window boundaries.

Examples:

- work admitted before `A` can occupy WIP during `[A,B)` and complete inside it;
- work admitted during `[A,B)` can remain WIP after `B`;
- startup can cause WIP accumulation;
- drain-down can produce completions from previously accumulated WIP.

Therefore FISL distinguishes:

```text
little_law_derived window ratio
```

from:

```text
direct mean residence time of items completed in the window
```

The former may be calculated whenever its inputs are dimensionally valid; the latter claim requires direct/cohort identity evidence or stronger analytical conditions.

### 9. Canonical Little's Law teaching runs SHOULD use a stable-flow interpretation profile

The first Factory Physics Little's Law labs should deliberately make the derived relationship pedagogically clean.

Canonical scenarios SHOULD therefore use:

- a warm-up phase before the measured window;
- a measured window long enough to reduce startup/end effects;
- conserved work-unit accounting;
- complete WIP/throughput coverage;
- no undeclared yield loss;
- diagnostics for opening/closing WIP and flow balance;
- a scenario-defined expectation that the measured interval represents approximately stable flow.

FISL SHOULD preserve diagnostics such as:

```text
opening_wip
closing_wip
wip_change
admitted_work
completed_work
flow_balance_error
```

rather than hard-code one universal numerical threshold for "steady state."

A scenario/research protocol may later define explicit acceptance thresholds.

### 10. A Little's-Law-derived result may remain computable when steady-flow suitability is poor, but its interpretation must be qualified

FISL should separate:

- dimensional/measurement validity;
- suitability for interpreting the ratio as a representative steady-flow mean cycle time.

For example, a strongly ramping system might still yield a mathematically defined:

```text
average_WIP / throughput
```

but the result should carry an interpretation flag such as:

```text
steady_flow_suitability: not_established
```

rather than being presented unqualified as the system's representative average cycle time.

The exact validity vocabulary is deferred to the aggregation/provenance pass.

### 11. `single_work_unit_probe` provides direct residence time when exactly one unambiguous probe traverses the flow

FISL may directly measure production flow cycle time in a specialized experiment when the apparatus guarantees an unambiguous pairing between one admitted probe work unit and one completion.

Conceptually:

```text
probe admitted at A
        |
        | exactly one probe in measured flow
        v
probe completed at B

cycle_time = B - A
```

The probe may use a purpose-built workpiece family compatible with the measured process.

Because there is only one eligible probe, FISL does not need persistent arbitrary per-item identity to pair entry and exit.

This method is `direct` with respect to that probe's declared boundary lifetime.

### 12. Single-work-unit probe time is not automatically representative of loaded-factory average cycle time

Running one workpiece through an otherwise empty line can estimate quantities such as:

- unloaded traversal/residence time;
- best-case or near-raw-process flow time;
- the physical path's minimum-like response under the chosen setup.

It generally does **not** capture queueing delay associated with normal WIP/load.

FISL MUST therefore retain the probe conditions and MUST NOT automatically substitute this result for a continuous-flow Little's-Law-derived cycle time.

This difference is pedagogically valuable: students can compare a low-load probe traversal with loaded-system cycle time to see how waiting/queues dominate elapsed flow time.

### 13. Probe experiments require explicit isolation/coverage guarantees

A `single_work_unit_probe` is only valid when FISL can establish that:

- exactly one eligible probe flow unit is admitted for the measurement;
- no indistinguishable pre-existing probe work is inside the measured flow;
- completion can only correspond to that probe;
- the flow's admission and completion interfaces retain authoritative coverage;
- the probe is not manually removed, duplicated, scrapped, or diverted through undeclared exits.

If these guarantees fail, the direct probe time becomes unresolved/invalid rather than guessed.

### 14. `transport_traversal_probe` is a direct segment metric, not automatically whole-system production cycle time

For a declared transport segment with no material transformation, FISL may measure the elapsed time of one unambiguous tracer/probe between explicit segment entry and exit interfaces.

For example:

```text
transport entry sensor -> belt/inserter segment -> transport exit sensor
```

This can be useful for studying:

- conveyor travel delay;
- material-handling design;
- routing changes;
- later transport variability.

The result is `transport_traversal_time` unless the segment itself is explicitly declared as the complete measured flow.

FISL MUST NOT relabel an internal transport traversal as end-to-end production cycle time.

### 15. `cohort_response` is supported as a separate experimental response-time concept

A scenario may intentionally release or mark a batch/cohort and measure its downstream response.

Examples include:

```text
time to first cohort completion
time to 50% cohort completion
time to 95% cohort completion
time to final cohort completion
```

This is useful for experiments involving system response, drain-down, demand shocks, or batch flow.

However, a cohort response time is not automatically the mean item cycle time.

If individual members of the cohort entered the production system at different ticks or can overtake/reorder, FISL generally cannot reconstruct individual residence times from only aggregate cohort completion counts.

Therefore the metric must remain named/typed as a cohort response unless the experiment supplies stronger simultaneous-admission/identity guarantees.

### 16. Cohort completion distributions may be quantity-weighted without pretending to identify individual commodities

If a controlled cohort has a common authoritative origin/trigger tick `T0`, FISL may record completion quantities by settlement tick:

```text
T1: 3 units completed
T2: 5 units completed
T3: 2 units completed
```

and derive response quantities such as:

```text
first_completion_time = T1 - T0
p50_completion_time
p95_completion_time
final_completion_time = T3 - T0
```

These are auditable cohort-response measurements.

They become direct individual cycle-time observations only when the cohort's admission semantics make `T0` the actual common production-entry time for every counted unit.

### 17. Demand waiting time is not production cycle time

ADR 0008 already preserves:

```text
demand_created_tick -> demand_fulfillment_tick
```

That interval answers:

> How long did the customer requirement wait?

Production flow cycle time answers:

> How long did the production work unit reside inside the declared production flow?

The two can differ radically.

If finished goods inventory exists before demand arrives, customer wait may be nearly zero while the goods had a nonzero production cycle time.

Conversely, customer backlog may wait while a newly admitted workpiece is still moving through production.

FISL MUST keep these measurement families distinct.

### 18. Nominal recipe/process time is not production cycle time

Summing Factorio recipe craft times, machine nominal craft durations, or observed productive processing time does not automatically produce end-to-end cycle time.

Cycle time includes all elapsed residence inside the flow, including:

- queueing;
- blocking;
- transport;
- waiting in buffers;
- process time;
- other internal residence permitted by the flow.

A future `raw_process_time` or `theoretical_minimum_flow_time` metric may use recipe/process data, but it must not masquerade as observed cycle time.

### 19. Direct/cohort cycle-time-style measurements require an observation horizon and censoring semantics

A probe or cohort can remain inside the system when the run/window ends.

FISL MUST NOT assign:

```text
cycle_time = end_of_run - admission_tick
```

as though the item completed then.

Instead unresolved work is censored/incomplete.

For direct probe measurements, a complete result requires observing the matching completion.

For cohort response, results may explicitly include:

```text
cohort_quantity
completed_quantity
unresolved_quantity
observation_horizon_end
```

A final-completion/100%-completion metric is incomplete until all required cohort work is observed leaving through the intended completion boundary.

### 20. The flow object is the compatibility anchor for WIP, throughput, and cycle time

ADR 0006 introduced the emerging `flow` abstraction. Cycle-time semantics make that abstraction necessary.

Conceptually:

```yaml
flows:
  workpiece_flow:
    system: factory
    unit: workpiece
    basis:
      type: conserved_work_unit
      materials:
        fisl-rough-workpiece: 1
        fisl-machined-workpiece: 1
        fisl-finished-workpiece: 1
    entry_ports:
      - workpiece_source
    completion_ports:
      - finished_goods
```

Compatible metrics then reference the same flow:

```yaml
metrics:
  line_wip:
    type: wip
    flow: workpiece_flow

  line_throughput:
    type: throughput
    flow: workpiece_flow

  line_cycle_time:
    type: cycle_time
    flow: workpiece_flow
    method: little_law_derived
```

This prevents each metric from silently inventing a different system lifetime.

### 21. Little's-Law-derived cycle time depends on time-weighted average WIP, not an arbitrary snapshot average

The valid numerator for:

```text
CT_LL = average_WIP / throughput
```

must represent the average WIP occupancy over the same simulation-time analysis window.

A naïve arithmetic average over irregularly timed samples is not automatically acceptable.

The upcoming aggregation/window ADR will define the exact integration rule. Canonical tick-resolution WIP permits an exact/discrete time-weighted average under FISL's boundary-state convention.

The cycle-time metric MUST depend on that authoritative aggregation result rather than performing its own hidden averaging.

### 22. Cycle-time results preserve method, directness, boundary, and assumption provenance

A cycle/response-time result must be able to report at least:

```text
metric_id
flow_id / segment_id
method
measurement_class: direct | controlled_probe | derived
flow_unit
entry semantics
completion semantics
analysis/cohort window as applicable
observation horizon as applicable
result value/unit
resolved/unresolved quantity where applicable
source primitive/metric dependencies
coverage/validity metadata
assumption/suitability metadata
```

For `little_law_derived`, provenance includes at least:

```text
average_wip metric/result
throughput metric/result
shared flow definition
window
```

For a direct probe it includes the authoritative admission and completion observations.

### 23. V1 canonical Factory Physics content should teach both direct and derived meanings rather than hiding the distinction

Where practical, the course should deliberately contrast:

1. an unloaded/single-probe traversal or other direct controlled time measurement;
2. loaded-system WIP and throughput;
3. Little's-Law-derived average cycle time.

This demonstrates that:

- physical processing time is not the same as total flow time;
- queueing/WIP creates elapsed time;
- direct tracking and aggregate inference are different measurement methods;
- Little's Law gives a powerful system-level relationship without requiring per-item digital identity.

That distinction is part of the teaching value of FISL rather than a limitation to conceal.

## Proposed v1 schema shape

Illustrative only:

```yaml
metrics:
  loaded_cycle_time:
    type: cycle_time
    flow: workpiece_flow
    method: little_law_derived
    window:
      phase: measured
    interpretation:
      profile: stable_flow
```

A direct probe could be conceptually:

```yaml
metrics:
  probe_cycle_time:
    type: cycle_time
    flow: workpiece_flow
    method: single_work_unit_probe
    probe:
      require_isolated: true
    observation_horizon:
      through_phase: probe_drain
```

A transport-only measurement could instead be:

```yaml
metrics:
  conveyor_travel_time:
    type: transport_traversal_time
    segment: conveyor_test
    method: transport_traversal_probe
```

And a cohort response might be:

```yaml
metrics:
  batch_p95_response:
    type: cohort_response_time
    cohort: test_batch
    completion_fraction: 0.95
```

The exact schema/window syntax remains deferred.

## Consequences

### Positive

- FISL never pretends ordinary fungible Factorio commodities have end-to-end identity they do not possess.
- Little's Law becomes the rigorous canonical continuous-flow cycle-time method for v1 Factory Physics labs.
- Direct probe measurements remain available where the experiment can genuinely establish entry/exit pairing.
- Cohort/batch response experiments are useful without being mislabeled as individual cycle time.
- Customer demand wait, transport delay, process time, and production flow cycle time remain semantically separate.
- WIP, throughput, and cycle time now share one explicit `flow` compatibility object.
- Finite-window/transient limitations become visible rather than hidden behind a single number.
- The measurement-method distinction itself becomes pedagogically useful.

### Negative / trade-offs

- FISL v1 cannot produce generic per-item end-to-end cycle-time distributions for arbitrary vanilla production graphs.
- Little's-Law-derived cycle time requires authoritative average-WIP aggregation and complete throughput coverage.
- Direct probes can perturb/underload the system and therefore require careful interpretation.
- Cohort response measurements need controlled experiment structure and do not automatically yield mean item residence time.
- Stronger direct identity tracking would require additional apparatus/semantics in future versions.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- exact time-weighted WIP integration syntax/arithmetic;
- percentile algorithms for direct/cohort time distributions;
- the final metric validity/status vocabulary;
- a universal steady-state statistical test;
- direct persistent identity propagation through custom production recipes;
- rework/yield-loss cycle-time semantics;
- queue-time versus process-time decomposition per individual work unit;
- final `flow` schema syntax;
- UI wording/visualization for direct versus derived time measurements.

## Acceptance criteria

The cycle-time portion of Issue #1 is complete when we agree that:

1. production cycle time means residence from the flow's declared admission boundary through its completion boundary;
2. production cycle time, process time, transport time, customer demand wait, and cohort response time are distinct concepts;
3. every time metric preserves an explicit measurement method/directness class;
4. ordinary fungible Factorio production does not receive fictitious per-item end-to-end identity;
5. `little_law_derived` is the canonical v1 continuous-flow cycle-time method using compatible average WIP and throughput;
6. Little's-Law-derived results are explicitly derived rather than described as direct tracked-item means;
7. WIP, throughput, and cycle time must reference compatible work units and the same declared flow lifetime;
8. finite-window Little's-Law ratios are not automatically equated with the direct mean residence time of items completing inside that window;
9. canonical Little's Law labs should use warm-up/stable-flow-oriented protocols and preserve opening/closing/flow-balance diagnostics;
10. a `single_work_unit_probe` may provide direct cycle time only under unambiguous isolated-entry/completion guarantees;
11. single-probe results are not automatically representative of loaded-factory mean cycle time;
12. transport probes and cohort response measurements remain explicitly named for the concepts they actually measure;
13. unresolved probes/cohorts are censored/incomplete rather than assigned artificial completion times;
14. time-weighted average WIP from the aggregation contract is required for Little's-Law-derived cycle time;
15. cycle-time results preserve method, boundary, window/horizon, dependencies, coverage, and interpretation provenance;
16. canonical teaching content should expose the difference between direct controlled timing and aggregate Little's-Law inference.

## References

- Mark L. Spearman, "Little's Law in Production Systems with Yield Loss," Project Production Institute, 2019.
- Factorio Runtime API — `ItemStackIdentification` and `LuaItemStack` runtime documentation.
