# ADR 0005: WIP, Inventory, and Flow-Unit Semantics

- **Status:** Proposed
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

Factory Physics uses Work in Process (WIP), throughput (TH), and cycle time (CT) as related quantities. In Little's Law, WIP must be expressed in a flow unit compatible with throughput and cycle time. It is not enough to count every physical Factorio item inside a rectangle and call the resulting integer "WIP."

This matters especially in Factorio because production transforms unlike items. For example, a factory can simultaneously contain plates, gears, cable, circuits, and finished products. The vector:

```text
iron plate: 10
gear wheel: 5
electronic circuit: 3
```

is a perfectly valid physical inventory observation. The scalar `18`, however, is not automatically a meaningful WIP value. Adding unlike material counts can destroy the dimensional meaning required by Little's Law.

The problem is compounded by Factorio's physical representation:

- items can sit in containers;
- items can travel on belt transport lines;
- inserters can hold items in flight;
- crafting machines have input/output inventories and also work currently committed to an active craft;
- items can be dropped on the ground;
- trains, logistic robots, players, and vehicles can carry mobile inventories;
- FISL source/sink apparatus can physically contain items while remaining outside the measured system by accounting definition.

ADR 0002 established that spatial geometry and accounting membership are distinct. ADR 0003 established explicit material boundary ports. ADR 0004 established canonical point-state sampling and primitive-observation semantics. This ADR defines what FISL may legitimately call WIP on top of those foundations.

## Decision

### 1. Physical inventory and WIP are distinct concepts

FISL distinguishes:

1. **physical inventory observations** — item quantities by material identity and holder/location;
2. **WIP** — work currently admitted to a declared production flow but not yet exited, expressed in an explicit common **flow unit**.

Physical inventory may always be reported as a vector, for example:

```text
iron-plate = 120
fisl-rough-workpiece = 18
fisl-machined-workpiece = 9
fisl-finished-workpiece = 4
```

FISL MUST NOT implicitly sum unlike material quantities and label the result `WIP`.

This distinction is central to the scientific contract.

### 2. A scalar WIP measurement requires an explicit flow-unit basis

Every scalar WIP metric must declare the unit in which work is counted.

Conceptually:

```yaml
wip:
  unit: workpiece
```

The corresponding throughput used with that WIP must be expressed in compatible units per simulation time, and cycle time must describe the time spent by that same unit within the same flow boundary.

FISL MUST reject or clearly classify as non-Little's-Law-compatible any scalar WIP definition whose unit cannot be reconciled with the relevant throughput unit.

### 3. V1 uses explicit conserved work-unit mappings; FISL does not infer WIP equivalence from arbitrary recipes

For a WIP metric spanning more than one item identity, the scenario declares an exact mapping from tracked item identities to a common conserved work unit.

Illustrative form:

```yaml
wip:
  basis:
    type: conserved_work_unit
    unit: workpiece
    materials:
      fisl-rough-workpiece: 1
      fisl-machined-workpiece: 1
      fisl-finished-workpiece: 1
```

The mapping coefficients are exact rational quantities in the resolved scenario, not floating-point guesses.

A single-item WIP measurement is the trivial special case where one tracked item has coefficient `1`.

FISL v1 MUST NOT automatically derive scalar WIP weights from Factorio recipe ingredient counts, raw-material costs, monetary values, stack sizes, or item counts.

Such derived equivalences can be useful for other inventory analyses, but they are not automatically valid counts of jobs/work units.

### 4. Canonical Little's Law teaching scenarios SHOULD use conserved workpieces

The recommended FISL Factory Physics content should provide purpose-built workpiece items/recipes for experiments whose primary purpose is to teach WIP, throughput, and cycle time.

A canonical line might use normal Factorio machinery with recipes such as:

```text
rough-workpiece
      -> machined-workpiece
      -> inspected-workpiece
      -> finished-workpiece
```

where each transformation preserves exactly one logical workpiece.

The physical identities may change so the learner can see stages of processing, while the declared work-unit mapping remains:

```text
1 rough       = 1 workpiece
1 machined    = 1 workpiece
1 inspected   = 1 workpiece
1 finished    = 1 workpiece
```

This is not a replacement for Factorio's production mechanics. The learner still solves the problem using ordinary assemblers, belts, inserters, buffers, circuits, and layout decisions. The custom items/recipes merely provide a scientifically well-defined conserved flow unit.

### 5. Arbitrary Factorio inventory remains measurable even when scalar WIP is not

FISL should remain useful for ordinary Factorio factories.

A scenario may request physical inventory observations for arbitrary materials without defining a scalar WIP basis.

For example, FISL may validly report:

```text
inside system at T:
  iron-plate: 120
  copper-cable: 310
  electronic-circuit: 87
```

while refusing to report:

```text
WIP = 517
```

unless the scenario supplies a scientifically defensible common work-unit basis.

This is an intentional correctness constraint, not a missing feature.

### 6. WIP accounting begins when a work unit crosses an admitted source boundary and ends when it crosses an exit sink boundary

For a system-level WIP flow using ADR 0003 ports:

- work represented in source staging is external and is not WIP;
- after recognized source withdrawal, the admitted work unit is inside the flow and is WIP;
- it remains WIP while waiting, moving, processing, or stored inside the system;
- finished work waiting in an internal finished-goods buffer remains WIP;
- once delivered to the declared sink and settled as `sink_delivery`, it is outside the system and no longer WIP;
- material physically present in FISL source/sink apparatus is excluded according to ADRs 0002 and 0003.

This creates a clean accounting lifetime:

```text
external supply
      |
      | source withdrawal
      v
================ ENTRY =================
      |
      |     W I P   L I F E T I M E
      |
      | wait -> move -> process -> buffer
      |
================ EXIT ==================
      |
      | sink delivery
      v
external/customer environment
```

### 7. WIP is measured as a canonical boundary-state value

A point WIP value at experiment boundary tick `T` describes the prepared system state defined by ADR 0004.

It is a point-state metric derived from declared primitive holder observations at that boundary.

It does not by itself imply a duration.

Average WIP, WIP item-ticks/work-unit-ticks, percentiles, and other time aggregations are deferred to the aggregation/window contract. They will derive from the point WIP series rather than redefining what an instantaneous WIP value means.

### 8. FISL observes WIP through explicit holder adapters

FISL does not ask only "which items are in this zone?" It asks which declared **holders of process work** contain tracked flow units.

A holder adapter is responsible for exposing the portion of a Factorio construct that contributes to WIP without double counting.

V1 should support at least the following holder classes for canonical belt-based Factory Physics labs:

1. stationary internal containers/buffers;
2. crafting-machine process inventories;
3. work committed to an active craft;
4. belt/underground-belt/splitter transport lines;
5. inserter held stacks;
6. dropped item entities inside the system.

FISL-owned boundary apparatus is explicitly excluded.

Mobile inventory classes such as trains, logistic robots, player inventories, and vehicles are addressed separately below.

### 9. Stationary containers count tracked work units when they belong to the system

For an ordinary internal chest/buffer/storage entity whose canonical entity membership belongs to the measured system, tracked work-unit items in its applicable storage inventory count as WIP.

A container's inclusion is an accounting decision derived from the system/observation plan, not merely from physical proximity.

Examples:

- an internal queue chest: included;
- an internal finished-goods buffer before the sink: included;
- a FISL source staging container: excluded;
- a FISL sink staging container: excluded.

### 10. Crafting-machine process inventories count, but non-process compartments do not automatically count

For crafting machines/furnaces and similar supported production entities, FISL distinguishes process-material compartments from unrelated inventories.

Tracked work-unit material in process input/output inventories counts as WIP.

Inventories such as the following are not automatically WIP:

- module inventory;
- fuel inventory;
- burnt-result inventory;
- equipment inventory;
- trash or logistic-control inventory;
- other non-process compartments.

A scenario may measure such resources separately, but merely being stored in a production entity does not make an item part of the declared work flow.

### 11. Work committed to an active craft MUST remain represented as WIP

Counting visible machine inventories alone is insufficient.

Factorio crafting machines expose whether a craft is currently in process (`is_crafting`) and expose crafting progress. During an active craft, some portion of the logical work may no longer be represented as a freely visible input stack and the output does not yet exist as finished inventory.

FISL therefore defines an **in-process occupancy** holder for supported crafting machines.

For a declared conserved-work-unit recipe, the adapter accounts for the work units committed to the currently active craft exactly once.

For example, if a supported recipe transforms:

```text
1 machined-workpiece -> 1 inspected-workpiece
```

then an assembler with one active craft contains:

```text
in_process_wip = 1 workpiece
```

for as long as that craft is active, regardless of where Factorio internally stores or reserves the consumed ingredient.

The concrete adapter MUST be tested against the supported Factorio runtime version so that visible input inventory plus in-process occupancy never double-counts the same work.

This implementation test is mandatory because WIP continuity through processing is part of the scientific contract.

### 12. V1 conserved-work-unit recipes must have deterministic, conservation-compatible transformations

For a metric declared `conserved_work_unit`, each production transformation participating in the measured flow must preserve the declared work-unit quantity.

Conceptually, for each counted transformation:

```text
tracked work units consumed = tracked work units produced
```

Auxiliary untracked inputs such as energy/fuel/catalysts may exist; they do not alter the work-unit count unless explicitly part of the declared basis.

The resolved scenario/compiler SHOULD validate known recipe transformations where feasible.

Canonical v1 Little's Law scenarios SHOULD avoid:

- productivity effects that create additional counted work units;
- probabilistic counted outputs;
- counted byproducts that make flow-unit ownership ambiguous;
- quality transformations that change the declared work-unit accounting unless explicitly mapped;
- recipe switching that cannot preserve the declared work-unit basis.

Speed/energy-efficiency changes are compatible when they alter processing time/cost without changing counted yield.

### 13. Belt WIP is counted from unique transport lines, not by summing every belt entity

Factorio exposes belt contents through `LuaTransportLine`. A transport line may span multiple belt entities, and different owners can refer to the same underlying internal line.

Therefore FISL MUST NOT simply iterate every belt entity and sum `get_contents()` results; that can double count.

The belt holder adapter must identify/deduplicate underlying transport lines (for example using the runtime's line-equality semantics) and count each physical line exactly once.

For v1 system-level WIP, canonical scenarios SHOULD keep measured belt networks fully within the primary system zone. If a transport line crosses the spatial/accounting boundary in a way that makes partial-line ownership ambiguous, the scenario must either:

- use a stronger position-aware observation method;
- split the line at explicit boundary apparatus;
- or fail WIP coverage validation.

Raw geometric belt crossing is still not an authoritative system transaction; source/sink ports remain the entry/exit accounting mechanism.

### 14. Inserter-held tracked work counts as WIP for internal inserters

An inserter exposes its currently held stack and the position of its hand.

For a supported internal inserter, a tracked work-unit stack in the hand counts as WIP.

This avoids a temporary accounting hole while a workpiece is moving between a belt, machine, or buffer.

The accounting owner is the declared internal inserter/transfer apparatus, not a fractional geometric test of the hand position at each instant.

This is especially important at ports:

- once a source withdrawal has been recognized and the work is in an internal transfer device, it is WIP;
- a workpiece being moved toward the sink remains WIP until the sink settlement recognizes delivery.

Standard scenarios SHOULD place boundary-transfer inserters so their accounting role is unambiguous and consistent with ADR 0002 boundary-integrity rules.

### 15. Dropped tracked work inside the system still counts as WIP and is separately flagged

A tracked workpiece dropped as an item entity inside the primary system zone has not automatically left the system.

V1 SHOULD count such a workpiece as WIP while simultaneously emitting a diagnostic/protocol condition such as:

```text
uncontained_wip
```

This prevents learners from artificially reducing measured WIP merely by dropping work on the ground while preserving the distinction between normal production flow and abnormal material handling.

A future scrap/loss interface may explicitly remove discarded work from the system; simply dropping it does not.

### 16. Player-carried work is not supported as normal v1 WIP transport

Canonical v1 measured runs SHOULD treat manual carriage of tracked work units in player inventories as a protocol violation.

Player inventory is not part of the normal counted WIP holder set.

This prevents the scientific boundary from becoming dependent on whether a learner happens to stand inside or outside a rectangle while carrying workpieces.

If tracked work enters a player inventory during a measured phase, FISL should preserve diagnostic evidence and flag WIP coverage/validity rather than silently treating the items as zero WIP.

Learners remain free to build, remove, and redesign production equipment according to the scenario; the restriction concerns manually carrying the production work units whose flow is being measured.

### 17. Trains, logistic robots, and arbitrary vehicle/mobile inventories are deferred for authoritative v1 WIP

FISL's architecture should eventually support mobile material holders, but v1 Factory Physics WIP should not make weak claims about them.

Canonical WIP scenarios therefore SHOULD avoid using the following to transport tracked work units during measured phases:

- trains/cargo wagons;
- logistic robots;
- cars/tanks/spider vehicles;
- other mobile inventory-bearing entities.

If a scenario requires these transport modes, it needs a specific holder adapter and accounting policy before its WIP can be considered authoritative.

For example, Factorio exposes train inventory contents, and logistic-network APIs expose useful aggregate state, but system-boundary membership and in-flight robot cargo require additional semantics that are intentionally outside v1's canonical WIP path.

FISL MUST prefer "unsupported / incomplete WIP coverage" over silently ignoring mobile inventory.

### 18. Tracked work-unit scope is explicit; auxiliary material is not automatically WIP

A production line may consume coal, lubricant, repair materials, catalysts, or other resources.

Those are not automatically part of the WIP scalar simply because they are physically inside the factory.

The WIP basis declares which material identities represent the flow units being counted.

Other materials can be reported through physical inventory/resource metrics.

This ensures that a workpiece WIP metric retains a stable dimensional meaning even when the factory consumes auxiliary resources.

### 19. Item quality is part of material identity when applicable, but canonical v1 WIP SHOULD use normal quality

Where the active Factorio runtime supports item quality, material identity may include quality.

A conserved-work-unit mapping could theoretically assign multiple qualities to the same work-unit family.

However, canonical v1 Factory Physics WIP scenarios SHOULD use normal-quality tracked workpieces and avoid quality-changing production until the measurement contract for quality/yield is explicitly developed.

This keeps the first Little's Law labs focused on flow rather than yield semantics.

### 20. WIP holder samples are primitive observations; scalar WIP is a derived point metric

The observation layer should preserve auditable material-holder facts such as:

```text
holder_material_count
in_process_work_units
inserter_held_count
ground_work_unit_count
```

with subject, material identity, count, method, and boundary tick.

The scalar WIP value is then derived deterministically from those primitive facts and the declared work-unit mapping.

Conceptually:

```text
primitive holder observations
          |
          v
work-unit normalization
          |
          v
WIP(T)
```

This allows later changes to metric definitions or holder classifications to be audited against retained primitive data.

### 21. The observation plan must declare WIP coverage explicitly

A compiled WIP metric produces a holder/coverage plan before the run starts.

The plan identifies at least:

- system/zone being measured;
- work-unit basis/material mapping;
- supported holder adapters;
- participating production entities/transport lines/inserters;
- excluded FISL apparatus;
- prohibited/unsupported carrier classes;
- recipe transformations whose work-unit conservation is assumed/validated.

If the runtime enters a state outside the coverage plan, FISL records a coverage/validity condition rather than quietly continuing with a deceptively precise WIP number.

### 22. A conserved work-unit flow enables an accounting-balance integrity check

For a system with conserved work units and no declared scrap/loss exit, the following accounting relationship should hold across checkpoints:

```text
initial_wip
+ cumulative_admitted_work
- cumulative_exited_work
= current_wip
```

More generally, once explicit losses/scrap exits exist:

```text
initial_wip
+ admitted
- exited
- declared_losses
= current_wip
```

FISL SHOULD calculate a diagnostic `wip_balance_error` from these quantities.

A nonzero balance error can reveal:

- unobserved/manual material movement;
- missing holder coverage;
- accidental double counting;
- recipe non-conservation;
- loss/destruction not represented by a declared boundary process;
- adapter defects.

The balance check is an integrity diagnostic, not itself the definition of WIP.

### 23. Unmodeled destruction/scrap is a validity problem in v1, not silent disappearance

Canonical v1 conserved-WIP scenarios do not include arbitrary scrap/yield loss.

If tracked work units are destroyed, consumed by an undeclared recipe, manually removed, or otherwise disappear without a declared exit/loss mechanism, FISL SHOULD flag a conservation/coverage violation.

A future Course II extension can add explicit scrap/loss interfaces and yield processes. The v1 architecture leaves room for that by treating losses as additional accounting exits rather than redefining WIP.

### 24. Little's Law compatibility requires matching WIP, throughput, and boundary scope

A WIP value is not Little's-Law-compatible merely because it is expressed as a scalar.

For a later Little's Law calculation:

- WIP must count the declared flow unit;
- throughput must count exits of the same flow unit;
- cycle time must describe time spent by that same flow unit;
- all three must use the same accounting entry/exit boundary;
- the averaging/window conditions required by the later metric contract must also be satisfied.

FISL SHOULD encode this compatibility information in metric metadata so the UI cannot casually divide unrelated measurements.

### 25. Subsystem inventory is allowed without claiming whole-flow WIP semantics

A scenario may define inventory/WIP-like measurements for a subregion or stage, for example a queue before one machine.

Those can be useful for bottleneck and buffer analysis.

However, unless that subsystem also has compatible declared entry/exit semantics and a conserved flow unit, FISL should describe the result as stage inventory/queue inventory rather than automatically claiming it is eligible for whole-system Little's Law calculations.

This keeps local diagnostic measurements useful without weakening the system-level scientific contract.

## Proposed v1 schema shape

Illustrative only:

```yaml
metrics:
  line_wip:
    type: wip
    system: factory

    basis:
      type: conserved_work_unit
      unit: workpiece
      materials:
        fisl-rough-workpiece: 1
        fisl-machined-workpiece: 1
        fisl-inspected-workpiece: 1
        fisl-finished-workpiece: 1

    coverage:
      holders:
        - stationary_process_inventory
        - active_craft
        - transport_line
        - inserter_hand
        - ground_item

      unsupported_carriers:
        policy: protocol_violation
        types:
          - player_inventory
          - train
          - logistic_robot
          - vehicle

    compatibility:
      little_law: required
```

A physical-inventory-only observation might instead be declared separately and would not need a WIP basis:

```yaml
metrics:
  raw_inventory:
    type: material_inventory
    system: factory
    materials:
      - iron-plate
      - copper-cable
      - electronic-circuit
```

The final syntax is deferred until the `fisl/v1` schema pass.

## Implementation notes

Current Factorio runtime APIs provide useful primitives for this design:

- `LuaTransportLine::get_contents()` exposes item counts on a transport line;
- transport lines have equality semantics because the same underlying line can span multiple owners, which is why belt observation must deduplicate lines;
- `LuaEntity::held_stack` and `held_stack_position` expose inserter-held material;
- crafting machines expose `is_crafting()` and `crafting_progress`;
- train APIs expose train inventory contents, demonstrating that future mobile-holder adapters are technically possible even though their accounting semantics are deferred.

The WIP adapter test suite should include conservation fixtures in which known work units are placed successively in every supported holder state and the measured WIP remains constant while the work moves/changes stage.

A particularly important regression test is:

```text
source -> inserter -> belt -> inserter -> machine input
       -> active craft -> machine output -> inserter -> buffer
       -> inserter -> sink
```

For one admitted conserved workpiece, system WIP should remain exactly one at every canonical checkpoint after admission and before sink delivery, independent of which supported holder currently represents it.

## Consequences

### Positive

- WIP retains the dimensional meaning required by Factory Physics rather than becoming a sum of arbitrary game items.
- Physical inventory remains fully useful even when a scalar WIP value is unjustified.
- Canonical Little's Law labs can be made rigorous with conserved workpiece families while still using normal Factorio machinery.
- Items do not disappear from WIP simply because they are on a belt, in an inserter hand, or actively being processed.
- FISL can detect measurement holes through work-unit conservation checks.
- The holder-adapter architecture provides a clean extension path for trains, bots, scrap, quality, and more complex flows.
- Port semantics, spatial-system semantics, and WIP accounting now reinforce rather than contradict one another.

### Negative / trade-offs

- Canonical Little's Law scenarios need purpose-designed workpiece recipes or another explicit conserved work-unit mapping.
- Arbitrary vanilla Factorio production graphs cannot automatically receive a trustworthy scalar WIP number.
- Belt and active-craft adapters require careful implementation/testing to avoid double counts and temporary disappearance.
- Canonical v1 WIP scenarios must constrain manual item carriage, logistics bots, trains, and other unsupported mobile carriers during measured phases.
- Productivity/yield-changing mechanics require additional accounting before they can participate in conserved-work-unit WIP.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- exact time aggregation of point WIP into average WIP/item-ticks;
- throughput formulas/windows;
- cycle-time measurement beyond compatibility requirements;
- general-purpose `entity_set` schema;
- exact Lua inventory indices/adapters per Factorio entity prototype;
- optimized belt observation algorithms;
- train/mobile-holder accounting;
- logistic-robot in-flight cargo accounting;
- explicit scrap/rework/yield-loss processes;
- arbitrary assembly-tree job reconstruction;
- quality/productivity WIP semantics;
- UI presentation of material inventory versus work-unit WIP.

## Acceptance criteria for this decision

The WIP portion of Issue #1 is complete when we agree that:

1. physical inventory and WIP are distinct concepts;
2. scalar WIP requires an explicit common flow-unit basis compatible with throughput/cycle time;
3. FISL does not infer scalar WIP by summing arbitrary unlike Factorio item counts;
4. v1 supports explicit conserved-work-unit mappings, with single-item WIP as a trivial case;
5. canonical Little's Law labs should use purpose-built conserved workpiece families where appropriate;
6. system WIP begins after source admission and ends at sink delivery;
7. canonical WIP sampling uses ADR 0004's prepared boundary-state convention;
8. supported v1 holders include internal containers, process inventories, active crafts, unique belt transport lines, internal inserter hands, and ground work items;
9. FISL port staging is excluded from WIP;
10. active crafts preserve in-process WIP continuity rather than allowing work to disappear between input and output;
11. belts are deduplicated by underlying transport-line identity/semantics rather than summed per entity;
12. manual player carriage and unsupported mobile carriers produce coverage/protocol problems rather than silent undercounting;
13. productivity/yield-changing transformations are excluded from canonical conserved-WIP labs until explicitly modeled;
14. primitive holder observations remain auditable inputs to the derived WIP point metric;
15. conserved flows support a WIP balance-integrity diagnostic;
16. Little's Law compatibility requires matching work units and matching system boundaries across WIP, throughput, and cycle time.

## References

- Mark L. Spearman, "Little's Law in Production Systems with Yield Loss," Project Production Institute, 2019.
- Factorio Runtime API: `LuaTransportLine`, `LuaEntity`, and `LuaTrain` runtime documentation.
