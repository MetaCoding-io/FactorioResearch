# ADR 0010: Aggregation and Observation-Window Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

ADRs 0001–0009 define FISL's experiment clock, phases, system boundaries, ports, primitive observations, WIP, throughput, machine-state classification, service cohorts, and cycle-time methods.

Those decisions intentionally leave one major analytical layer unresolved: **aggregation**.

FISL now has several different kinds of scientific inputs:

- point-state values such as WIP and backlog at canonical boundary ticks;
- one-tick interval classifications such as productive/starved/blocked machine state;
- interval transactions such as sink delivery and source withdrawal;
- instantaneous events such as phase transitions and protocol violations;
- quantity cohorts such as demand units with observed waits;
- derived rates such as throughput.

Turning these into statements such as:

```text
average WIP = 437 workpieces
productive time = 71%
p95 demand wait = 22 seconds
peak upstream backlog = 900 plates
throughput over the last 60 seconds = 57.9/min
```

requires more than calling a statistics library. FISL must define:

- exactly which simulation intervals belong to a metric;
- how state values are integrated through time;
- how missing coverage affects a result;
- what denominator a percentage uses;
- how multiple machines are pooled;
- how percentiles are weighted;
- how rolling windows are anchored;
- how the same result can be reproduced in Lua and Python.

These semantics are part of the scientific API. They must not be left to dashboard conventions or library defaults.

## Decision

### 1. Every aggregate metric has an explicit resolved observation window

For ordinary v1 time-windowed metrics, an observation window resolves to one contiguous half-open interval:

```text
[A, B)
```

with:

```text
0 <= A < B <= experiment_end_tick
```

The interval is expressed in **experiment simulation ticks** under ADR 0001.

Authoring syntax may refer to a phase, contiguous phases, or explicit durations/ticks, but the compiled/resolved metric stores exact integer boundaries.

Examples:

```yaml
window:
  phase: measured
```

or conceptually:

```yaml
window:
  start: 5m
  duration: 20m
```

may both compile to:

```text
start_tick = 18,000
end_tick   = 90,000
```

Warm-up has no special aggregation meaning. A phase contributes to a metric only because the metric's resolved window includes it.

### 2. Ordinary v1 aggregation windows are contiguous; non-contiguous selections are deferred

A v1 aggregate window is one continuous interval.

If an author selects multiple phases for one ordinary aggregate, those phases must be contiguous in experiment time and compile to their combined half-open span.

FISL v1 does not silently aggregate arbitrary disjoint periods such as:

```text
phase 1 + phase 3 but not phase 2
```

into one ordinary mean/rate unless a future aggregation-set construct explicitly defines that behavior.

This keeps duration, coverage, time integration, and rate denominators unambiguous.

Repeated-run comparison remains a separate analysis layer.

### 3. Cohort-selection windows and observation horizons remain distinct from ordinary aggregation windows

ADR 0008 and ADR 0009 introduced metrics whose population is selected in one interval but whose outcome may be observed later.

Examples include:

- demand cohorts created during `[A,B)` whose deadlines extend beyond `B`;
- probe/cohort work admitted during one period and completed during a later drain period.

For these metrics:

- the **cohort/population window** selects subjects;
- the **observation horizon** determines how long outcomes may be resolved;
- any aggregation over the resolved outcomes is performed only after that population/horizon logic.

FISL MUST NOT collapse an observation horizon into the cohort window or treat post-window fulfillment/completion as ordinary in-window activity.

### 4. Canonical prepared-state samples define a discrete state over the following one-tick interval

ADR 0004 defines a canonical point-state sample at boundary tick `T` as the prepared state at the start of:

```text
[T, T+1)
```

For state variables whose observation contract is canonical tick-resolution prepared-state sampling, FISL therefore interprets:

```text
X(T)
```

as the state value applying to the FISL discrete observation interval:

```text
[T, T+1)
```

for aggregation purposes.

This is not a claim that Factorio's hidden physical state can never change within a tick. It is the declared resolution and state semantics of the FISL experimental model.

Therefore canonical tick-resolution WIP/backlog integration requires no interpolation between observations.

### 5. Time integration of canonical tick-resolution state uses left-boundary interval occupancy

For state `X(T)` sampled canonically at each boundary, the time exposure over window `[A,B)` is:

```text
area_X = sum_{T=A}^{B-1} X(T) * 1 tick
```

The time-weighted mean is:

```text
mean_X = area_X / (B - A)
```

For WIP:

```text
wip_work_unit_ticks = sum WIP(T)
average_WIP          = wip_work_unit_ticks / window_ticks
```

For customer backlog:

```text
backlog_unit_ticks = sum demand_backlog(T)
average_backlog    = backlog_unit_ticks / window_ticks
```

The sample at `B` is useful as the closing state/diagnostic but contributes zero exposure to `[A,B)`.

This convention is exact under FISL's one-tick prepared-state model and matches the half-open interval semantics used by ports and phases.

### 6. FISL preserves the integrated exposure as a first-class result, not only the average

For meaningful state quantities, FISL SHOULD preserve the time integral in addition to the average.

Examples:

```text
WIP area                  -> workpiece-ticks
customer backlog area     -> workpiece-ticks
external supply backlog   -> plate-ticks
```

Human-facing conversions may present:

```text
workpiece-minutes
plate-minutes
```

using exact tick conversion.

This is important because the integrated quantity often represents accumulated waiting/burden directly and can be reused without reconstructing it from rounded averages.

### 7. A lower-frequency point sample is not automatically safe for state integration

A generic point observation taken every `N > 1` ticks does not by itself prove that its value held for all unsampled ticks.

Therefore FISL MUST NOT silently integrate sparse point samples by simple arithmetic mean or implicit carry-forward.

A lower-frequency state metric can support time integration only if its declared observation method supplies an explicit interval reconstruction rule, such as a validated event-driven state transition stream or another scientifically justified hold/interpolation policy.

Canonical v1 WIP/backlog measurements that support authoritative time-weighted averages SHOULD use complete one-tick prepared-state coverage or an exactly equivalent event/change accumulator.

Optimization may change storage representation, but not the logical interval result.

### 8. Interval observations aggregate by interval membership, not discovery checkpoint

For an interval fact attributed to:

```text
[T, T+1)
```

it belongs to ordinary aggregate window `[A,B)` when:

```text
A <= T < B
```

This preserves ADR 0004/0006 semantics for transactions such as:

```text
source_withdrawal
sink_delivery
machine interval activity
```

A fact settled at checkpoint `B` for `[B-1,B)` remains included. A fact for `[B,B+1)` is excluded.

### 9. Count/sum metrics use exact interval/event quantities; rates divide only after the count is formed

For count-like observations inside `[A,B)`, FISL first calculates the exact total quantity:

```text
Q = sum eligible quantities
```

Only a rate metric divides that total by the explicit simulation-time denominator:

```text
rate = Q / (B - A)
```

FISL SHOULD retain `Q` and the denominator ticks in the result/provenance rather than only a rounded rate.

This preserves ADR 0006's exact-throughput arithmetic and makes results auditable.

### 10. Machine-state duration uses classified one-tick intervals, not point-status samples

ADR 0007 distinguishes raw point status from interval activity/classification.

For each measured production resource, the authoritative state-duration input for interval `[T,T+1)` is the one-tick classified interval result.

For a machine `m` and headline state `s`:

```text
state_ticks(m,s,[A,B))
= count of covered intervals in [A,B) classified as s
```

The mutually exclusive headline categories include:

```text
productive
starved
blocked
unavailable
disabled
idle_other
unclassified / missing coverage
```

Constraint/condition dimensions such as `energy_limited` may overlap a productive headline and therefore have their own condition-tick accumulators rather than replacing the headline-state partition.

### 11. FISL does not expose a bare `utilization` percentage without an explicit denominator

The word `utilization` is denominator-sensitive.

For example, these are different quantities:

```text
productive_ticks / full_window_ticks
productive_ticks / classified_observed_ticks
productive_ticks / available_ticks
```

FISL v1 therefore SHOULD use explicit metric names/metadata such as:

```text
productive_fraction_of_window
productive_fraction_of_classified_time
state_fraction(..., denominator=...)
```

rather than a bare `utilization`.

A future convenience name `utilization` may only be introduced by a profile that makes its denominator visible and versioned.

### 12. The full-window denominator does not silently shrink when measurement coverage is missing

For a machine expected to be observed throughout `[A,B)`:

```text
window_ticks = B - A
```

remains the full temporal denominator.

If classification is missing for `M` ticks, FISL records:

```text
classified_ticks = window_ticks - M
coverage_fraction = classified_ticks / window_ticks
```

It MUST NOT automatically report:

```text
productive_ticks / classified_ticks
```

as though it were the same thing as productive fraction of the full window.

If the classified-time fraction is useful, it must be explicitly named as such and accompanied by coverage.

Missing measurement is not a reason to renormalize silently.

### 13. Availability-based denominators must name which states are excluded

A metric may legitimately ask how productive a resource was **while considered available**.

But `available_time` is a policy definition, not a primitive fact.

Such a metric must explicitly define its denominator state set or exclusion set.

For example, a profile might define:

```text
available_time =
    productive + starved + blocked + idle_other
```

while excluding:

```text
unavailable + disabled
```

Another experiment may choose differently, especially if deliberate disablement is part of normal control policy.

FISL MUST preserve the denominator definition in metric provenance and MUST NOT hard-code one universal availability formula into the machine-state classifier.

### 14. Multi-machine state aggregation defaults to pooled machine-time only when explicitly requested

For an entity set containing machines `m1...mn`, one useful aggregate is **pooled machine-time**:

```text
pooled_state_ticks(s)
= sum_m state_ticks(m,s)
```

with denominator:

```text
pooled_eligible_ticks
= sum_m eligible_ticks(m)
```

This weights one machine-tick as one unit of resource-time.

It is distinct from:

```text
mean of per-machine state fractions
```

when machines have different lifetimes or coverage.

FISL MUST preserve per-machine results and must record which cross-entity aggregation method was used.

Canonical v1 line-level state summaries SHOULD use pooled machine-time when the goal is to describe how the production-resource pool spent its time.

### 15. Peak/minimum state metrics use covered interval values and preserve timing

For a time-state metric such as WIP or backlog, FISL may derive:

```text
min
max / peak
```

over eligible canonical interval states in `[A,B)`.

A peak result SHOULD retain at least one tick/location in time where the peak occurred, or enough provenance to recover it.

The closing state at `B` is not part of the interval-state population for `[A,B)` unless a metric explicitly requests boundary diagnostics rather than time occupancy.

### 16. Time-weighted percentiles use simulation-time exposure as weight

For a state quantity such as WIP, a percentile describes the distribution experienced over simulation time.

For canonical tick-resolution samples, each interval value has weight:

```text
1 tick
```

For an equivalent event/change representation, each state value has weight equal to its covered duration.

Thus `p95_wip` means:

> the weighted empirical 95th percentile of WIP over eligible simulation time.

It is not the 95th percentile of an arbitrary set of logging timestamps.

### 17. Quantity-time distributions use quantity as weight when the population is quantity-based

For demand waiting time under ADR 0008, fulfillment allocations may represent more than one demanded unit.

If:

```text
wait = 10s, quantity = 5
wait = 20s, quantity = 1
```

then a quantity-weighted waiting-time distribution contains five units at 10 seconds and one unit at 20 seconds.

Likewise, cohort-response completion distributions may weight completion timestamps by completed quantity when the metric is defined over units rather than cohort events.

The metric must declare its weighting domain, for example:

```text
time_weighted
quantity_weighted
entity_weighted
unweighted_event
```

FISL MUST NOT let a statistics library choose this implicitly.

### 18. V1 uses one deterministic weighted empirical quantile rule

To avoid different percentile answers from Lua, Python, spreadsheets, or plotting-library defaults, FISL v1 uses a deterministic **weighted nearest-rank empirical quantile** for weighted distributions.

For observations `(x_i, w_i)` with positive weights, sorted by `x_i`, and percentile `p` where:

```text
0 < p <= 1
```

let:

```text
W = sum w_i
threshold = p * W
```

The quantile is the smallest `x_i` for which cumulative weight is greater than or equal to `threshold`.

No interpolation between physically unobserved values is performed by the scientific metric.

If a visualization wants an interpolated curve, that is presentation only.

Minimum is exposed directly as `min`; a `p=0` quantile is unnecessary in v1.

### 19. Means over quantity distributions are explicitly quantity-weighted

For demand waits or other quantity-cohort measurements:

```text
mean_wait
= sum(wait_i * quantity_i) / sum(quantity_i)
```

when the metric is defined per demanded unit.

An unweighted mean of cohort records would answer a different question because one one-unit cohort and one hundred-unit cohort would receive equal weight.

FISL therefore records the population/weighting semantics with the result.

### 20. Empty populations produce `undefined/no_data`, not fabricated zero or perfect performance

If a metric requires a nonempty population and none exists, FISL does not invent a numeric result.

Examples:

- no demand cohorts in the selected service population;
- no completed probe units for a completion-time percentile;
- no classified machine intervals due to total coverage failure.

The result is semantically:

```text
no_data / undefined
```

with the reason preserved.

In particular, zero demand does not imply either 0% or 100% customer service.

Zero-duration ordinary windows are invalid under the existing throughput/time rules.

### 21. Missing source coverage makes canonical scientific aggregates incomplete by default

For canonical v1 scientific metrics, the default missing-data policy is **strict coverage**.

If required primitive/state coverage is missing for any eligible portion of the window/population, the aggregate result is marked incomplete rather than silently:

- filling zero;
- carrying the previous value forward;
- deleting the missing interval from the denominator;
- interpolating;
- treating unresolved cohorts as failures/successes.

FISL may still calculate and expose a partial diagnostic value when useful, but it must be labeled partial and accompanied by:

```text
coverage_fraction
missing_ticks / missing_quantity
missing reason(s)
```

Objectives and research comparisons SHOULD default to requiring complete coverage unless explicitly configured otherwise.

### 22. Rolling/trailing windows are anchored at a boundary and contain only settled history

For a trailing window of width `L` evaluated at experiment boundary tick `T`, the canonical historical window is:

```text
[T-L, T)
```

provided `T >= L`.

It contains only intervals that have fully occurred and been settled by checkpoint `T`.

For example, a trailing-60-second throughput shown at boundary `T` uses completion intervals in the previous 3,600 ticks.

A current point state such as `WIP(T)` is a separate current-value display and is not inserted into the historical average for `[T-L,T)` as an extra sample.

This avoids look-ahead and off-by-one leakage.

### 23. Incomplete early rolling windows must declare their startup policy

Before a trailing window has accumulated its full requested width, FISL must not silently change the definition.

A metric/profile may choose one of at least these explicit behaviors:

```text
not_available_until_full
partial_window_with_actual_duration
```

Canonical scientific rolling metrics SHOULD default to:

```text
not_available_until_full
```

so a “60-second throughput” means 60 seconds of history.

A learner UI may choose partial startup behavior if it visibly reports the actual duration.

### 24. Fixed scientific metrics and live display metrics can share semantics without sharing storage strategy

A whole-phase metric and a live rolling metric may consume the same primitive fact stream while using different windows.

FISL may implement aggregates using:

- streaming Lua accumulators;
- retained primitive observations;
- Python post-run calculation;
- a combination of these.

However, implementation location does not define the result.

Given the same resolved scenario, primitive fact stream, and metric definition, authoritative Lua and Python implementations MUST be capable of reproducing the same logical result within the declared numeric representation/rounding rules.

### 25. Scientific values use exact integer/rational accumulators where practical; rounding is presentation

FISL's source observations are frequently integer counts and integer tick durations.

Canonical accumulators SHOULD retain exact quantities such as:

```text
work_unit_ticks
state_ticks
completed_units
window_ticks
quantity_wait_ticks
```

and compute ratios/rates from those exact numerators/denominators.

Decimal formatting such as:

```text
57.9/min
71.2%
```

belongs to presentation.

The result/provenance should retain enough exact numerator/denominator data to recompute the displayed value.

### 26. Aggregation dependencies must use compatible windows unless the metric explicitly defines a cross-window relationship

A derived metric that combines other time-windowed metrics must verify that their resolved windows are semantically compatible.

For example, ADR 0009's:

```text
CT_LL = average_WIP / throughput
```

requires both average WIP and throughput to refer to the same analysis window and flow.

FISL MUST NOT silently divide:

```text
average WIP from measured phase
```

by:

```text
throughput from entire experiment
```

merely because both values exist.

Metrics with intentionally different cohort/horizon windows must declare that relationship explicitly.

### 27. Aggregation results preserve their method, weighting, window, denominator, and coverage provenance

An aggregate result must be able to expose at least:

```text
metric_id
aggregation_type
resolved_window_start_tick
resolved_window_end_tick
population/subject scope
weighting_method
source observation/metric dependencies
exact numerator/denominator or integrated exposure where applicable
coverage_fraction / unresolved population
missing-data policy
result unit
presentation/display unit if different
```

For state-duration fractions, provenance also includes the denominator definition.

For percentiles, provenance includes the quantile rule and weighting domain.

For rolling metrics, provenance includes the requested width and actual resolved width.

### 28. The same aggregation vocabulary applies to upstream, internal, and downstream waiting

The source-buffer model, WIP model, and demand model now expose analogous state quantities:

```text
external supply pending
internal WIP
demand backlog
```

FISL can therefore apply the same time-integration semantics to all three:

```text
upstream backlog item-ticks
WIP work-unit-ticks
customer backlog work-unit-ticks
```

This consistency is intentional. It allows students to compare **where waiting resides** without pretending the three states are economically or operationally identical.

### 29. V1 aggregate vocabulary should remain small and composable

Canonical v1 aggregation should support a compact set of well-defined operations sufficient for Labs 0–6:

```text
sum/count
time integral
mean
min/max
state duration
state fraction with explicit denominator
weighted empirical percentile
rolling/trailing application of the same operations
```

Additional statistics such as variance, standard deviation, autocorrelation, confidence intervals, spectral analysis, and hypothesis testing are useful future analytical features but are not required to define the v1 scientific runtime contract.

The raw/primitive data should remain sufficient for external analysis tools to compute them later.

## Illustrative v1 schema shapes

Exact schema syntax remains deferred.

### Time-weighted WIP

```yaml
metrics:
  average_wip:
    type: aggregate
    source: line_wip
    aggregation: time_mean
    window:
      phase: measured
```

Conceptually this resolves to:

```text
sum(WIP(T), T in measured intervals) / measured_ticks
```

### WIP percentile

```yaml
metrics:
  p95_wip:
    type: aggregate
    source: line_wip
    aggregation: percentile
    p: 0.95
    weighting: simulation_time
    quantile_method: weighted_nearest_rank
    window:
      phase: measured
```

### Machine state fraction

```yaml
metrics:
  line_productive_fraction:
    type: state_fraction
    source: machine_state
    entities: line_machines
    state: productive
    entity_aggregation: pooled_machine_time
    denominator: full_window
    window:
      phase: measured
```

### Explicit available-time productivity

```yaml
metrics:
  productive_when_available:
    type: state_fraction
    source: machine_state
    entities: line_machines
    state: productive
    denominator:
      states:
        - productive
        - starved
        - blocked
        - idle_other
    window:
      phase: measured
```

### Rolling throughput

```yaml
metrics:
  live_throughput:
    type: throughput
    flow: workpiece_flow
    window:
      trailing: 60s
      startup: not_available_until_full
```

### Demand-wait percentile

```yaml
metrics:
  p95_customer_wait:
    type: demand_wait_percentile
    demand: customer_demand
    cohort_window:
      phase: measured
    observation_horizon:
      through_phase: service_tail
    p: 0.95
    weighting: demanded_quantity
    quantile_method: weighted_nearest_rank
```

## Consequences

### Positive

- Average WIP and backlog have exact, auditable simulation-time meanings.
- Little's-Law-derived cycle time gets the authoritative time-weighted WIP numerator it requires.
- Machine-state percentages no longer hide denominator choices.
- Missing coverage cannot silently improve or degrade a percentage by changing its denominator.
- Time-weighted and quantity-weighted percentiles are explicitly distinguished.
- Lua, Python, dashboards, and exported analysis can share one percentile/aggregation contract instead of library defaults.
- Rolling displays cannot accidentally include future/current unsatisfied intervals.
- Integrated waiting quantities expose accumulated congestion upstream, inside the system, and downstream using one consistent mechanism.
- Exact integer/tick accumulators preserve reproducibility and avoid rounding drift.

### Negative / trade-offs

- Metric definitions are more explicit than casual dashboard configuration.
- One-tick canonical state coverage can require significant observation/accumulation work, although storage may be optimized with equivalent change/event encoding.
- FISL intentionally refuses to auto-renormalize around missing data, so some runs will report incomplete results rather than convenient percentages.
- Weighted nearest-rank percentiles may differ from interpolated defaults in common statistics packages, requiring adapters/tests.
- Bare `utilization` remains unavailable unless a later profile explicitly defines its denominator.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- learner/instructor/debug visibility of aggregate metrics;
- objective pass/fail syntax and how objectives treat incomplete metrics;
- final metric validity/status enum names;
- long-term telemetry retention/downsampling format;
- persistence/storage optimization for one-tick state series;
- statistical steady-state detection;
- cross-run confidence intervals/statistical tests;
- non-contiguous aggregate windows;
- final YAML/Pydantic schema syntax.

## Acceptance criteria

The aggregation/window portion of Issue #1 is complete when we agree that:

1. ordinary aggregate metrics resolve to explicit contiguous half-open simulation-time windows;
2. cohort windows and observation horizons remain semantically distinct;
3. canonical prepared-state sample `X(T)` represents FISL state over `[T,T+1)` for tick-resolution aggregation;
4. time-weighted state integration uses `sum X(T) * 1 tick` over interval starts in the window;
5. the closing point at `B` is diagnostic but contributes no occupancy to `[A,B)`;
6. integrated exposures such as WIP/backlog unit-ticks remain first-class results;
7. sparse point samples are not silently treated as continuous state without an explicit reconstruction method;
8. interval facts aggregate according to their attributed interval, not settlement checkpoint;
9. machine-state durations use ADR 0007's classified intervals rather than raw point statuses;
10. a bare utilization percentage is forbidden without an explicit denominator definition;
11. missing coverage does not silently shrink denominators or become zero;
12. multi-machine pooling explicitly uses pooled machine-time or another named aggregation method;
13. time-state percentiles are weighted by simulation-time exposure;
14. demand/cohort percentiles are quantity-weighted when defined per unit;
15. v1 uses deterministic weighted nearest-rank empirical quantiles without scientific interpolation;
16. empty populations produce undefined/no-data rather than fabricated 0%/100%/zero values;
17. strict coverage is the default for canonical scientific metrics, with partial results visibly labeled;
18. trailing window `[T-L,T)` contains only settled historical intervals and has an explicit startup policy;
19. authoritative aggregate semantics are implementation-independent between Lua streaming and Python post-run calculation;
20. exact integer/rational numerator/denominator quantities are retained where practical and display rounding is non-authoritative;
21. derived metrics such as Little's-Law cycle time verify window compatibility rather than silently combining unlike periods;
22. aggregate results preserve window, weighting, denominator, quantile/method, source dependencies, and coverage provenance.
