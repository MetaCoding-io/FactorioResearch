# ADR 0002: Zones and System Boundary Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

FISL needs a rigorous way to describe **where** an experiment takes place and **what counts as the system being measured**.

Those are related questions, but they are not the same question.

A rectangle drawn around part of a Factorio factory is useful for locating entities, but it is not by itself a complete industrial-system boundary. Material can cross through inserters, belts, trains, bots, or fluids; power and circuit networks can cross spatial boundaries; beacons can influence machines across a line; a FISL source or demand chest may physically sit inside the same rectangle while semantically representing the environment outside the system.

The contract therefore must not equate geometric inclusion with accounting membership or external interaction.

The v1 design must support Factory Physics labs cleanly while leaving a path toward later experiments involving more complex material, energy, information, and organizational boundaries.

## Decision

### 1. A `zone` is a spatial selector, not a system boundary

A FISL `zone` answers the question:

> Which part of which Factorio surface are we referring to?

A zone has no built-in WIP, throughput, ownership, or external-environment semantics.

A system boundary may **reference** a zone, but the meanings of `zone` and `system` must remain distinct.

This prevents hidden assumptions such as:

- every entity geometrically inside the rectangle automatically counts as WIP;
- every item geometrically outside the rectangle is external;
- every flow crossing the rectangle is measurable throughput;
- FISL-owned source/demand entities physically inside the rectangle must count as part of the production system.

### 2. V1 zones are static, rectangular, surface-qualified regions

A v1 zone is defined by:

- a unique zone ID;
- an explicit Factorio surface;
- an axis-aligned rectangle;
- immutable coordinates for the duration of a run.

Illustrative authoring form:

```yaml
zones:
  factory_floor:
    surface: nauvis
    area:
      left_top: [-50, -30]
      right_bottom: [50, 30]
```

V1 deliberately does not require:

- polygons;
- circles;
- dynamic/resizable zones;
- topology defined by walls or connected machines;
- automatically inferred factory boundaries.

Those may be added later if a concrete experiment requires them.

### 3. V1 zone coordinates are tile-aligned and use half-open geometry

The recommended v1 contract requires zone rectangle boundaries to be integer tile coordinates.

A zone is interpreted as:

```text
left <= x < right
top  <= y < bottom
```

or mathematically:

```text
[left, right) × [top, bottom)
```

This mirrors the half-open convention already accepted for experiment time and removes ambiguity for entities whose canonical position lies exactly on a boundary.

Tile-aligned boundaries are intentionally restrictive in v1. They make scenarios visually inspectable, easy to author, and difficult to misinterpret.

### 4. Surface identity is part of zone identity

A spatial coordinate is meaningless without a surface.

The author-facing scenario SHOULD use the human-readable Factorio surface name. At run initialization FISL resolves that surface and records sufficient provenance to identify the actual runtime surface used, including its name and runtime index when available.

A missing or ambiguous surface reference is a scenario validation failure.

### 5. Canonical entity membership uses `LuaEntity.position`

When FISL needs the answer:

> Is this entity spatially located in zone Z?

v1 uses the entity's canonical runtime position as the membership point.

An entity is spatially in a zone when:

```text
zone.left <= entity.position.x < zone.right
zone.top  <= entity.position.y < zone.bottom
```

FISL MUST NOT use the incidental behavior of a broad Factorio area query as the scientific definition of zone membership.

In particular, runtime APIs may return entities whose physical bounding box overlaps an area. FISL may use such queries as candidate lookups for efficiency, but MUST post-filter according to the explicit membership rule.

### 6. Entity footprint and entity membership are separate concepts

An entity's canonical position determines spatial membership.

Its physical collision footprint is used for a separate question:

> Does this entity straddle the declared zone boundary?

For relevant stationary production entities, FISL SHOULD use the runtime entity `bounding_box` (the oriented collision box) for containment validation.

The selection box is not the scientific footprint because it exists primarily for interaction/UI purposes and may be larger than the collision box.

For entity types with secondary physical bounding boxes, such as certain rail entities, later support must consider those additional boxes before claiming full containment.

### 7. A `system` is an accounting/experimental construct that references a zone

V1 introduces a system concept distinct from zones.

Illustrative shape:

```yaml
system:
  id: factory
  primary_zone: factory_floor
```

The system is the thing later measurement contracts will reference for concepts such as WIP, internal production entities, and controlled boundary interfaces.

For v1, each system has exactly one `primary_zone`.

The schema may contain additional zones for subregions or auxiliary measurements, but v1 does not define a multi-zone union as a single system boundary.

A future version may allow one system to be composed from multiple spatial regions without changing the meaning of an individual zone.

### 8. Zones may overlap; overlap does not imply ownership or aggregation

Multiple named zones may overlap in v1.

This is useful for experiments such as:

- the whole factory;
- a smelting subregion;
- an assembly subregion;
- a diagnostic area.

Overlap is not an error because zones are selectors.

However:

- no entity is automatically assigned exclusive ownership by a zone;
- overlapping zone metrics are independent measurements;
- FISL MUST NOT sum overlapping zone measurements without an explicitly defined aggregation that handles overlap.

The eventual `entity_set` and metric contracts will determine which selected entities are actually observed.

### 9. FISL-owned boundary/interface entities are not automatically internal merely because they are spatially inside

A source port, demand sink, marker, controller entity, or other FISL-owned apparatus may be physically located inside the primary zone for gameplay or implementation convenience while semantically representing the experiment boundary or external environment.

Therefore geometric inclusion does not force accounting inclusion.

Later contracts will define explicit entity sets and port semantics, but this ADR establishes the principle that FISL-owned boundary/interface apparatus can be excluded from internal production/WIP accounting even when located inside the primary zone.

This is necessary to avoid artificial WIP caused by source inventory waiting in a FISL supply chest or finished goods already delivered to a FISL demand sink.

### 10. A zone is not a material-flow detector

FISL MUST NOT infer authoritative input, output, or throughput merely from an item's or entity's geometric movement across the zone rectangle.

V1 material boundary flows are intended to be defined by explicit source/demand or other declared ports under the separate port contract.

This keeps throughput semantics auditable and avoids difficult ambiguities involving:

- inserter hands crossing the rectangle;
- belts or underground belts crossing it;
- train wagons whose inventory crosses as a container;
- logistic/construction bots;
- dropped items;
- fluid systems;
- mobile containers.

Spatial membership may later help describe WIP location, but it is not the authoritative boundary transaction mechanism.

### 11. Boundary integrity is a protocol/validation concern, not the membership rule itself

For rigorous Factory Physics scenarios, FISL SHOULD support a system boundary-integrity policy that detects obviously ambiguous layouts.

The recommended v1 default is conceptually `contained`:

- relevant internal stationary entities should have their physical collision footprint fully contained in the system's primary zone;
- relevant external stationary entities should not ambiguously straddle the system boundary;
- FISL-owned declared boundary/interface entities are exempt and governed by their own contract.

A straddling entity does not cause FISL to reinterpret membership using percentages or overlap area. Its canonical position still determines spatial membership, while the straddle is logged as a boundary-integrity event/protocol violation.

FISL SHOULD preserve run data rather than destroying a run solely because such a violation occurred.

### 12. Zone geometry is immutable during a run; entity membership may change

The coordinates of a v1 zone do not move or resize after the run enters `READY`.

Entities can be built, mined, rotated, moved, created, or destroyed during gameplay.

Therefore the set of entities spatially within a zone is dynamic even though the zone is static.

FISL SHOULD update relevant entity membership in response to observed world changes and/or deterministic validation scans.

If learner actions cause a relevant entity to straddle the system boundary under a containment policy, that is recorded as a protocol event/violation rather than silently resizing the zone or changing the scientific definition.

### 13. System boundaries are accounting boundaries, not guaranteed physical firewalls

Even a perfectly drawn spatial rectangle does not isolate every Factorio interaction.

Potential cross-boundary influences include:

- electric networks;
- circuit wires/signals;
- fluid and heat networks;
- beacon/module effects;
- logistic networks and bots;
- train networks;
- pollution and military/environmental interactions.

FISL v1 MUST NOT claim that geometric containment proves isolation from all such interactions.

Factory Physics scenario authors should deliberately design baseline worlds so that any external dependencies are known and pedagogically intentional.

For example, electric power may be treated as an exogenous service that is stable and intentionally outside the measured production system.

Future FISL versions may generalize boundary interfaces beyond material ports to explicit energy, information, transport, or environmental interfaces.

### 14. V1 should visualize declared zones for learners and authors

The scientific definition is the resolved coordinate rectangle, not the rendering.

However FISL SHOULD visibly render or otherwise identify the primary system zone during scenario setup and play so that the learner can understand the accounting boundary.

The visualization is pedagogical/UI state and MUST NOT itself determine membership.

### 15. Scenario authoring conveniences may differ from the resolved scientific representation

A later scenario authoring tool may let an instructor draw a rectangle in-game, select tiles, use marker entities, or otherwise define a zone interactively.

Those are authoring mechanisms only.

Before a run begins, every v1 zone MUST resolve to an explicit surface and exact rectangle in the scenario/run manifest.

This follows the same pattern as friendly time durations compiling to exact ticks.

## Proposed v1 schema shape

Illustrative only:

```yaml
spec: fisl/v1

zones:
  factory_floor:
    surface: nauvis
    area:
      left_top: [-50, -30]
      right_bottom: [50, 30]

  smelting_area:
    surface: nauvis
    area:
      left_top: [-40, -20]
      right_bottom: [-5, 20]

system:
  id: factory
  primary_zone: factory_floor

  boundary_integrity:
    entity_containment: contained
```

The eventual port contract may extend the system declaration conceptually with something like:

```yaml
system:
  boundary_interfaces:
    material:
      policy: explicit_ports
```

but the exact port schema is deliberately deferred to the next Issue #1 section.

## Implementation notes

Current Factorio runtime APIs provide the primitives needed for this design:

- `LuaEntity.position` gives the entity's current canonical position;
- `LuaEntity.bounding_box` exposes the oriented runtime collision box;
- `LuaEntity.selection_box` is separately exposed and should not be confused with the collision footprint;
- surface area queries can be used to find candidate entities, but FISL should post-filter candidates according to its own explicit membership rule.

The implementation should therefore avoid embedding scientific semantics in the exact behavior of `find_entities_filtered(area=...)`.

## Consequences

### Positive

- Spatial location and industrial/accounting semantics are no longer conflated.
- Source/demand apparatus can live conveniently near or inside the learner's factory without automatically contaminating WIP.
- WIP and throughput can later have explicit auditable definitions rather than being inferred from geometric overlap.
- Entity membership is deterministic and easy to explain.
- Collision footprint validation catches many accidental boundary ambiguities without making overlap the membership rule.
- Multiple diagnostic/subsystem zones can be added without prematurely implementing multi-system topology.
- Later energy/information/organizational interfaces can extend the system-boundary concept without replacing the zone model.

### Negative / trade-offs

- A rectangle alone cannot guarantee true physical isolation.
- Some cross-boundary Factorio interactions will initially depend on careful scenario design rather than automatic enforcement.
- Mobile inventories such as trains require later special treatment if used in WIP measurements across a spatial boundary.
- Boundary integrity and spatial membership are two separate concepts that implementers must not accidentally merge.
- FISL must maintain or recompute membership rather than simply trust an area-query result.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- which Factorio entity types belong in default measured `entity_set`s;
- exact semantics for items on belts, in machines, inserter hands, bots, trains, chests, or fluids;
- WIP inclusion/exclusion rules;
- source/demand port placement and transaction timing;
- how an item becomes internal when removed from a source port;
- how an item becomes external when delivered to a demand port;
- whether student building outside the primary zone is allowed, prohibited, or merely ignored;
- automatic detection of cross-boundary power, circuit, beacon, bot, fluid, or rail interactions;
- multi-zone systems;
- moving/mobile system boundaries;
- rails and secondary bounding-box details;
- exact rendering/authoring UI.

Those belong to the port, primitive-observation, entity-set, WIP, and later protocol contracts.

## Acceptance criteria for this decision

The zones/system-boundary portion of Issue #1 is complete when we agree that:

1. a zone is a spatial selector, not the complete system/accounting boundary;
2. v1 zones are static, rectangular, surface-qualified, tile-aligned regions;
3. zone geometry is half-open;
4. canonical spatial entity membership is based on `LuaEntity.position`;
5. collision bounding boxes are used for boundary-integrity checks, not membership percentages;
6. a v1 system references exactly one primary zone;
7. zones may overlap without implicit ownership or aggregation;
8. FISL-owned boundary/interface entities may be geometrically inside while semantically outside internal accounting;
9. throughput/input/output are not inferred from raw geometric boundary crossing;
10. zone geometry is immutable per run while entity membership can change;
11. system boundaries are accounting constructs and do not falsely claim perfect physical isolation from all Factorio interactions.
