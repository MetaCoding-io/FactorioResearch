# ADR 0003: Material Ports, Supply, Demand, and Boundary Transactions

- **Status:** Proposed
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

ADR 0002 established that geometric zone crossing is **not** the authoritative definition of material entering or leaving a FISL system. FISL therefore needs explicit boundary interfaces whose behavior is reproducible, measurable, and understandable to learners.

For the first Factory Physics labs, these interfaces need to support at least:

- effectively unconstrained raw-material supply;
- rate-limited raw-material supply;
- finished-goods output collection;
- customer demand and backlog;
- authoritative input/output event streams for later throughput and service metrics.

The design must remain compatible with later stochastic supply/demand, failures, costs, multi-system experiments, and other boundary-interface types without making v1 implement all of them.

A major implementation constraint is that Factorio exposes inventory contents and script insertion/removal, but normal machine/inserter activity is not represented as a universal per-item inventory-transfer event stream. FISL must therefore define exactly what it can observe and avoid claiming gross transaction precision that the runtime apparatus does not actually provide.

## Decision

### 1. A material `port` is an explicit system-boundary interface

A FISL material port is a logical interface between one declared system and its external environment.

A port answers:

> At what declared interface do items enter or leave the system, and how does FISL account for that exchange?

A port is not merely a chest, coordinate, or zone edge. A physical Factorio entity is an implementation endpoint to which the logical port is bound.

Every v1 material port references exactly one FISL system.

V1 does not require direct system-to-system ports. Such a feature should later be expressible as an interface connecting two systems rather than redefining the meaning of a port.

### 2. V1 has two material-port directions: `source` and `sink`

V1 material ports have one of two semantic directions:

- `source` — material is made available by the external environment and may enter the system;
- `sink` — material leaves the system and is accepted by the external environment.

A source is therefore an **input boundary**.

A sink is therefore an **output boundary**.

Ports are one-way in v1. Bidirectional material interfaces are deferred.

### 3. Demand is not a port type

`demand` is an exogenous process that may be attached to a sink.

This distinction is fundamental:

```text
source / sink = boundary direction

demand        = external requirement over time
```

A sink may exist without demand. This is useful for labs that measure output throughput without modeling a customer.

The same sink can later be configured with demand to study fulfillment, backlog, service level, push/pull behavior, and response to changing requirements.

This prevents physical boundary semantics from being coupled unnecessarily to one particular business interpretation.

### 4. V1 ports track one material identity each

Each v1 port tracks exactly one item identity.

Illustrative form:

```yaml
ports:
  iron_supply:
    system: factory
    direction: source
    material:
      item: iron-plate

  customer_shipments:
    system: factory
    direction: sink
    material:
      item: electronic-circuit
```

The resolved material identity SHOULD be capable of including item quality where the active Factorio configuration supports it. Base-game Factory Physics scenarios should default to normal-quality items and should not require expansion mechanics.

Multi-item ports, fluids, heat, energy, information, and other interface types are deferred.

### 5. Logical port semantics are separate from physical endpoint implementation

Each v1 logical port binds to exactly one physical Factorio endpoint that exposes an inventory FISL can inspect and manipulate.

The scientific contract MUST NOT depend on whether that endpoint is ultimately implemented as:

- a FISL-specific custom entity;
- a protected native container;
- another inventory-bearing apparatus that satisfies the same contract.

The standard FISL distribution SHOULD provide purpose-built, visually distinctive FISL port apparatus because ports are part of the experimental bench rather than part of the student's factory.

At `READY`, a port binding must resolve unambiguously and FISL records at least:

- logical port ID;
- system ID;
- direction;
- material identity;
- surface;
- endpoint prototype;
- endpoint position;
- stable runtime entity identifier when available;
- effective usable inventory capacity;
- measurement method.

An unresolved or ambiguous binding is a validation failure.

If the endpoint becomes unavailable during an active run, the run data are preserved but the experiment must be marked as having lost an authoritative measurement interface. The recommended v1 behavior is to abort the run rather than continue producing apparently valid boundary metrics.

### 6. Standard port apparatus is controlled experimental equipment

The standard v1 endpoint SHOULD be protected from ordinary learner manipulation as far as Factorio permits without interfering with intended automated item transfer.

Where appropriate FISL SHOULD make the endpoint:

- non-minable;
- non-destructible;
- non-rotatable if relevant;
- non-operable through the normal player GUI/quick-transfer interface.

Factorio's runtime API supports script insertion/removal and inventory inspection, and exposes flags such as `operable`, `destructible`, and `minable_flag` on applicable entities.

The purpose is not to prevent all adversarial behavior. It is to keep the experimental interface stable during normal classroom play.

### 7. Port apparatus is external to normal system WIP accounting

A source staging inventory represents material that is still external to the measured production system.

A sink staging inventory represents boundary apparatus through which output is being accepted by the external environment.

Therefore FISL-owned port inventories are excluded from ordinary internal WIP accounting unless a future scenario explicitly models a boundary buffer as part of the system.

This preserves ADR 0002's separation between physical placement and accounting membership.

### 8. V1 ports use deterministic per-tick settlement

Each active port participates in one FISL-controlled **settlement** per executed simulation tick.

A settlement is the authoritative accounting point at which FISL reconciles changes in the endpoint inventory since the previous settlement and performs its own source/sink actions.

The port contract therefore measures boundary exchange in discrete simulation-tick intervals rather than pretending to observe the exact sub-tick instant at which an inserter moved an item.

Each settlement must be timestamped in the authoritative FISL experiment clock.

The exact placement of the settlement callback within FISL's complete per-tick observation pipeline will be fixed by the primitive-observation ADR. This ADR fixes the accounting semantics independently of that implementation detail.

### 9. Source input is measured by net withdrawal from external staging

After FISL has completed settlement for a source, it retains the resulting tracked-item count as the source's previous post-settlement state.

At the next settlement it observes the source inventory before applying any new FISL replenishment/release action.

For a compliant one-way source:

```text
input_quantity = previous_post_settlement_count
                 - current_pre_settlement_count
```

when that value is positive.

This quantity is the authoritative v1 boundary input for the interval just completed.

Conceptually:

```text
external source staging
       |
       | withdrawal by student's system
       v
================ SYSTEM BOUNDARY ================
       |
       v
 internal production system
```

Items sitting in source staging are external. Quantity recognized as withdrawn at settlement has crossed the declared input boundary.

### 10. V1 source measurement is explicitly net, not guaranteed gross flow

A normal Factorio inventory does not expose a universal gross history of every inserter transfer into and out of it.

Therefore v1 source-port measurement MUST identify its method as a net-inventory settlement method rather than claiming exact gross transaction tracking.

If material is both withdrawn from and returned to the same source endpoint between two settlements, only the resulting net change may be directly observable through this method.

Accordingly:

- reverse flow into a source is prohibited by the v1 port protocol;
- standard scenarios and apparatus SHOULD make reverse flow difficult during normal play;
- any detectable reverse flow is a protocol violation;
- v1 scientific claims assume protocol-compliant one-way source use.

A future one-way instrumented endpoint may provide stronger gross-transfer observability without changing the logical meaning of a source port.

### 11. Sink output is settled, recorded, then removed from staging

At each sink settlement FISL reads the count of the sink's tracked material.

The tracked quantity present at settlement is recorded as a `sink_delivery` for the interval just completed and is then removed from the endpoint by FISL.

Thus the normal post-settlement tracked-item count of a sink is zero.

Conceptually:

```text
 internal production system
       |
       | delivery
       v
================ SYSTEM BOUNDARY ================
       |
       v
 FISL sink staging -> settled/removed -> external environment
```

The settlement event is the authoritative v1 accounting point at which the delivered quantity becomes recorded system output.

### 12. Sink delivery and demand fulfillment are different observations

Every valid tracked item accepted at a sink is a system output delivery, regardless of whether there is customer demand waiting for it.

Therefore FISL distinguishes at least:

- `sink_delivery` — physical/accounting output across the declared boundary;
- `demand_fulfillment` — the portion of that delivery that satisfies existing demand;
- `surplus_delivery` — output delivered when there was not enough existing demand to consume it.

This prevents throughput from being confused with customer service.

It also allows a learner to overproduce and observe that:

```text
high output != high demand fulfillment efficiency
```

### 13. Deliveries do not retroactively satisfy future demand

If a sink receives material when no demand is currently outstanding, that quantity is recorded as surplus delivery.

It does not become a credit that automatically fulfills demand generated later.

If an experiment needs finished-goods inventory that can satisfy future demand, that inventory should be modeled explicitly as part of the system or as a distinct downstream buffer rather than hidden inside demand accounting.

This keeps the system boundary and inventory model intellectually honest.

### 14. V1 demand uses a backlog ledger

A sink may declare an attached demand process.

V1 demand creates discrete item requirements over simulation time and uses **backlog** as the supported shortage policy.

At any point the demand ledger includes at least cumulative values for:

- demand created;
- demand fulfilled;
- current backlog;
- surplus delivery.

For a delivery quantity `D` and backlog `B` already outstanding when that delivery is settled:

```text
fulfilled = min(D, B)
surplus   = D - fulfilled
backlog   = B - fulfilled
```

Demand generated for a future simulation interval cannot be fulfilled by surplus output from an earlier interval.

Lost-sales/expiry semantics are intentionally deferred because they require an additional definition of due-time tolerance and demand expiration.

### 15. Demand and supply schedules use simulation time and exact discrete accumulation

Constant rates such as:

```yaml
rate: 180/min
```

are authoring conveniences.

The resolved scenario MUST represent them using exact simulation-time arithmetic that determines a discrete cumulative item entitlement without floating-point drift.

For example, a constant rate may be compiled to an integer/rational accumulator such that the cumulative number of items released after `N` ticks is deterministic.

FISL MUST NOT repeatedly add an inexact floating-point `items_per_tick` value and hope that rounding errors remain insignificant.

The same scheduling abstraction should later support stochastic policies while preserving the source/sink interface.

### 16. Source release and demand creation are prepared for the upcoming simulation interval

FISL's causal model is:

1. a tick interval runs using source availability and demand state already established at its beginning;
2. at the next settlement, FISL accounts for source withdrawals and sink deliveries that occurred during that interval;
3. sink deliveries are allocated to demand that was already outstanding during that interval;
4. FISL then advances source-supply and demand schedules to establish state for the next interval.

The first experiment interval is initialized before `experiment_tick = 0` begins.

This rule prevents output produced before a demand exists from satisfying that future demand merely because of callback ordering.

The primitive-observation ADR will define the exact implementation ordering and event timestamps consistent with this causal contract.

### 17. V1 supports two source-supply modes

Factory Physics labs need both an external source that is intentionally *not* the bottleneck and an external source whose availability rate is part of the experiment.

V1 therefore SHOULD support:

#### `replenish`

Maintain a declared staging target after each settlement.

Illustrative form:

```yaml
supply:
  mode: replenish
  target: 400
```

After settling student withdrawals, FISL inserts enough tracked material to restore staging toward the target, subject to actual endpoint capacity.

This is the preferred source mode when the pedagogical model intends raw-material availability to be effectively unconstrained.

It is not literally infinite: extraction is still limited by the physical Factorio endpoint and the student's material-handling design.

#### `scheduled`

Release material according to an explicit simulation-time schedule.

Illustrative form:

```yaml
supply:
  mode: scheduled
  schedule:
    type: constant
    rate: 180/min
```

Scheduled mode is used when upstream availability itself is part of the experiment.

### 18. Scheduled source supply accumulates externally when staging is full

For v1 scheduled supply, the supported overflow policy is **external backlog**.

If the schedule says more material has become available than can currently fit into the port staging inventory, FISL records that quantity as pending outside the system and attempts to stage it later when capacity becomes available.

This means a full receiving interface delays external delivery rather than silently destroying scheduled supply.

Future scenarios may add lost supply, perishable supply, delivery windows, or other policies.

### 19. Initial port conditions are explicit

A scenario must not rely on an accidental quantity already present in a saved chest.

At `READY`, FISL validates and establishes the declared initial state for every port.

Relevant initial conditions include, as appropriate:

- initial source staging quantity;
- replenishment target;
- scheduled-supply accumulator state;
- external pending supply, normally zero;
- sink tracked inventory, normally zero;
- initial demand backlog, normally zero.

The resolved run manifest records these initial conditions.

### 20. Unsupported material in a port is contamination, not output/input

A v1 port tracks one declared material identity.

Any other material found in the endpoint is a `port_contamination` condition.

Unsupported material MUST NOT be counted as valid input, output, fulfillment, or WIP merely because it is physically in FISL apparatus.

Where Factorio endpoint filtering can reliably prevent contamination, the standard apparatus SHOULD use it.

If contamination is detected, FISL records a protocol/validity event. V1 SHOULD NOT silently destroy unsupported material merely to make the experiment appear clean; the default should preserve the unexpected state for diagnosis unless a later explicit quarantine policy is added.

### 21. Port flow observations are first-class primitive data

The eventual telemetry vocabulary should be able to preserve primitive port facts such as:

```text
source_withdrawal
source_reverse_flow
source_release
source_external_pending
sink_delivery
demand_created
demand_fulfilled
demand_backlog
surplus_delivery
port_contamination
```

Each such record should include at least:

- experiment tick / settlement interval;
- port ID;
- system ID;
- material identity;
- quantity;
- measurement/settlement method where relevant.

Later metrics such as throughput, input rate, fulfillment rate, and service level should derive from these observations instead of reaching back into arbitrary endpoint inventory state.

### 22. Multiple ports are explicit, not implicitly merged

A system may have multiple source and sink ports, including multiple ports carrying the same item.

Each port produces its own authoritative observation stream.

System-wide totals must be constructed by an explicit later aggregation over named ports; FISL MUST NOT silently combine ports merely because their item identities match.

This leaves room for experiments involving multiple suppliers, alternate routes, parallel customers, or decentralized subsystems.

### 23. V1 material ports deliberately do not model every boundary phenomenon

V1 does not require:

- fluids;
- energy exchange;
- circuit/information exchange;
- train-consist boundary accounting;
- logistic-bot boundary accounting;
- inter-system transfer ports;
- bidirectional ports;
- demand expiration/lost sales;
- stochastic schedules;
- order-level demand objects;
- costs or prices;
- exact gross sub-tick transfer histories.

These are extensions of the boundary-interface and scheduling model, not reasons to complicate the first Factory Physics implementation.

## Proposed v1 schema shape

Illustrative only:

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
      overflow_policy: external_backlog

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

An unconstrained teaching source might instead declare:

```yaml
ports:
  iron_supply:
    system: factory
    direction: source
    material:
      item: iron-plate
    supply:
      mode: replenish
      target: 400
```

The exact binding syntax and general schedule syntax remain subject to the eventual `fisl/v1` schema pass.

## Implementation notes

Factorio's runtime inventory APIs provide the core primitives needed for this design: inventory/entity item counts can be read, items can be inserted or removed by script, and entity interaction flags can protect apparatus from common player manipulation.

However, the runtime event model does not provide a single universal event representing every arbitrary inserter transfer into or out of a container inventory. That is why v1 explicitly defines source flow using deterministic net inventory settlement and requires one-way protocol use rather than claiming unavailable gross-flow observability.

The standard endpoint implementation should be chosen to make one-way use as natural and robust as possible. A future custom apparatus may improve gross-flow observability without altering the scenario-level port semantics.

## Consequences

### Positive

- Input/output become explicit auditable boundary transactions rather than geometric guesses.
- Demand is cleanly separated from physical output, which supports both pure throughput labs and customer-service labs.
- The same port model extends naturally to stochastic schedules later.
- Replenishing sources allow Factorio's own material-handling machinery to remain the learner's problem while removing unintended upstream scarcity.
- Rate-limited sources allow upstream availability to become an intentional experimental variable.
- Surplus output remains visible rather than being falsely credited against future demand.
- Port observation streams give later throughput/service metrics a strong primitive-data foundation.
- Binding semantics remain independent of the exact endpoint prototype.

### Negative / trade-offs

- Net source settlement cannot reconstruct arbitrary gross same-tick reverse transfers.
- Standard apparatus and scenario layout must reinforce one-way use.
- Per-tick settlement introduces at most sub-tick physical/accounting timing granularity rather than claiming an exact inserter-movement instant.
- Sink acceptance of surplus output means experiments that require a hard customer acceptance limit will need an additional future policy or an explicit downstream buffer.
- Lost-sales demand is deferred in favor of a simpler backlog model.
- Inventory-bound endpoints remain a deliberate experimental abstraction rather than a universal model of every industrial interface.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- exact position of port settlement inside the complete FISL per-tick callback/order;
- exact telemetry file/event schema;
- WIP treatment of inserter-held items immediately after source withdrawal;
- exact throughput metric window/aggregation syntax;
- service-level formulas;
- order-level demand objects and response time;
- whether sink surplus delivery should later support configurable rejection/holding policies;
- a stronger custom one-way endpoint implementation;
- exact authoring/binding UI;
- general stochastic schedule syntax;
- multi-system and non-material interfaces.

## Acceptance criteria for this decision

The ports/source/demand portion of Issue #1 is complete when we agree that:

1. ports are explicit logical boundary interfaces attached to systems;
2. v1 material port directions are `source` and `sink`;
3. demand is an optional external process attached to a sink, not a third port direction;
4. each v1 port tracks one material identity and one physical endpoint;
5. standard port apparatus is FISL-owned controlled experimental equipment and is excluded from normal internal WIP;
6. authoritative v1 port accounting occurs at deterministic per-tick settlements;
7. source input uses an explicitly documented net-withdrawal measurement under a one-way protocol;
8. sink delivery is recorded and settled independently from demand fulfillment;
9. output delivered before demand is surplus and does not retroactively fulfill future demand;
10. v1 demand uses backlog rather than lost-sales expiration;
11. constant schedules compile to deterministic exact discrete release arithmetic;
12. v1 sources support both replenishing and scheduled supply;
13. scheduled supply that cannot fit stages as external pending supply rather than disappearing;
14. initial conditions are explicit and reproducible;
15. port observations become primitive data from which later metrics are derived;
16. multiple ports remain separate unless a metric explicitly aggregates them.
