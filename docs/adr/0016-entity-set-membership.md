# ADR 0016: Entity-Set Selection and Membership Semantics

- **Status:** Accepted
- **Scope:** FISL v1 scientific schema

## Context

Several accepted measurements need named groups of Factorio entities:

- production-machine state classification;
- pooled productive/starved/blocked time;
- holder coverage and diagnostics;
- stage/zone analysis;
- future role ownership or local dashboards.

A static list of entity IDs is insufficient for normal FISL labs because the learner may legitimately add, remove, replace, or relocate production equipment during a run.

Entity sets therefore need precise dynamic membership semantics without becoming a second definition of the system boundary.

## Decision

### 1. An `entity_set` is an analytical selector, not a system boundary

A named entity set answers:

> Which Factorio entities are subjects of this measurement/control view at this time?

It does not by itself define:

- what material is inside the production system;
- where authoritative flow crosses the system boundary;
- who owns an entity organizationally;
- whether an entity is allowed to exist.

Those remain separate concepts.

### 2. V1 entity sets use explicit selector predicates

A selector may constrain at least:

```text
system / zone
Factorio entity type
prototype name(s)
FISL role/tag exclusions or inclusions
```

Illustrative form:

```yaml
entity_sets:
  line_machines:
    zone: factory_floor
    types:
      - assembling-machine
      - furnace
    exclude_roles:
      - fisl_apparatus
```

The final schema may normalize these fields but MUST preserve explicit selection criteria.

### 3. V1 entity-set membership is dynamic by default

If a learner builds a matching machine during a run, it becomes a member when the canonical membership evaluation first recognizes it.

If a member is mined/destroyed/moved so it no longer matches, it ceases to be a member at the corresponding canonical boundary.

An implementation may maintain membership incrementally from build/mine/move events rather than rescan the zone every tick, provided the resulting membership intervals are equivalent.

### 4. Membership is evaluated on canonical FISL boundary semantics

For spatial selectors, ADR 0002's canonical entity position/zone-membership rule applies.

The entity-set state at boundary `T` is the membership used for the prepared interval:

```text
[T, T+1)
```

This matches ADR 0004/0010 prepared-state semantics.

### 5. Entity membership has explicit eligibility intervals

For time aggregation, each subject has intervals during which it belongs to the set.

Conceptually:

```text
machine A selected from tick 100 through 499
eligibility interval = [100,500)
```

Pooled machine-time denominators therefore sum only eligible machine-ticks, not the full experiment duration multiplied by every machine that ever appeared.

This directly supports ADR 0010's pooled resource-time semantics.

### 6. A newly built machine does not retroactively contribute history

If a machine is constructed at/near boundary `T`, it contributes state/machine-time only from the first interval in which it is canonically selected.

Its prior nonexistence is not interpreted as `unavailable`, `idle`, or missing classification.

Likewise, after it leaves the set, future intervals are not part of that entity's eligibility denominator.

### 7. Unexpected loss of a required fixed subject is distinguishable from ordinary dynamic membership

Some scenarios may require a specific apparatus/resource to exist throughout a run.

Such a subject should be represented by a required binding or an entity set with an explicit fixed/required policy, not by assuming all dynamic set departures are protocol violations.

Canonical learner-owned production sets are generally dynamic; FISL-owned ports/apparatus use stronger binding/integrity rules.

### 8. Overlapping entity sets are allowed

One entity may simultaneously belong to:

```text
all_line_machines
assembly_stage
high_priority_cell
```

Overlap has no automatic double-counting consequence. Each metric explicitly names its subject set.

The set model therefore supports multiple analytical views over one factory.

### 9. FISL apparatus is excluded explicitly rather than by geometry alone

Source/sink entities and other FISL-owned apparatus may physically lie inside a zone.

Selectors used for learner production equipment SHOULD exclude entities marked with FISL apparatus roles/tags/prototypes as appropriate.

This preserves ADR 0002's separation between geometry and accounting/experimental apparatus.

### 10. Entity identity and membership provenance are retained

Where Factorio supplies a stable runtime entity identifier such as `unit_number`, FISL uses it as the run-local subject identifier and retains prototype/type/position information needed for audit.

If an entity class lacks a suitable stable identifier, its adapter must define an equivalent run-local identity method before it can participate in per-entity longitudinal metrics.

### 11. Entity-set selection failure is coverage, not zero activity

If FISL cannot reliably determine membership because of unsupported entities, invalid references, or selector adapter failure, affected measurements become incomplete/flagged.

FISL MUST NOT silently treat an unknown subject as absent or nonproductive merely to preserve a clean denominator.

### 12. Selector definitions are immutable during a run

The resolved scenario fixes entity-set selector rules before `RUNNING`.

The membership population changes as the world changes, but the predicate itself does not change through ad-hoc runtime commands.

A future explicitly modeled phase-dependent selector is possible but not required for v1.

### 13. Entity sets are included in resolved experiment identity

Because changing which machines are measured changes metric semantics, selector definitions participate in the resolved experiment hash/provenance.

Membership history is run data.

## Consequences

### Positive

- Learners can add/remove production machines without breaking measurement semantics.
- Pooled machine-time has a correct eligibility denominator for changing resource populations.
- Entity sets remain reusable analytical views rather than accidental system boundaries.
- Overlap supports stage/local/global analysis cleanly.
- FISL apparatus exclusion is explicit.

### Negative / trade-offs

- Runtime must maintain dynamic membership accurately.
- Some Factorio entity classes may need specialized identity/movement handling.
- A simple static list implementation is insufficient for learner-editable production sets.

## Acceptance criteria

Entity-set semantics are ready when:

1. entity sets are analytical selectors distinct from systems/zones;
2. selectors explicitly identify zone/type/prototype/role criteria;
3. learner production sets are dynamically maintained;
4. membership follows canonical prepared-boundary semantics;
5. each member has explicit eligibility intervals for aggregation;
6. new entities do not retroactively contribute time and removed entities do not remain in denominators;
7. fixed required apparatus uses stronger binding policies rather than ordinary dynamic-set assumptions;
8. overlapping sets are permitted;
9. FISL apparatus is explicitly excludable;
10. run-local entity identity and membership history are auditable.
