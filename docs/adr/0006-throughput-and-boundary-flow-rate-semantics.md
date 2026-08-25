# ADR 0006: Throughput and Boundary Flow-Rate Semantics

- **Status:** Proposed
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

ADRs 0001–0005 now give FISL:

- an exact simulation-time clock and explicit observation windows;
- declared systems and accounting boundaries;
- explicit material source/sink ports;
- authoritative primitive port observations such as `source_withdrawal` and `sink_delivery`;
- an explicit conserved flow-unit basis for scalar WIP and Little's Law-compatible experiments.

The next question is what FISL means by **throughput**.

The word is easy to misuse. A Factorio factory exposes many rates that might informally be called throughput:

- items produced by an assembler;
- items moving on a belt;
- material admitted at a source;
- material crossing an arbitrary sink;
- completed work leaving the measured system;
- demand fulfilled;
- scrap leaving the system.

Those are not interchangeable.

FISL needs to preserve the distinction between a physical boundary transaction, a generic boundary flow rate, and the Factory Physics concept of system throughput. It must also ensure that throughput used with WIP and cycle time has compatible units, boundaries, and observation windows.

## Decision

### 1. Throughput is a derived interval/window metric, not a primitive observation

Primitive observations remain facts such as:

```text
source_withdrawal
sink_delivery
demand_fulfilled
```

Throughput is derived from those facts over an explicit simulation-time window.

FISL does not define an unqualified instantaneous throughput value.

For an observation window:

```text
[A, B)
```

with duration:

```text
D_ticks = B - A
```

throughput is conceptually:

```text
completed_flow_units_in_[A,B) / simulation_time_[A,B)
```

The denominator is always simulation time under ADR 0001, never wall-clock time.

### 2. `boundary_flow_rate`, `input_rate`, `output_rate`, and `throughput` are distinct concepts

FISL distinguishes a generic boundary rate from system throughput.

#### `input_rate`

Rate of material/work admitted through explicitly selected source ports.

It derives from `source_withdrawal` observations.

#### `output_rate`

Rate of material/work delivered through explicitly selected sink ports.

It derives from `sink_delivery` observations.

#### `boundary_flow_rate`

A more general conceptual family covering an explicitly selected direction/port set. The final schema may expose `input_rate` and `output_rate` directly rather than requiring authors to use the generic name.

#### `throughput`

Rate of **completed flow units** leaving a declared measured flow through its designated completion sink(s).

Thus every throughput is an output rate, but not every output rate is throughput.

This vocabulary prevents FISL from calling arbitrary material movement or disposal “throughput.”

### 3. Throughput uses declared completion exits

A measured flow that supports system throughput must designate one or more sink ports as **completion exits** for that flow.

Conceptually:

```yaml
flow:
  id: workpiece_flow
  system: factory
  unit: workpiece
  entry_ports:
    - workpiece_source
  completion_ports:
    - finished_goods
```

The exact schema is deferred, but the semantics are fixed:

- delivery through a completion sink contributes to throughput;
- delivery through another sink does not contribute unless that sink is explicitly part of the completion set;
- internal production events do not contribute merely because a recipe completed;
- geometric crossing does not contribute;
- demand fulfillment does not redefine whether a completed unit crossed the system boundary.

### 4. Throughput counts the same flow unit used by the compatible WIP definition

A scalar throughput metric declares or inherits a flow-unit basis.

For a conserved workpiece flow:

```text
1 fisl-finished-workpiece = 1 workpiece
```

then ten finished workpieces delivered through the completion sink contribute:

```text
10 workpieces
```

to the throughput numerator.

If multiple completion materials are allowed, every accepted material must have an exact mapping to the common flow unit.

The mapping uses exact rational coefficients in the resolved specification. FISL MUST NOT infer work-unit equivalence from prices, stack sizes, recipe ingredient totals, or other incidental game properties.

### 5. The authoritative throughput numerator is normalized `sink_delivery`, not production statistics

For v1 system throughput, FISL derives completed flow from the primitive `sink_delivery` observations produced by ADR 0003/0004 port settlement.

FISL MUST NOT use Factorio production statistics, assembler craft counts, belt contents, or geometric boundary crossings as the authoritative system-throughput numerator when an explicit completion sink defines the accounting boundary.

Those other measurements can be useful diagnostics, but they answer different questions.

This gives throughput the same declared exit boundary used by WIP accounting.

### 6. Sink delivery counts as throughput independent of current customer demand

Throughput and demand fulfillment remain distinct.

If a declared completion sink receives eight valid completed work units while only five units of customer demand are outstanding:

```text
sink_delivery      = 8 workpieces
demand_fulfilled   = 5 workpieces
surplus_delivery   = 3 workpieces
```

then the system output/throughput numerator receives all eight completed work units.

The customer-service layer receives only five fulfilled units.

Therefore:

```text
throughput != fulfillment rate
```

in general.

This preserves ADR 0003's distinction between physical completed output and external demand.

### 7. Scrap, loss, rejection, and other non-completion exits are not system throughput by default

A later scenario may have explicit exits for:

- scrap;
- rejected product;
- yield loss;
- disposal;
- rework routing outside the current system;
- other loss mechanisms.

These are accounting exits, but they do not contribute to good/completed system throughput unless the scenario explicitly defines them as completion exits for a different flow metric.

FISL may calculate their own `output_rate` or loss rate.

This supports future yield relationships such as:

```text
admission rate = completion throughput + loss rate + change in WIP rate
```

without redefining throughput.

### 8. Throughput is calculated over an explicit half-open observation window

A throughput metric must specify an observation window under ADR 0001/0004 semantics.

For window:

```text
[A, B)
```

FISL includes completion deliveries attributed to one-tick intervals that lie inside that window.

Because v1 port deliveries are interval observations, a `sink_delivery` for:

```text
[T, T+1)
```

belongs to the throughput numerator when:

```text
A <= T < B
```

Equivalently, all one-tick delivery intervals whose interval start lies in `[A,B)` are included.

A delivery settled at checkpoint `B` for interval `[B-1,B)` is included. Activity prepared for `[B,B+1)` is not.

This matches the half-open time convention used throughout FISL.

### 9. Throughput uses exact simulation-time arithmetic internally

For a window of `D_ticks` ticks and a completed work-unit quantity `Q`, the exact rate in work units per simulation tick is:

```text
Q / D_ticks
```

Human-facing units are deterministic conversions.

For example, work units per simulation minute are:

```text
Q * 3600 / D_ticks
```

because one simulation minute is exactly 3,600 ticks under ADR 0001.

The resolved calculation SHOULD preserve exact rational arithmetic as long as practical. Decimal rounding belongs to presentation/output formatting, not the scientific definition.

### 10. Zero-duration windows are invalid

A throughput metric requires:

```text
B > A
```

FISL MUST reject a zero-duration or negative-duration throughput window.

This avoids undefined rates and prevents a point event from masquerading as an instantaneous rate.

### 11. FISL does not define an unqualified “instantaneous throughput”

Discrete manufacturing output is inherently lumpy at short timescales.

A one-tick interval rate may be mathematically computed, but it is an interval rate over one tick, not an instantaneous physical rate.

FISL therefore SHOULD NOT present a bare `instantaneous_throughput` metric.

For live dashboards, a scenario may later define an explicit trailing/rolling window such as:

```text
throughput over previous 60 simulation seconds
```

The window width must be visible in the metric metadata/UI.

A smoothed visualization that is not itself a declared metric must be clearly treated as presentation, not authoritative scientific data.

### 12. Whole-phase and rolling throughput use the same numerator semantics

Whether throughput is calculated for:

- a complete measured phase;
- a fixed sub-window;
- a trailing live window;
- a later sequence of comparison windows;

the numerator always comes from the same normalized completion-delivery observations.

Only the selected temporal window changes.

The general observation-window/rolling-window syntax is deferred to the aggregation ADR; this ADR fixes the meaning of what is counted.

### 13. Cumulative completions are useful but are not themselves throughput

FISL may expose a cumulative metric such as:

```text
completed_work_units
```

which is the total normalized quantity delivered through declared completion sinks since a specified origin.

This is a count, not a rate.

Throughput is obtained only when a count is associated with a nonzero simulation-time window.

Keeping cumulative count and rate separate makes the metric dimensions explicit.

### 14. Multiple completion sinks may be aggregated only explicitly

A measured flow may have more than one valid completion sink.

For example, two parallel shipping docks may both be legitimate exits for finished work.

FISL may aggregate their deliveries into one throughput numerator only when the metric/flow definition explicitly names both sinks and validates that:

- both represent completion of the same declared flow;
- their output materials map to the same flow unit;
- a physical completion cannot be counted through both interfaces;
- their observation coverage is valid for the requested window.

Ports carrying the same item are never silently merged merely because material identities match.

This preserves ADR 0003's explicit-port rule.

### 15. Intermediate/stage rates are allowed, but should be named as stage/output rates unless they define a subsystem flow

A learner may legitimately want to know how quickly work leaves a particular machine cell or stage.

FISL can support such rates through an explicit intermediate measurement interface or a subsystem with declared boundaries.

However, an arbitrary internal production rate SHOULD NOT automatically be labeled whole-system throughput.

If a subsystem has its own explicit entry/completion boundary and compatible flow-unit semantics, it may have its own subsystem throughput.

This preserves the distinction between local flow and end-to-end system performance.

### 16. Input rate is not assumed equal to throughput

For a finite window, FISL MUST NOT assume:

```text
input_rate = throughput
```

The difference can represent changing WIP, losses, startup/drain-down effects, or other declared exits.

For a conserved no-loss flow over `[A,B)`:

```text
WIP(B) - WIP(A)
= admitted_work_[A,B) - completed_work_[A,B)
```

This balance identity provides a useful integrity/teaching relationship.

Only under appropriate steady-state/long-run conditions will average admission rate and average completion throughput converge.

FISL should make that distinction visible rather than imposing steady state by definition.

### 17. Little's Law compatibility is explicit metadata, not inferred from matching numeric values

A throughput metric may be marked Little's-Law-compatible with a WIP/cycle-time flow only if:

- it counts the same declared flow unit;
- it uses the same measured system/completion boundary;
- the WIP definition uses the corresponding admission/exit lifetime;
- the requested analysis uses compatible observation windows/averaging assumptions;
- no unmodeled loss or coverage violation breaks the conserved-flow model.

The later cycle-time and aggregation ADRs will complete these requirements.

FISL MUST NOT infer compatibility merely because the units happen to have the same display label.

### 18. Missing completion-port coverage makes throughput incomplete, not zero

If a completion sink loses its binding or the authoritative sink-delivery stream is unavailable during any part of the requested window, FISL MUST NOT silently treat the missing interval as zero completions.

The throughput result must carry incomplete/invalid coverage according to the later metric validity policy.

Likewise, if one of several explicitly aggregated completion sinks lacks coverage, the aggregate is incomplete unless the metric explicitly defines a valid degraded mode.

Missing measurement is not zero output.

### 19. Protocol violations and measurement coverage are distinct

A run can contain a protocol violation while its completion-port observation stream remains technically complete.

For example, a learner may violate a layout rule without damaging sink measurement.

FISL should therefore distinguish:

- whether throughput was measurable from complete primitive coverage;
- whether the run is valid for a particular pedagogical/research comparison.

The metric should preserve both forms of validity rather than collapsing every protocol issue into missing data.

### 20. Throughput results preserve dimensional and provenance metadata

A throughput result should be able to state at least:

```text
metric_id
flow_id / system_id
completion_ports
flow_unit
window_start_tick
window_end_tick
completed_quantity
rate
rate_unit
source_observation_types
source_measurement_methods
coverage/validity metadata
```

For canonical v1 system throughput, provenance should trace back to `sink_delivery` primitive observations and their FISL port-settlement method.

This makes the rate auditable rather than a dashboard number detached from its measurement basis.

## Proposed v1 schema shape

Illustrative only:

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
        fisl-inspected-workpiece: 1
        fisl-finished-workpiece: 1

    entry_ports:
      - workpiece_source

    completion_ports:
      - finished_goods

metrics:
  measured_throughput:
    type: throughput
    flow: workpiece_flow

    window:
      phase: measured

    display_unit: workpieces_per_minute
```

A generic input-rate metric could look conceptually like:

```yaml
metrics:
  admission_rate:
    type: input_rate
    ports:
      - workpiece_source
    basis: workpiece_flow
    window:
      phase: measured
```

And a live trailing rate might later be expressed as:

```yaml
metrics:
  live_throughput:
    type: throughput
    flow: workpiece_flow
    window:
      trailing: 60s
```

The exact window syntax is deferred to the aggregation/window ADR.

## Consequences

### Positive

- Throughput has a precise Factory Physics meaning rather than becoming a synonym for any production rate.
- The accepted sink-port apparatus provides a direct auditable completion numerator.
- Throughput remains distinct from demand fulfillment and customer service.
- Scrap/loss can be modeled as separate exits/rates without corrupting good-output throughput.
- WIP, throughput, and later cycle time can share one explicit flow-unit/boundary definition.
- Exact simulation-time arithmetic prevents wall-time/UPS effects and rate drift.
- Live rolling displays and whole-phase scientific results can share the same counting semantics.
- Input/output imbalance becomes a useful signal of WIP accumulation or depletion instead of being hidden.

### Negative / trade-offs

- Scenario authors must explicitly identify completion sinks/flows rather than relying on Factorio production statistics.
- Arbitrary internal production numbers are not automatically called throughput.
- Multi-output/yield-heavy factories require explicit flow-unit mappings and completion classification.
- A short-window throughput value can be noisy/lumpy and must be presented with its window width.
- Little's Law compatibility still requires later decisions about averaging and cycle-time semantics.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- final general observation-window syntax;
- exact rolling-window implementation/storage;
- average WIP integration over the same window;
- direct/derived cycle-time semantics;
- service-level/fulfillment-rate formulas;
- metric validity policy beyond missing-coverage principles;
- UI smoothing/graph rendering;
- stage-rate instrumentation that lacks explicit ports;
- yield/rework/scrap process details beyond classifying non-completion exits;
- final `flow` schema organization.

## Acceptance criteria for this decision

The throughput portion of Issue #1 is complete when we agree that:

1. throughput is a derived rate over an explicit nonzero simulation-time window;
2. primitive `sink_delivery` observations provide the authoritative v1 completion numerator;
3. input rate, output rate, demand fulfillment rate, and system throughput are distinct concepts;
4. throughput counts declared completed flow units through explicit completion sinks;
5. throughput uses a flow-unit basis compatible with WIP/cycle time;
6. surplus completed output still counts as throughput even when it does not fulfill demand;
7. scrap/loss/rejection exits do not count as good system throughput by default;
8. throughput window membership follows FISL's half-open interval semantics;
9. internal calculation uses exact simulation-time/rational rate arithmetic where practical;
10. FISL does not expose an unqualified instantaneous throughput metric;
11. cumulative completions are counts, not rates;
12. multiple completion sinks aggregate only when explicitly named and semantically compatible;
13. internal/stage rates are not automatically whole-system throughput;
14. admission rate and completion throughput are not assumed equal over finite windows;
15. Little's Law compatibility requires matching flow units, boundaries, coverage, and later window assumptions;
16. missing completion-port coverage makes the rate incomplete rather than zero;
17. throughput results preserve their window, unit, completion interfaces, primitive provenance, and validity metadata.
