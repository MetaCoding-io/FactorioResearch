# ADR 0008: Service-Level and Demand-Cohort Semantics

- **Status:** Proposed
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

ADR 0003 established an external demand process attached to a sink, with backlog as the v1 shortage policy. ADR 0004 established exact simulation-time observations. ADR 0006 separated completed production throughput from demand fulfillment.

FISL now needs a rigorous meaning for **service level**.

A bare percentage such as:

```text
service level = 95%
```

is ambiguous. It might mean:

- 95% of demanded items were eventually delivered;
- 95% were delivered immediately;
- 95% were delivered within a specified wait tolerance;
- 95% of orders were filled completely;
- 95% of replenishment cycles had no stockout;
- backlog was zero for 95% of the time.

Those are different measurements.

A second problem is temporal matching. The apparently simple finite-window ratio:

```text
fulfillment during window / demand created during window
```

is generally not a valid service metric. If the window begins with backlog, fulfillment during the window may satisfy old demand and the ratio can exceed 100%. If the window ends with newly created demand that has not yet had time to be served, the same ratio can understate service. Numerator and denominator are not necessarily the same demand population.

FISL therefore needs a cohort-based demand accounting model that can answer when demand was created and how long each demanded quantity waited, while avoiding the premature complexity of order objects.

## Decision

### 1. FISL does not expose a bare, semantically unspecified `service_level` metric

Scenario authors must choose an explicit service definition.

V1's canonical customer-service metric is:

```text
on_time_item_rate
```

which measures the fraction of demanded **item/work-unit quantity** fulfilled within a declared maximum wait.

Other service-adjacent quantities such as backlog and backlog-free time may be measured separately, but they are not aliases for `on_time_item_rate`.

Order-level and replenishment-cycle service metrics are deferred until their underlying objects exist in the scientific model.

### 2. V1 demand remains quantity-based; demand cohorts are not customer orders

Each demand process maintains an internal FIFO sequence of **demand cohorts**.

A demand cohort is the homogeneous quantity created by one demand process at one experiment boundary tick.

Conceptually:

```text
cohort:
  demand_process_id
  material / flow unit
  created_tick
  original_quantity
  remaining_quantity
```

A cohort is an accounting structure used to retain age/provenance of demand quantity.

It is **not** an order object and carries no implicit concepts such as:

- order ID;
- customer identity;
- multi-line order contents;
- all-or-nothing order completion;
- order priority;
- promised date independent of the service policy.

Those can be added later without changing the v1 quantity-service semantics.

### 3. Every `demand_created` transaction creates or extends a demand cohort

When ADR 0003's demand scheduler creates quantity `Q` at boundary tick `T`, FISL records the existing primitive:

```text
demand_created = Q
```

and adds that quantity to a cohort whose `created_tick = T`.

If implementation efficiency combines multiple same-process creations at the exact same boundary into one cohort, that does not alter the scientific semantics.

Demand cohorts are part of the authoritative demand ledger and therefore must be reproducible from primitive demand/fulfillment observations or preserved directly in the run data needed for service metrics.

### 4. Fulfillment is allocated FIFO to the oldest outstanding demand quantity

For a v1 backlog demand process, sink deliveries allocated to demand are matched against outstanding cohorts in ascending `created_tick` order.

Conceptually:

```text
oldest backlog
     ↓
next oldest
     ↓
newest backlog
```

This FIFO rule gives each fulfilled unit an unambiguous demand age and prevents a later demand cohort from being declared on-time while older identical demand remains waiting.

If future experiments need priorities, classes of service, reservations, or non-FIFO allocation, they require an explicit policy rather than silently changing v1 semantics.

### 5. Demand fulfillment records retain cohort-age information

ADR 0003's `demand_fulfilled` observation remains a primitive accounting fact, but service analysis needs to know which creation cohort was fulfilled.

The normalized fulfillment data therefore must be capable of retaining at least:

```text
demand_process_id
created_tick
fulfillment_tick
quantity
```

or an equivalent auditable linkage.

One physical sink delivery may fulfill quantities from several cohorts; the normalized fulfillment stream may therefore contain several cohort-allocation records derived from one `sink_delivery`.

The sum of those allocations must equal the `demand_fulfilled` quantity attributed to that delivery.

### 6. Fulfillment time is the settlement boundary at which delivery is recognized

A demand cohort created at experiment boundary `T` becomes outstanding for upcoming interval `[T,T+1)` under ADR 0003/0004.

A physical delivery occurring during interval `[F-1,F)` is recognized when the sink is settled at boundary `F`.

For service timing, that fulfilled quantity therefore has:

```text
created_tick    = T
fulfillment_tick = F
wait_ticks       = F - T
```

The earliest normal port-backed fulfillment of demand created at `T` is therefore boundary `T+1`.

This follows the accepted causal pipeline rather than inventing sub-tick customer-service timing.

### 7. `on_time_item_rate` requires an explicit maximum-wait tolerance

A v1 `on_time_item_rate` metric declares:

```text
max_wait_ticks = L
```

or an authoring-time duration that compiles exactly to ticks.

A demanded unit created at tick `T` is on time if it is fulfilled at boundary `F` such that:

```text
F - T <= L
```

Equivalently, its service deadline is:

```text
deadline_tick = T + L
```

and fulfillment is on time when:

```text
fulfillment_tick <= deadline_tick
```

Because normal v1 demand cannot be fulfilled before the first subsequent settlement, canonical port-backed scenarios SHOULD use `L >= 1 tick`.

A human-facing lab will normally use tolerances such as seconds or minutes rather than a one-tick threshold.

### 8. The canonical service numerator and denominator refer to the same demand cohort population

For an explicitly selected set of eligible demand cohorts `C`:

```text
on_time_item_rate =
    on_time_quantity(C)
    / total_created_quantity(C)
```

where both numerator and denominator refer to demand **created in the same cohort-selection window**.

This is the central correction to the invalid formula:

```text
fulfillment events in window / demand events in window
```

Fulfillment may occur after the demand-creation window and still count for that cohort if it meets the deadline.

Fulfillment of demand created before the cohort window does not enter the numerator for that metric, even if it occurs during the metric's observation horizon.

### 9. A service metric separates the demand-cohort window from the fulfillment observation horizon

A service metric needs two temporal concepts:

1. **cohort window** — which demand creation events are being evaluated;
2. **observation horizon** — how long FISL watches those cohorts to determine whether their deadlines were met.

Conceptually:

```text
cohort window:       [A, B)
max wait:             L
required observation: through at least B-1 cohort's deadline
```

A demand unit created near the end of `[A,B)` must not be called late merely because the measured production phase ended before its allowed wait expired.

The final aggregation/window ADR will define reusable syntax, but this semantic separation is fixed here.

### 10. Unobserved deadlines are censored/incomplete, not automatically failed service

If FISL stops observing a cohort before its deadline, that quantity has an unresolved service outcome.

It MUST NOT silently count as:

- on time;
- late;
- fulfilled;
- zero demand.

Instead the service metric is incomplete/censored for that cohort population unless the scenario's observation horizon extends far enough to resolve all deadlines.

Canonical v1 teaching scenarios SHOULD be designed so all demand cohorts included in the reported service metric have fully observed deadlines.

This can be achieved by, for example:

- ending the demand-cohort window before the run ends;
- adding a non-demand observation/drain phase;
- otherwise extending the run through the latest required deadline.

### 11. Passing the deadline fixes the on-time outcome even if the demand is fulfilled later

If a demand unit remains unfulfilled after its deadline, it has missed the on-time service target.

A later delivery still:

- reduces backlog;
- records eventual fulfillment;
- contributes to throughput if it crossed a completion sink;

but it does not retroactively convert that unit to on-time service.

Thus FISL distinguishes:

```text
on-time fulfilled
late fulfilled
still outstanding
```

for cohort quantities.

This lets a factory recover backlog without rewriting its historical service performance.

### 12. Partial cohort fulfillment is quantity-weighted

A cohort may be partially fulfilled before the deadline and partially afterward.

For example:

```text
cohort created:   100 units
on time:           92 units
late:               8 units
```

Then that cohort contributes:

```text
92 / 100
```

to a quantity-based `on_time_item_rate` numerator/denominator.

FISL v1 does not convert the entire cohort to failure merely because one item was late. Doing that would be an order/cycle-style metric and requires a different semantic object.

### 13. Demand backlog remains a state quantity distinct from service rate

At boundary tick `T`, `demand_backlog(T)` is the currently outstanding quantity across all unfulfilled cohorts for that demand process.

It is not itself a service-level percentage.

Useful derived backlog metrics may include later:

```text
current backlog
peak backlog
average backlog
backlog unit-ticks
fraction of time backlog > 0
fraction of time backlog == 0
```

These answer different operational questions from `on_time_item_rate`.

A system can have a high on-time item rate but occasional large short-lived backlog, or a modest backlog almost continuously. FISL should preserve both views.

### 14. `backlog_free_time_fraction` is allowed as an explicitly named service-adjacent metric

A later aggregation may define:

```text
backlog_free_time_fraction =
    simulation time with demand_backlog == 0
    / eligible observation time
```

This can be pedagogically useful for understanding stockout exposure or persistent queueing.

However FISL MUST NOT label this bare `service_level` because it weights time rather than demanded quantity.

The exact integration rule belongs to the aggregation/window ADR.

### 15. V1 does not expose order-fill rate or cycle-service level without order/cycle objects

The following metrics are deferred:

```text
order_fill_rate
on_time_order_rate
cycle_service_level
probability_of_no_stockout_per_replenishment_cycle
```

because FISL v1 does not yet have authoritative semantic objects for:

- customer orders;
- multi-line orders;
- order completeness;
- replenishment cycles.

FISL MUST NOT approximate these by treating each simulation tick's demand cohort as if it were a customer order or replenishment cycle.

Demand cohorts exist to preserve item-quantity age, not to create artificial business objects.

### 16. “Fill rate” is avoided as an unqualified metric name in v1

In operations/inventory practice, `fill rate` is used with multiple conventions, often involving immediate quantity availability.

To avoid importing an unstated convention, FISL v1 uses explicit names such as:

```text
on_time_item_rate
backlog_free_time_fraction
```

A future metric named `item_fill_rate` must define precisely whether “filled” means immediate service, service within one tick, service within a declared tolerance, or another policy.

The schema should favor explicit semantic names over familiar but overloaded terminology.

### 17. Surplus delivery does not improve service for future demand

ADR 0003 established that output delivered before demand exists is `surplus_delivery` and does not create a hidden customer-side inventory credit.

Therefore surplus delivery cannot improve the on-time outcome of a future demand cohort.

If an experiment needs finished goods to satisfy future demand immediately, that inventory must be modeled explicitly in a declared buffer/warehouse whose relation to the system boundary is known.

This preserves the distinction among:

- production throughput;
- finished-goods inventory;
- customer demand;
- customer service.

### 18. Multiple demand processes remain separate unless explicitly aggregated

A sink/system may eventually have multiple demand processes or customer classes.

Each process has its own cohort ledger and service result.

FISL MUST NOT silently aggregate service across processes merely because they request the same material.

An aggregate quantity-weighted service metric may explicitly combine compatible demand processes, in which case its numerator and denominator are sums over the named cohort populations.

Future priority/customer-class policies may make some cross-process aggregations inappropriate, so aggregation must remain explicit.

### 19. Service metrics preserve cohort, deadline, and coverage provenance

An `on_time_item_rate` result should be able to report at least:

```text
metric_id
demand_process_id(s)
material / flow unit
cohort_window_start_tick
cohort_window_end_tick
max_wait_ticks
observation_horizon_end_tick
total_demand_quantity
on_time_quantity
late_quantity
unresolved_quantity
rate
source observation types/methods
coverage/validity metadata
```

The metric should be auditable back to:

```text
demand_created
cohort allocation
demand_fulfilled
```

and the corresponding sink-delivery settlement provenance.

### 20. Service validity and experiment protocol validity remain separate

A service metric can have complete cohort/deadline coverage even if the learner committed an unrelated protocol violation.

Conversely, a perfectly protocol-compliant run can have incomplete service measurement if the run ended before deadlines were observable.

FISL therefore preserves separately:

- measurement coverage/completeness;
- service outcome;
- experiment/protocol validity.

A service percentage must not hide missing cohort outcomes.

### 21. Canonical Factory Physics push/pull labs SHOULD use `on_time_item_rate` as the service constraint

For the first production-control labs, a useful objective form is:

```text
maintain on_time_item_rate >= 95%
within max_wait = X simulation seconds/minutes
```

while simultaneously minimizing or comparing quantities such as:

- average WIP;
- peak WIP;
- capacity;
- upstream supply backlog;
- machine-state distributions.

This creates the intended Factory Physics trade-off:

> Do not minimize WIP by simply refusing to serve the customer.

Likewise, do not maximize throughput by grossly overproducing unless the scenario objective permits the resulting inventory/control consequences.

The exact numeric tolerance/target is scenario-specific, not hard-coded into FISL.

### 22. Demand waiting-time distributions are enabled but not fully specified here

The cohort ledger naturally makes quantities such as these possible:

```text
mean demand wait
median demand wait
95th-percentile demand wait
late-unit wait distribution
```

However, percentile/aggregation rules belong to the aggregation ADR, and customer-demand wait is distinct from end-to-end production cycle time.

This ADR only requires preserving enough cohort timing information to support those later metrics accurately.

## Proposed v1 schema shape

Illustrative only:

```yaml
ports:
  customer_shipments:
    system: factory
    direction: sink
    material:
      item: fisl-finished-workpiece

    demand:
      id: customer_demand
      shortage_policy: backlog
      allocation: fifo
      schedule:
        type: constant
        rate: 60/min

metrics:
  customer_service:
    type: on_time_item_rate
    demand: customer_demand

    cohort_window:
      phase: measured

    max_wait: 30s

    observation_horizon:
      through_phase: service_tail
```

A scenario might therefore use phases such as:

```yaml
phases:
  - id: warmup
    duration: 5m

  - id: measured
    duration: 20m

  - id: service_tail
    duration: 30s
```

where demand creation can be disabled in `service_tail` while FISL continues observing fulfillment of the measured demand cohorts.

The final phase-policy and window syntax will be settled in the schema/aggregation pass.

## Consequences

### Positive

- “95% service” becomes a precise, auditable statement rather than a dashboard convention.
- Numerator and denominator always refer to the same demand population.
- Opening backlog cannot artificially inflate a service ratio.
- End-of-window demand is not unfairly classified before its service tolerance expires.
- FIFO cohort accounting supports age, lateness, and waiting-time analysis without prematurely modeling customer orders.
- Service remains distinct from throughput, surplus production, and backlog magnitude.
- The model extends naturally to future order/customer-priority semantics without redefining v1 item service.
- Push/pull labs can constrain customer service while allowing students to optimize WIP/capacity/control choices.

### Negative / trade-offs

- The demand ledger must retain cohort age rather than only cumulative counters.
- A scientifically complete service result may require an observation tail beyond the demand-creation window.
- `on_time_item_rate` is more verbose than the familiar but ambiguous label `service level`.
- Order-level service and cycle-service metrics remain unavailable until FISL models their semantic objects.
- FIFO allocation is a real policy choice; future priority-service experiments will need an extension.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- final general window/horizon schema syntax;
- percentile/wait-time aggregation;
- order objects and order-level service;
- replenishment-cycle semantics;
- customer classes/priorities;
- lost-sales/expiration policies;
- immediate-service semantics backed by explicit finished-goods inventory;
- UI presentation of service/backlog distributions;
- exact objective syntax.

## Acceptance criteria

The service-level portion of Issue #1 is complete when we agree that:

1. FISL does not expose a bare ambiguous `service_level` metric;
2. v1's canonical service metric is quantity-based `on_time_item_rate` with an explicit maximum wait;
3. demand is retained in FIFO age cohorts by creation tick without treating cohorts as customer orders;
4. fulfillment is allocated to oldest outstanding demand first;
5. fulfillment records retain enough cohort linkage to determine wait/lateness;
6. service timing uses the FISL settlement boundary and exact simulation ticks;
7. numerator and denominator refer to the same demand-creation cohort population;
8. the cohort-selection window is distinct from the fulfillment observation horizon;
9. cohorts whose deadlines were not observed are unresolved/censored rather than automatically late;
10. passing a deadline fixes the on-time failure even if backlog is later recovered;
11. partial fulfillment is quantity-weighted rather than all-or-nothing at the cohort level;
12. backlog metrics remain distinct from quantity service rate;
13. order-fill/cycle-service metrics are deferred until orders/cycles exist explicitly;
14. surplus delivery cannot retroactively serve future demand;
15. service results preserve cohort/deadline/provenance and measurement completeness metadata;
16. canonical push/pull labs can use an explicit on-time item rate as a customer-service constraint alongside WIP/throughput analysis.
