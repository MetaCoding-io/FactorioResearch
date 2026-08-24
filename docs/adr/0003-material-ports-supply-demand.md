# ADR 0003: Material Ports, Supply, Demand, and Boundary Transactions

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

ADR 0002 established that geometric zone crossing is **not** the authoritative definition of material entering or leaving a FISL system. FISL therefore needs explicit boundary interfaces whose behavior is reproducible, measurable, and understandable to learners.

For the first Factory Physics labs, these interfaces must support effectively unconstrained raw-material supply, rate-limited supply, finished-goods output collection, customer demand/backlog, and authoritative input/output observations. The design must also leave a clean path toward stochastic supply/demand, failures, costs, finite warehousing, perishability, and multi-system experiments.

A key runtime constraint is that Factorio exposes inventory contents and script insertion/removal but not a universal gross event stream for every arbitrary inserter transfer. FISL therefore must be explicit about what is directly observed and must not claim precision the apparatus cannot support.

## Decision

### 1. A material `port` is an explicit system-boundary interface

A FISL material port is a logical interface between one declared system and its external environment. It answers:

> At what declared interface do items enter or leave the system, and how does FISL account for that exchange?

A port is not merely a chest, coordinate, or zone edge. A physical Factorio entity is an implementation endpoint bound to the logical port.

Every v1 material port references exactly one FISL system.

### 2. V1 material-port directions are `source` and `sink`

- `source` — external material is made available and may enter the system.
- `sink` — material leaves the system and is accepted by the external environment.

Ports are one-way in v1. Bidirectional and direct system-to-system material interfaces are deferred.

### 3. Demand is not a port type

`demand` is an exogenous process optionally attached to a sink.

```text
source / sink = physical/accounting boundary direction

demand        = external requirement over time
```

A sink can therefore measure pure output throughput without a customer model, while the same sink can later carry demand/backlog/service semantics.

### 4. V1 ports track one material identity and one endpoint

Each v1 port tracks exactly one item identity and binds to one inventory-bearing Factorio endpoint.

The scenario-level contract does not depend on whether that endpoint is implemented as a FISL-specific custom entity, a protected native container, or another inventory-bearing apparatus satisfying the contract.

At `READY`, the binding must resolve unambiguously and FISL records at least the logical port ID, system ID, direction, material identity, surface, endpoint prototype/position, runtime entity identifier when available, usable inventory capacity, and measurement method.

Loss of an authoritative port endpoint during a run preserves collected data but should abort the run rather than continue producing apparently valid boundary metrics.

### 5. Standard port apparatus is controlled experimental equipment

Standard FISL port endpoints SHOULD be visually distinctive and protected from normal learner manipulation as far as Factorio permits without preventing intended automated transfer. Appropriate endpoints should be non-minable, non-destructible, and non-operable through ordinary player inventory interaction.

Port apparatus represents the experimental bench rather than the learner's factory.

### 6. Port inventories are external to normal system WIP

Items waiting in source staging have not yet entered the measured production system. Items delivered to sink staging have reached the output boundary and are being accepted by the external environment.

Therefore FISL-owned port inventories are excluded from ordinary internal WIP unless a future scenario explicitly models a boundary warehouse as part of the measured system.

### 7. V1 ports use deterministic per-tick settlement

Each active port participates in one FISL-controlled settlement per executed simulation tick.

Settlement is the authoritative accounting point at which FISL:

1. reconciles endpoint changes from the completed tick interval;
2. records source/sink boundary observations;
3. settles sink output against already-outstanding demand;
4. advances supply/demand schedules;
5. prepares source availability and demand state for the next interval.

The exact callback location within the complete FISL per-tick pipeline is deferred to the primitive-observation contract, but the causal semantics are fixed here.

### 8. Source input is measured as net withdrawal from staging

After source settlement, FISL retains the source tracked-item count as the previous post-settlement state. At the next settlement, before adding newly available supply:

```text
source_withdrawal = previous_post_settlement_count
                    - current_pre_settlement_count
```

when positive.

This quantity is the authoritative v1 input boundary observation for the completed interval.

The method is explicitly **net inventory settlement**, not a claim of exact gross transfer history. Reverse flow into a source is therefore prohibited by the v1 protocol; standard apparatus/layout should make it difficult, and detectable reverse flow is a protocol violation.

### 9. Sink output is recorded and removed at settlement

At each sink settlement, FISL reads the tracked material present in sink staging. That quantity is recorded as `sink_delivery` for the completed interval and then removed from staging, normally returning the sink tracked-item count to zero.

This settlement event is the authoritative v1 output boundary transaction.

### 10. Output and demand fulfillment are distinct observations

Every valid item accepted at a sink is system output regardless of customer demand.

FISL distinguishes:

- `sink_delivery` — output crossing the declared system boundary;
- `demand_fulfilled` — the portion of that output satisfying already-outstanding demand;
- `surplus_delivery` — delivered output in excess of already-outstanding demand.

Surplus delivery does not automatically satisfy future demand. If an experiment requires finished-goods inventory that can serve later demand, that inventory must be explicitly represented as a warehouse/buffer with an explicit location relative to the system boundary.

### 11. V1 demand uses a backlog ledger

A demand-enabled sink creates discrete item requirements over simulation time. V1 shortage semantics use backlog.

For delivery `D` and previously outstanding backlog `B`:

```text
fulfilled = min(D, B)
surplus   = D - fulfilled
backlog   = B - fulfilled
```

Demand generated for a future interval cannot be fulfilled by surplus output from an earlier interval.

Lost-sales/expiry semantics are deferred because they require explicit due-time/expiration rules.

### 12. Supply and demand schedules use exact simulation-time accumulation

Author-facing constant rates such as `180/min` compile into deterministic discrete release arithmetic. FISL MUST NOT accumulate floating-point `items_per_tick` values in a way that introduces drift.

The same schedule interface should later admit stochastic policies without changing port semantics.

### 13. V1 supports `replenish` and `scheduled` source modes

#### `replenish`

Maintain a declared staging target after settlement:

```yaml
supply:
  mode: replenish
  target: 400
```

Use this when external raw-material availability should not be the experimental bottleneck. Physical extraction capacity still depends on the Factorio endpoint and the learner's handling system.

#### `scheduled`

Release material according to an explicit schedule:

```yaml
supply:
  mode: scheduled
  schedule:
    type: constant
    rate: 180/min
```

Use this when upstream availability is an experimental variable.

### 14. Scheduled supply has an explicit external buffer

Scheduled material that has become available but cannot yet fit into source staging exists **outside the measured system**. FISL models this with an explicit external supply buffer rather than forcing one universal overflow behavior.

The external buffer has a capacity policy:

```text
unbounded      all blocked scheduled supply may wait externally
finite(N)      at most N items may wait externally
zero           no external warehouse/storage exists
```

This unifies several useful scenarios:

- an upstream warehouse with effectively unlimited storage;
- a finite supplier/receiving warehouse;
- no warehouse at all, where blocked arrivals are lost/discarded.

When scheduled supply becomes available, FISL first stages as much as current source-port capacity permits. Remaining quantity is placed into the external supply buffer up to its configured capacity. Any quantity beyond that capacity becomes `source_supply_lost`.

When source staging later gains capacity, externally buffered supply is offered to staging before later scheduled arrivals, using FIFO-by-availability semantics at the aggregate quantity level in v1.

This external buffer is **not system WIP**. It represents upstream inventory outside the declared production-system boundary.

### 15. Zero-capacity external storage models “use it or lose it” supply

A scenario with no upstream warehouse may declare conceptually:

```yaml
external_buffer:
  capacity: 0
```

If scheduled supply arrives while source staging is full, the blocked quantity is immediately recorded as lost/discarded supply.

This is not treated as a protocol violation: it is the declared behavior of the external environment.

Later versions may introduce additional disposition policies such as supplier blocking, rescheduling, perishability, or expiring delivery windows, but v1 needs only external buffering plus overflow loss.

### 16. External supply congestion/loss must be measurable

FISL must expose enough primitive observations to show not merely whether an upstream backlog exists, but **how severe and persistent it is**.

At minimum, source-side observations/state should support deriving:

- `source_external_pending_current` — items currently waiting in the external buffer;
- `source_external_pending_peak` — maximum external pending quantity in the observation window;
- `source_external_pending_item_ticks` — time integral of pending supply, expressed as item-ticks;
- `source_supply_scheduled_total` — cumulative supply made available by schedule;
- `source_release_total` — cumulative quantity successfully staged at the source endpoint;
- `source_withdrawal_total` — cumulative quantity actually taken into the system;
- `source_supply_lost_total` — cumulative quantity discarded because both staging and configured external storage lacked capacity;
- `source_supply_loss_fraction` — lost / scheduled over an explicit measurement window;
- `source_overflow_events` — count of schedule settlements in which loss occurred.

`source_external_pending_item_ticks` is important because current/peak backlog alone does not describe duration. It provides the raw material for later time-weighted backlog metrics analogous to WIP integration.

Learner-facing presentation may call `source_external_pending_*` **upstream backlog** or **external supply backlog**. It must remain visibly distinct from **customer demand backlog**, because these represent congestion on opposite sides of the system.

### 17. Port and external-buffer initial conditions are explicit

At `READY`, FISL validates and establishes declared initial state rather than trusting accidental save-game inventory.

Relevant state includes:

- initial source staging quantity;
- replenishment target when applicable;
- schedule accumulator state;
- external supply buffer capacity;
- initial external pending quantity;
- cumulative lost supply initialized to zero unless explicitly restoring a checkpoint;
- sink tracked inventory, normally zero;
- initial customer demand backlog, normally zero.

These conditions are retained in run provenance.

### 18. Unsupported material is contamination, not valid flow

A v1 port tracks one declared material identity. Other material found in the endpoint is `port_contamination` and must not count as valid input, output, fulfillment, or WIP.

Where endpoint filtering can reliably prevent contamination, standard apparatus should use it. Unexpected contents should be retained for diagnosis rather than silently destroyed unless a later explicit quarantine policy is introduced.

### 19. Port facts are first-class primitive data

The primitive telemetry vocabulary should support facts/state including:

```text
source_withdrawal
source_reverse_flow
source_release
source_external_pending
source_supply_scheduled
source_supply_lost
source_overflow
sink_delivery
demand_created
demand_fulfilled
demand_backlog
surplus_delivery
port_contamination
```

Each record includes appropriate experiment tick/interval, port ID, system ID, material identity, quantity, and measurement/settlement method.

Later throughput, input-rate, service-level, congestion, and supply-loss metrics derive from these observations rather than re-reading arbitrary endpoint state.

### 20. Multiple ports remain distinct unless explicitly aggregated

A system may have multiple source and sink ports, including several carrying the same item. Each emits its own authoritative observation stream.

System-wide totals require explicit aggregation over named ports; FISL never silently merges ports merely because material identities match.

### 21. V1 deliberately does not model every boundary phenomenon

Deferred capabilities include fluids, energy/information exchange, direct inter-system ports, bidirectional ports, train/bot boundary accounting, stochastic schedules, demand expiration/lost sales, order-level demand objects, prices/costs, perishable supply, supplier blocking/rescheduling, and exact gross sub-tick transfer history.

These should extend the established boundary/scheduling model rather than replace it.

## Illustrative v1 schema

A scheduled source with a finite upstream warehouse:

```yaml
ports:
  iron_supply:
    system: factory
    direction: source
    material:
      item: iron-plate

    binding:
      endpoint: iron_supply_port

    supply:
      mode: scheduled
      initial_quantity: 100
      schedule:
        type: constant
        rate: 180/min
      external_buffer:
        capacity: 2000
```

No upstream warehouse / blocked arrivals are lost:

```yaml
supply:
  mode: scheduled
  schedule:
    type: constant
    rate: 180/min
  external_buffer:
    capacity: 0
```

Effectively unlimited external warehouse:

```yaml
external_buffer:
  capacity: unbounded
```

A sink with demand:

```yaml
ports:
  customer_shipments:
    system: factory
    direction: sink
    material:
      item: electronic-circuit

    binding:
      endpoint: customer_port

    demand:
      shortage_policy: backlog
      initial_backlog: 0
      schedule:
        type: constant
        rate: 60/min
```

Exact binding and generic schedule syntax remain subject to the final `fisl/v1` schema pass.

## Consequences

### Positive

- Input/output are explicit auditable boundary transactions rather than geometric guesses.
- Demand is separated from physical output.
- Replenishing and scheduled sources support different Factory Physics teaching goals.
- External buffering is an explicit environmental assumption rather than hidden behavior.
- Zero, finite, and unbounded external storage are represented by one coherent abstraction.
- Supply lost because of inadequate receiving/upstream storage becomes measurable rather than disappearing from the model.
- Time-integrated upstream backlog makes prolonged congestion visible.
- The same interfaces can later support stochastic schedules, costs, and reliability experiments.

### Negative / trade-offs

- Net source settlement cannot reconstruct arbitrary gross same-tick reverse transfers.
- Per-tick settlement is a deliberate accounting granularity.
- External-buffer state adds one more stock outside the measured system that authors and students must conceptually distinguish from WIP.
- FIFO is aggregate rather than order-level in v1.
- Supplier blocking, rescheduling, and perishability remain deferred.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- exact placement of settlement inside the complete per-tick pipeline;
- final telemetry file/event schema;
- WIP treatment of items immediately after source withdrawal;
- exact time-window aggregation syntax for pending item-ticks and loss fractions;
- service-level formulas;
- order-level demand and response time;
- stronger custom one-way endpoint implementations;
- general stochastic schedule syntax;
- non-material and inter-system interfaces.

## Acceptance criteria

The ports/source/demand portion of Issue #1 is complete because we agree that:

1. ports are explicit logical boundary interfaces attached to systems;
2. v1 directions are `source` and `sink`;
3. demand is an optional external process attached to a sink;
4. each v1 port tracks one material identity and one endpoint;
5. port apparatus is FISL-owned experimental equipment excluded from normal internal WIP;
6. authoritative v1 accounting occurs at deterministic per-tick settlements;
7. source input uses documented net withdrawal under a one-way protocol;
8. sink delivery is distinct from demand fulfillment;
9. early surplus output does not satisfy future demand;
10. v1 customer shortage semantics use backlog;
11. schedules compile to exact deterministic discrete release arithmetic;
12. sources support replenishing and scheduled supply;
13. scheduled supply uses an explicit external buffer with zero, finite, or unbounded capacity;
14. blocked supply beyond external-buffer capacity is explicitly recorded as lost rather than silently disappearing;
15. upstream backlog/loss have primitive observations sufficient for current, peak, cumulative, and time-integrated metrics;
16. initial conditions are explicit and reproducible;
17. port observations are primitive data from which later metrics derive;
18. multiple ports remain distinct unless explicitly aggregated.
