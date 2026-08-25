# ADR 0017: Conservation-Ledger WIP and Physical Census Semantics

- **Status:** Accepted
- **Runtime validation:** Pending; see `../RUNTIME_VALIDATION.md`, especially RV-002 through RV-005
- **Scope:** FISL v1 conserved-work-unit flows
- **Supersedes in part:** ADR 0005 §§7–8, 11, 13–17, 20–23 where those sections made physical holder census the authoritative source of total conserved-flow WIP

## Context

ADR 0005 made two foundational decisions that remain correct:

1. scalar WIP requires an explicit common flow-unit basis; and
2. canonical Little's Law labs should use a conserved workpiece family whose transformations preserve one logical work unit.

ADR 0005 also defined the lifetime of that work unit by accounting boundaries:

```text
source admission -> internal WIP -> completion/loss exit
```

Its initial implementation model then attempted to derive total WIP at each boundary by physically enumerating every holder that might currently represent the work:

- containers;
- crafting-machine inventories;
- active crafts;
- belt transport lines;
- inserter hands;
- ground items;
- eventually mobile/player inventories.

That census model creates two avoidable problems.

First, exact tick-resolution total WIP would require expensive and version-sensitive observation of physical holders at very high cadence, especially belts where ordinary movement has no item-transfer event stream.

Second, a holder-census definition makes ordinary learner redesign brittle. Mining loaded equipment may temporarily place tracked work in player inventory even though the work has not crossed the declared production-system boundary.

For a genuinely conserved flow, however, total WIP is already determined by its accounting lifetime. Physical location is needed to answer **where the WIP is** and to validate the accounting, but not to define **how much WIP exists**.

This ADR inverts those epistemic roles.

## Decision

### 1. For a validated conserved work-unit flow, the conservation ledger is authoritative for total system WIP

For a canonical flow with conserved work units, total WIP at canonical boundary `T` is the ledger state:

```text
WIP(T)
  = initial_WIP
  + cumulative_admitted_work_through_T
  - cumulative_completed_work_through_T
  - cumulative_declared_losses_through_T
```

Equivalently, across one completed interval `[T-1,T)`:

```text
WIP(T)
  = WIP(T-1)
  + admissions[T-1,T)
  - completions[T-1,T)
  - declared_losses[T-1,T)
```

The quantities are exact work-unit quantities under the flow's declared rational mapping.

The ledger point state at boundary `T` represents the prepared state for `[T,T+1)` under ADR 0004/0010.

### 2. Boundary transactions define admission and completion

For canonical material flows:

- source `source_withdrawal` normalized into flow units is the admission transaction;
- completion-port `sink_delivery` normalized into flow units is the completion transaction;
- a future explicit scrap/loss interface may contribute a declared loss transaction.

Internal movement between belts, machines, inserters, chests, player inventory, or ground does not alter total WIP because no declared flow boundary was crossed.

This follows ADR 0005's already-accepted WIP lifetime directly.

### 3. The ledger method is available only to flows whose conservation assumptions are validated

`conservation_ledger` total WIP requires all of the following:

- an explicit conserved work-unit basis;
- validated deterministic transformations for counted work units;
- no productivity/yield behavior that creates counted work implicitly;
- no undeclared scrap/destruction/removal intended as normal scenario behavior;
- explicit admission and completion boundaries;
- supported authoritative boundary-transaction methods;
- a known initial WIP state.

If these assumptions do not hold, FISL MUST NOT silently apply the ledger formula as authoritative WIP.

Arbitrary Factorio factories may still expose physical inventory vectors and other measurements without receiving canonical conserved-flow WIP.

### 4. Initial WIP is established and validated at READY

Before a conserved-flow run enters `READY`, FISL performs a physical census sufficient to establish initial internal tracked work.

Canonical course baselines SHOULD normally start with:

```text
initial_WIP = 0
```

because this is easiest to reason about and validate.

A nonzero initial WIP is permitted only when the scenario explicitly expects it and READY-time census can establish its quantity unambiguously.

Source staging remains external and is not part of initial system WIP.

The established `initial_WIP` becomes immutable ledger provenance for the run.

### 5. Total WIP no longer depends on knowing the physical holder every tick

Once a work unit is admitted, it remains ledger WIP until a declared completion/loss transaction occurs.

Therefore the total-WIP metric does not need to determine every tick whether that unit is currently:

```text
on a belt
in an inserter hand
in machine input/output
committed to an active craft
in a buffer
on the ground
in a player inventory
```

This removes physical-holder scanning from the authoritative one-tick total-WIP path.

The authoritative point metric method is recorded as:

```text
conservation_ledger
```

with dependencies on the exact boundary/loss transaction methods.

### 6. Physical holder census remains required as an independent cross-check

Changing the authority does **not** make the physical census optional.

Ledger errors can accumulate: if an undeclared loss or masked boundary violation occurs once, a ledger-only result may remain biased for the rest of the run.

Canonical conserved-WIP scenarios therefore require an independent physical census at a declared validation cadence.

Initial v1 default:

```text
cross_check_interval = 60 simulation ticks
```

that is, once per simulation second at normal tick semantics.

The cadence is measurement/provenance metadata and may be tuned after profiling. It does not change the tick-resolution ledger WIP definition.

A physical census is also required:

- during READY to establish/validate initial WIP;
- at the final experiment boundary;
- optionally immediately after selected disruptive/material-handling events when inexpensive and useful.

### 7. Physical census measures holder/decomposition state and validates the ledger

At each cross-check, supported census adapters estimate the physical tracked work present in categories such as:

```text
stationary buffers/process inventories
belt/underground/splitter transport lines
inserter hands
active-craft occupancy
ground items
player-held tracked work
other explicitly supported holders
```

The census produces both:

1. a total physical work-unit count when coverage is complete; and
2. a location/holder decomposition useful for teaching and diagnostics.

The census therefore answers questions such as:

> Where is the WIP accumulating?

without becoming the ordinary per-tick definition of total WIP.

Lab 4 and other buffer/decomposition exercises may require these census/decomposition observations even though total WIP itself comes from the ledger.

### 8. Ledger/census discrepancies are never silently reconciled

When physical-census coverage is complete, FISL calculates:

```text
wip_census_discrepancy(T)
  = physical_census_WIP(T) - ledger_WIP(T)
```

For canonical 1:1 integer workpiece flows, the default allowed tolerance is:

```text
0 work units
```

A future flow using exact rational work units may define an exact rational comparison; tolerance is not an excuse for floating-point drift.

If the discrepancy is nonzero:

- the ledger remains the recorded authoritative total-WIP state;
- FISL MUST NOT overwrite/reconcile the ledger to the census automatically;
- emit a first-class `wip_census_discrepancy` validity event;
- preserve both values and census decomposition;
- mark WIP validity as suspect beginning after the most recent successful cross-check because the exact onset of an unobserved conservation failure may be unknown.

A later exact declared correction/loss transaction may restore accounting prospectively, but does not erase the earlier suspect interval.

### 9. Discrepancy policy is conservative because ledger errors can persist

Let:

```text
T_good = most recent successful complete census boundary
T_bad  = boundary where a discrepancy is first detected
```

If no exact event identifies when the conservation failure occurred, strict canonical analysis treats:

```text
[T_good, T_bad]
```

as a WIP-validity uncertainty interval.

Metrics whose required WIP integration overlaps that interval become incomplete/flagged under ADR 0010 strict-coverage semantics.

Subsequent census agreement does not retroactively prove every intervening ledger state correct; the discrepancy event remains part of run provenance.

This is the mechanism that prevents the ledger's accumulative error mode from failing quietly.

### 10. Incomplete census coverage is distinct from a confirmed discrepancy

If the physical census cannot account for every relevant holder at a cross-check, it emits:

```text
wip_census_coverage_incomplete
```

rather than fabricating a comparison.

This does not automatically change the ledger value.

However, canonical research/course scenarios SHOULD avoid unsupported holder modes when they require census validation/decomposition. Persistent inability to perform required cross-checks can make WIP validity incomplete according to the scenario's analysis policy.

### 11. Player-carried tracked work remains WIP under ledger accounting

Tracked work entering a player's inventory after admission has not crossed an external completion/loss boundary.

Therefore it remains part of authoritative ledger WIP.

This supersedes ADR 0005 §16's treatment of player inventory as an automatic WIP-coverage failure.

FISL SHOULD census player-held tracked work and emit diagnostics such as:

```text
manual_carriage_wip_current
manual_carriage_wip_item_ticks
manual_carriage_event
```

This supports ordinary learner redesign without making WIP disappear when loaded equipment is mined.

### 12. Manual carriage is still scientifically visible and has an end-of-run escalation rule

Player carriage is not invisible merely because it remains WIP.

Canonical scenarios may discourage or prohibit using the player as a normal material-transport mechanism. The default teaching policy is:

- transient player-held WIP during redesign: diagnostic, WIP remains valid if ledger/census agree;
- sustained/manual transport: diagnostic and scenario-policy condition;
- tracked player-held work remaining at final experiment boundary: emit `manual_carriage_residual` and flag canonical experiment validity for objectives/comparisons that require normal production flow.

The run and WIP values are preserved. FISL does not rewrite player-held work as zero or pretend it was delivered.

A scenario that deliberately studies manual transport may define a different explicit policy later.

### 13. Ground and other internal holding states likewise do not change total ledger WIP

A tracked work unit dropped on the floor, moved between internal holders, or temporarily stranded remains WIP until it crosses a declared exit/loss boundary.

Physical census may separately classify:

```text
uncontained_wip
manual_carriage_wip
unsupported_holder_wip
```

for diagnostic/decomposition purposes.

### 14. Unsupported mobile transport no longer implies silent total-WIP undercount, but may invalidate decomposition/cross-check coverage

A train, logistic robot, or vehicle carrying already-admitted conserved work does not cause the ledger total to fall.

However, if FISL lacks a census adapter for that holder:

- total ledger WIP may remain defined from boundary conservation;
- physical location/decomposition is incomplete;
- the required census cross-check may become incomplete;
- canonical scenarios SHOULD still avoid such modes until census/accounting adapters exist.

This distinction is more precise than treating an unsupported holder as zero WIP.

### 15. Active-craft and belt adapters are demoted from total-WIP authority to census/decomposition validation

ADR 0005's active-craft occupancy and transport-line deduplication semantics remain useful for physical census.

They are no longer load-bearing on the authoritative tick-resolution total-WIP metric for conserved flows.

Consequences:

- active-craft behavior still receives runtime validation because census continuity and decomposition depend on it;
- belt-line deduplication still receives runtime validation;
- failure of one of these adapters may produce incomplete census validation/decomposition without necessarily preventing ledger WIP from being calculated;
- strict analyses that require successful independent census validation may still mark the affected WIP window incomplete.

### 16. Boundary integrity becomes load-bearing and standard port apparatus MUST enforce the one-way protocol

The conservation ledger is only as trustworthy as its entry/exit transactions.

ADR 0003's net source-withdrawal method cannot reconstruct arbitrary masked gross reverse transfer within the same settlement interval. Therefore canonical conserved-flow apparatus MUST make reverse flow and direct learner manipulation structurally difficult/impossible where Factorio permits.

Standard v1 source/sink apparatus MUST, where applicable:

- be non-minable by learners;
- be non-destructible in normal scenario operation;
- be non-operable for ordinary direct player inventory interaction;
- use filters/directions/prototype design that enforce the declared material and one-way role;
- expose only the intended automated transfer side/interface;
- detect any reverse/contamination evidence that remains observable;
- fail READY when the binding/apparatus cannot satisfy the canonical protocol.

This upgrades one-way apparatus hardening from a convenience to part of the conserved-ledger validity contract.

### 17. Unobserved destruction/loss is a validity failure until modeled as a declared loss boundary

If admitted work is destroyed without an exact declared loss transaction, the ledger cannot know the correct new WIP from boundary accounting alone.

The physical census should detect the resulting discrepancy at the next validation point when coverage is complete.

The run then follows the discrepancy policy above.

A later explicit scrap/yield-loss process should emit exact loss transactions and thereby preserve ledger accounting rather than relying on census inference.

### 18. WIP time integration remains exact under ADR 0010

The ledger has one exact prepared-boundary state for every executed experiment tick.

Therefore:

```text
WIP_area[A,B)
  = sum_{T=A}^{B-1} ledger_WIP(T)
```

and:

```text
average_WIP
  = WIP_area / (B-A)
```

retain ADR 0010's tick-resolution semantics without every-tick physical holder scans.

Cross-check cadence does not create sample-and-hold approximation in total WIP; it only determines how frequently the independent physical validation is performed.

### 19. Little's-Law compatibility becomes clearer

For a conserved flow:

```text
ledger WIP
completion-port throughput
Little's-Law-derived cycle time
```

all derive from the same flow-unit definition and entry/exit accounting boundaries.

This reduces the risk that physical-holder implementation details accidentally redefine WIP relative to throughput.

### 20. Physical inventory and subsystem/queue measurements remain separate measurements

The ledger defines **whole-flow total WIP** only where its conservation assumptions apply.

It does not replace physical inventory or local queue measurements.

A Lab 4 question such as:

> How much work is waiting before machine 2?

still requires a physical/local observation method.

Likewise arbitrary multi-material inventory remains a vector measurement under ADR 0005.

### 21. Provenance distinguishes authoritative ledger WIP from census validation

A total WIP result records at least:

```text
method: conservation_ledger
flow_id
initial_wip
admission observation/method dependencies
completion observation/method dependencies
declared loss dependencies
cross_check_cadence_ticks
last successful census boundary
census discrepancy/coverage events
strict validity coverage
```

Physical census observations carry their own holder-adapter methods and Factorio/FISL adapter versions.

A report should make it possible to answer separately:

- What total WIP did the accounting ledger assert?
- When was that ledger independently cross-checked?
- Where was the work physically observed at those checks?
- Were any discrepancy/coverage intervals detected?

## Illustrative resolved metric shape

Exact schema syntax remains implementation work, but conceptually:

```yaml
metrics:
  line_wip:
    type: wip
    flow: workpiece_flow
    method: conservation_ledger
    validation:
      physical_census:
        required: true
        every: 60ticks
        discrepancy_tolerance: 0
        include_player_inventory: true
```

Canonical flow:

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
    entry_ports: [workpiece_source]
    completion_ports: [finished_goods]
```

## POC validation fixture

The first POC should exercise:

```text
source -> inserter -> belt -> assembler -> inserter -> sink
```

For a single admitted workpiece:

```text
ledger WIP = 1
```

at every canonical boundary after admission and before completion, independent of physical holder.

At 60-tick cross-check boundaries, physical census must also report total 1 and identify the holder category correctly enough for the supported fixture.

The fixture must also deliberately create at least one discrepancy case to prove that:

- the ledger is not silently overwritten;
- a discrepancy event is emitted;
- strict WIP validity becomes flagged over the conservative uncertainty interval.

## Consequences

### Positive

- Exact tick-resolution whole-flow WIP no longer requires every-tick belt/machine/inserter census.
- The WIP definition aligns directly with the already-declared source/sink accounting lifetime.
- Player inventory during legitimate redesign no longer creates artificial WIP disappearance.
- Active-craft and belt adapter bugs cannot silently redefine authoritative total WIP.
- Physical census remains valuable as an independent check and as a decomposition/teaching measurement.
- The ledger/census disagreement provides a direct measurement-integrity test.
- Little's-Law WIP and throughput share the same explicit boundary transactions by construction.

### Negative / trade-offs

- A missed boundary/loss transaction can create a persistent ledger error rather than a transient census error.
- The design therefore depends more strongly on hardened one-way port apparatus and mandatory independent census validation.
- A census discrepancy may conservatively invalidate a larger interval than the instant at which the true error occurred.
- Physical decomposition remains Factorio-adapter-specific and must still be runtime-tested.
- This method applies only to genuinely conserved declared flows, not arbitrary production graphs.

## Acceptance criteria

This decision is implemented correctly when:

1. conserved-flow total WIP is calculated from initial WIP plus exact admission/completion/loss transactions;
2. the ledger emits an exact prepared-boundary WIP value each tick without full holder scans;
3. READY performs an initial physical census and canonical baselines normally establish WIP=0;
4. a required coarse physical census independently validates/decomposes WIP at a declared cadence, initially 60 ticks;
5. complete census disagreement never silently reconciles the ledger and emits a validity event;
6. strict WIP validity conservatively marks the interval since the prior successful cross-check when discrepancy onset is unknown;
7. player-held admitted work remains total WIP and is measured diagnostically rather than becoming zero/missing;
8. residual player-held tracked work at experiment end produces an explicit experiment-validity flag;
9. unsupported holder modes can make census/decomposition coverage incomplete without automatically erasing ledger WIP;
10. active-craft and belt adapters remain required for census/decomposition fixtures but not every-tick total-WIP authority;
11. standard conserved-flow ports enforce the one-way protocol strongly enough for ledger boundary accounting;
12. undeclared destruction/loss is surfaced by discrepancy/validity handling rather than silently modifying WIP;
13. average WIP continues to use exact tick integration of ledger point states;
14. result provenance records both ledger method/dependencies and census-validation state.
