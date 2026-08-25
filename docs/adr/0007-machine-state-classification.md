# ADR 0007: Production Machine State Classification

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

Factory Physics labs need to distinguish why production resources are or are not producing. In particular, FISL needs useful and auditable concepts for:

- productive operation;
- input starvation;
- output blocking;
- equipment/resource unavailability;
- deliberate disablement;
- other idle states.

Factorio exposes `LuaEntity.status` as a native `defines.entity_status` value for entities that support status. The runtime documentation explicitly states that this is the entity's actual status even when a custom GUI status is configured.

However, Factorio's status vocabulary is broader than the Factory Physics vocabulary and is entity-type-specific. Examples include `working`, `item_ingredient_shortage`, `fluid_ingredient_shortage`, `full_output`, `no_power`, `low_power`, `no_fuel`, `disabled_by_control_behavior`, `disabled_by_script`, `no_recipe`, and many statuses used only by trains, inserters, labs, rockets, power systems, or expansion mechanics.

A second complication is that raw status is not always enough to answer the operational question "did this machine actually make production progress during this interval?" The Factorio API documents that `is_crafting()` only indicates that a craft has been started; it does **not** indicate that crafting progress is currently advancing. Brownouts can also slow crafting rather than simply switching a machine off.

ADR 0004 therefore made raw Factorio statuses primitive point observations rather than directly calling them productive/starved/blocked time. This ADR defines the derived production-machine classification on top of those primitives.

The design must preserve enough detail to support later utilization metrics without turning every non-working state into one vague `idle` bucket or assuming that every status has the same meaning for every entity class.

## Decision

### 1. Raw Factorio status remains the authoritative primitive status observation

FISL continues to preserve the native Factorio status as a primitive observation, for example:

```text
entity_status_sample:
  entity: assembler_17
  raw_status: item_ingredient_shortage
  method: factorio_point_sample
```

The FISL production-state classification is **derived** from primitive observations.

FISL MUST NOT replace or discard the raw status when emitting a higher-level state.

This ensures that future classifier changes can be applied to existing run data without rerunning the experiment.

### 2. Machine state is not modeled as only one raw-status lookup

FISL v1 does not define classification as:

```text
raw status -> one global category
```

because:

- statuses are entity-family-specific;
- some statuses indicate a constraint but do not prove zero production progress;
- `low_power` can describe degraded operation rather than complete unavailability;
- the same broad operational concept can be represented by different raw statuses on different production resource types.

Instead, the classifier uses an entity-family adapter and may combine multiple primitive observations.

Conceptually:

```text
raw Factorio status
craft/activity evidence
entity family / role
scenario configuration
        |
        v
FISL production-state classification
```

### 3. V1 production-state classification is scoped to explicitly supported production-resource adapters

Canonical v1 Factory Physics labs SHOULD classify crafting-machine resources such as assembling machines and furnaces through a `crafting_machine` production-state adapter.

Other entity families may expose raw status observations without automatically receiving the same production-state classification.

Future adapters may support:

- mining drills;
- inserters/material handlers;
- pumps/fluid equipment;
- labs;
- train/loading resources;
- other production-resource types.

FISL MUST NOT assume a status has the same scientific meaning for an unsupported entity family merely because the enum name is familiar.

### 4. The classification has two primary dimensions plus a convenience headline

A classified production-resource observation contains at least:

1. **activity** — whether process progress is occurring;
2. **constraint/cause** — the best supported explanation for the current operating condition;
3. **headline state** — a convenient mutually exclusive summary for dashboards and later aggregations.

This prevents a constraint from erasing useful activity information.

Illustrative logical form:

```text
activity: progressing | not_progressing | unknown
constraint: none | input_shortage | output_blocked | energy_limited |
            energy_unavailable | disabled_control | configuration |
            equipment_unavailable | other | unknown
headline: productive | starved | blocked | unavailable |
          disabled | idle_other | unclassified
```

The exact serialized names may change during the final schema pass, but the distinction among activity, cause, and headline is part of the contract.

### 5. `productive` means measured process progress occurred, not merely that Factorio displayed `working`

For a supported crafting-machine adapter, FISL's strongest evidence of productive operation is that the machine's declared process made measurable progress during the observation interval.

A `working` raw status is useful evidence, but FISL SHOULD NOT make the scientific definition of productive time depend solely on the status label.

This distinction matters under conditions such as brownouts, where a machine may make reduced progress while the status reports a power limitation.

For canonical v1 crafting-machine labs, the observation plan SHOULD collect enough state to establish craft progress between adjacent checkpoints, including as applicable:

- `raw_status`;
- `is_crafting`;
- `crafting_progress`;
- `products_finished`;
- recipe identity when needed for validation.

The exact interval-activity algorithm is defined below.

### 6. `is_crafting` is supporting state, not proof of productive progress

Factorio documents `is_crafting()` as indicating whether a craft process has been started, and explicitly notes that it does not indicate whether progress is currently being made.

Therefore FISL MUST NOT define:

```text
is_crafting == true -> productive
```

A machine can have an active craft while progress is stalled or degraded.

`is_crafting` remains useful for:

- active-craft WIP accounting under ADR 0005;
- validating craft-progress observations;
- distinguishing configured process state from a completely idle/unconfigured machine.

### 7. V1 crafting-machine activity is measured from progress across adjacent canonical checkpoints

For supported canonical crafting-machine scenarios, FISL derives an interval activity observation for `[T-1,T)` by comparing the machine's process state at the adjacent canonical checkpoints.

The adapter must be able to recognize progress when either:

- `crafting_progress` advances; or
- one or more crafts complete between samples, detected using a monotonic completion counter such as `products_finished`, together with the current progress state.

Conceptually, a machine is `progressing` for the interval when the adapter can establish that positive process progress occurred during `[T-1,T)`.

It is `not_progressing` when the adapter has complete coverage and can establish no process progress occurred.

It is `unknown` when coverage, recipe changes, unsupported behavior, counter discontinuity, or another condition prevents a trustworthy determination.

The exact arithmetic must be regression-tested against the pinned Factorio runtime. FISL MUST NOT rely on a naïve `crafting_progress(T) > crafting_progress(T-1)` test because progress resets when a craft completes.

### 8. Canonical v1 classified machines SHOULD use stable recipe configuration during measured phases

To keep craft-progress evidence auditable, canonical v1 production-state labs SHOULD lock or otherwise constrain the measured machine's recipe during a measured phase.

If a recipe changes in a way not anticipated by the observation plan, FISL should record a classification/coverage event rather than silently comparing incompatible progress counters.

Future versions may explicitly support scheduled or learner-controlled recipe switching with stronger activity adapters.

### 9. `starved` is a mechanistic input-shortage state, not a moral judgment or failure label

A production resource is `starved` when:

- it is not making process progress for the classified interval/state; and
- the strongest supported cause is absence/insufficiency of required process input.

For the v1 crafting-machine family, relevant raw statuses may include, subject to the pinned Factorio version and adapter validation:

```text
item_ingredient_shortage
fluid_ingredient_shortage
no_ingredients
```

Future adapters may include equivalent resource-specific statuses.

`starved` means the machine cannot progress because required process material is unavailable. It does **not** imply that the overall factory design is bad. A pull-controlled or demand-satisfied system may intentionally spend time in an input-starved condition.

### 10. `blocked` is a mechanistic output/backpressure state

A production resource is `blocked` when:

- it is not making process progress for the classified interval/state; and
- the strongest supported cause is inability to discharge output or downstream capacity/backpressure.

For supported crafting machines, relevant raw statuses may include:

```text
full_output
waiting_for_space_in_destination
```

where the status is valid for that entity family and scenario.

Again, `blocked` is descriptive rather than inherently negative. A machine may be blocked because downstream demand is intentionally satisfied.

### 11. `unavailable` means the production resource cannot provide normal process capacity for a non-input/non-output reason

A production resource is `unavailable` when it is not making process progress and the supported cause is an enabling-resource or equipment condition that prevents normal production capacity.

Examples for supported adapters may include:

```text
no_power
no_fuel
frozen
broken
```

The classifier may distinguish more specific causes such as:

```text
energy_unavailable
equipment_unavailable
```

while using `unavailable` as the headline category.

This is intentionally different from starvation: absence of iron plate is a process-input shortage; absence of machine power/fuel is an availability/resource condition.

### 12. `low_power` is not automatically `unavailable`

Factorio machines can continue operating at reduced speed during a brownout, and the raw `low_power` status does not by itself establish zero productive progress.

Therefore:

- `low_power` SHOULD produce an `energy_limited` / degraded condition flag or cause;
- if process progress occurred, the headline remains `productive` while retaining the degraded-power condition;
- if no process progress occurred and power limitation is the best supported cause, the headline may be `unavailable` with cause `energy_limited`;
- FISL MUST preserve the raw status either way.

This is one reason activity and constraint are separate dimensions.

### 13. `disabled` is distinct from physical/resource unavailability

A production resource is `disabled` when its process is deliberately prevented from operating by a control mechanism rather than by missing process input, blocked output, or unavailable capacity.

Relevant raw/runtime indicators may include:

```text
disabled_by_control_behavior
disabled_by_script
disabled
```

FISL should retain the more specific cause so later experiments can distinguish:

- circuit/controller disablement;
- FISL/script disablement;
- other explicit disabled states.

This distinction is important for later control-system experiments: a controller intentionally turning off a machine should not be counted as random equipment downtime.

### 14. `idle_other` covers non-producing states that are neither starved, blocked, unavailable, nor disabled

Examples may include configuration or experiment states such as:

```text
no_recipe
recipe_not_researched
normal
```

when they occur on a classified production resource and no stronger supported interpretation applies.

Canonical scenarios SHOULD generally prevent accidental `no_recipe`/recipe-configuration states during measured runs unless they are part of the lesson.

`idle_other` is intentionally visible rather than silently folded into starvation or availability.

### 15. Unknown or newly introduced statuses do not silently become `idle_other`

The Factorio status vocabulary can change between versions, and FISL's classification registry is scientific logic rather than a best-effort GUI translation.

If an adapter encounters a raw status that is not mapped for the pinned Factorio version/entity family, the classification is:

```text
unclassified
```

and FISL records a classifier-coverage condition.

It MUST NOT silently map unknown statuses to `idle_other` or another apparently valid category.

This makes runtime-version changes detectable instead of allowing semantic drift.

### 16. The mapping registry is versioned by Factorio runtime and FISL adapter version

Run provenance must identify enough information to reproduce the classifier, including:

- Factorio version;
- FISL version;
- production-state adapter/classifier version;
- entity prototype/type/family;
- raw status observations used;
- additional activity observations used.

The current Factorio documentation distinguishes a stable release line from the experimental release line; FISL's classifier must be validated against the specifically supported runtime rather than assuming the latest documentation is identical to the pinned stable version.

### 17. Headline classification uses measured activity first, then supported constraint cause

For a supported production-resource interval/state with complete evidence, the conceptual headline precedence is:

```text
if activity == progressing:
    productive
else if cause == input_shortage:
    starved
else if cause == output_blocked:
    blocked
else if cause in {energy_unavailable, energy_limited, equipment_unavailable}:
    unavailable
else if cause == disabled_control:
    disabled
else if cause in {configuration, other}:
    idle_other
else:
    unclassified
```

This precedence intentionally permits:

```text
headline: productive
condition: energy_limited
raw_status: low_power
```

rather than forcing every raw status into a mutually exclusive bucket.

### 18. The classifier reports reasons/conditions even when the headline is productive

A productive machine can still be in a degraded or constrained condition.

For example:

```text
headline: productive
activity: progressing
constraint: energy_limited
raw_status: low_power
```

or potentially:

```text
headline: productive
activity: progressing
constraint: input_shortage
raw_status: item_ingredient_shortage
```

if an in-progress craft is still advancing while the machine lacks material for a subsequent craft.

The headline answers "did productive process progress occur?" while the constraint explains the contemporaneous machine condition.

This preserves more information than a single enum.

### 19. Classification is mechanistic and local; it does not determine whether the state is desirable

FISL machine-state categories describe the immediate production-resource condition.

They do not assert that:

- starvation is always waste;
- blocking is always a fault;
- disabled time is always bad;
- 100% productive time is always desirable.

A low-WIP pull system may intentionally produce more machine idle/starved time while improving system performance.

This is pedagogically important because FISL should teach system optimization rather than reward local machine utilization by definition.

### 20. Raw state and classification are separate from utilization denominators

This ADR does not define a bare `utilization` metric.

Later metrics may calculate quantities such as:

```text
productive_time / scheduled_time
productive_time / available_time
```

but the denominator semantics belong to the aggregation/utilization contract.

This ADR provides the classified state series needed to calculate them without prematurely declaring which nonproductive categories belong in a denominator.

### 21. Point-state classification and interval activity remain distinguishable

ADR 0004 established that point samples do not automatically imply duration.

This ADR therefore distinguishes:

- a **point condition/status classification** at canonical boundary `T`; and
- an **interval activity determination** for `[T-1,T)` based on progress evidence.

A later aggregation rule may combine these into time-occupancy metrics, but the raw temporal semantics remain auditable.

FISL SHOULD avoid presenting a point status sample as if it directly proved the machine held that state for an entire tick unless the declared interval-classification method establishes that assumption.

### 22. Canonical v1 state-duration metrics should use one-tick classified intervals, not UI polling cadence

For v1 Factory Physics analysis, the intended high-resolution input to later time aggregation is one classified record per executed simulation tick/interval for each measured production resource.

UI refresh cadence is irrelevant.

A dashboard may update once per second while the scientific state accumulator operates at simulation-tick resolution.

If a later performance optimization changes the scientific sampling cadence, that change must be explicit in measurement metadata and cannot silently alter the semantics.

### 23. State classification should support both per-machine and aggregate analysis

Primitive/raw observations and classified state should retain individual machine identity.

Later aggregations may derive:

- time distribution for one machine;
- fraction of machines starved at a point in time;
- total machine-ticks by state;
- state distribution for a production cell/entity set;
- bottleneck/dependency diagnostics.

FISL MUST NOT discard per-machine provenance merely because the learner UI initially shows aggregate percentages.

### 24. Classification coverage failures are not the same as observed idle time

If FISL cannot classify a machine because of:

- missing raw status;
- missing progress state;
- unsupported entity family;
- unexpected recipe change;
- counter discontinuity;
- new/unmapped Factorio status;
- invalid entity reference;

then the result is missing/unclassified coverage.

FISL MUST NOT count that interval as zero production, `idle_other`, starvation, or any other state merely to preserve a 100% denominator.

Missing classification is missing measurement.

### 25. Canonical v1 labs should provide classifier fixtures for every supported state

The test suite should include small deterministic scenarios that force one supported crafting machine into each intended condition and verify both raw and classified output.

At minimum:

```text
normal production             -> productive
missing tracked ingredient    -> starved / input_shortage
full output buffer            -> blocked / output_blocked
no electrical power           -> unavailable / energy_unavailable
circuit-disabled machine      -> disabled / disabled_control
no configured recipe          -> idle_other / configuration
```

A brownout fixture should verify that reduced-power operation can remain `productive` while carrying an `energy_limited` condition when craft progress is actually observed.

These fixtures should run against every Factorio runtime version FISL claims to support.

## Initial v1 classifier table

This table is conceptual and applies only when the raw status is valid for the supported production-resource adapter. The pinned-version implementation table must be tested against the runtime.

| Raw/status evidence | Cause/condition | Headline when no progress | Headline when progress observed |
| --- | --- | --- | --- |
| `working` | `none` | `idle_other` or coverage anomaly | `productive` |
| `item_ingredient_shortage` | `input_shortage` | `starved` | `productive` + input-shortage condition |
| `fluid_ingredient_shortage` | `input_shortage` | `starved` | `productive` + input-shortage condition |
| `no_ingredients` | `input_shortage` | `starved` | `productive` + input-shortage condition |
| `full_output` | `output_blocked` | `blocked` | `productive` + output-blocked condition |
| `waiting_for_space_in_destination` | `output_blocked` | `blocked` | `productive` + output-blocked condition |
| `no_power` | `energy_unavailable` | `unavailable` | `productive` + anomaly/energy condition |
| `low_power` | `energy_limited` | `unavailable` | `productive` + energy-limited condition |
| `no_fuel` | `energy_unavailable` | `unavailable` | `productive` + anomaly/energy condition |
| `frozen` | `equipment_unavailable` | `unavailable` | `productive` + anomaly condition |
| `broken` | `equipment_unavailable` | `unavailable` | `productive` + anomaly condition |
| `disabled_by_control_behavior` | `disabled_control` | `disabled` | `productive` + anomaly condition |
| `disabled_by_script` | `disabled_control` | `disabled` | `productive` + anomaly condition |
| `disabled` | `disabled_control` | `disabled` | `productive` + anomaly condition |
| `no_recipe` | `configuration` | `idle_other` | `productive` + anomaly condition |
| `recipe_not_researched` | `configuration` | `idle_other` | `productive` + anomaly condition |
| unmapped status | `unknown` | `unclassified` | `productive` + unclassified condition |

`working` with no measured progress is intentionally not automatically productive; it should prompt adapter/test scrutiny because raw status and measured process activity disagree.

## Proposed scenario/metric shape

Illustrative only:

```yaml
entity_sets:
  line_machines:
    system: factory
    types:
      - assembling-machine
      - furnace

metrics:
  machine_state:
    type: production_state
    entities: line_machines

    adapter: crafting_machine

    activity:
      method: craft_progress_delta
      cadence: 1tick

    classification:
      profile: factory_physics_v1
```

The final schema should likely avoid requiring ordinary scenario authors to reproduce the raw mapping table. The adapter/profile should supply a validated default while provenance records the exact classifier version.

## Consequences

### Positive

- Raw Factorio state remains auditable and reclassifiable.
- Productive operation is tied to actual process progress rather than one GUI/status label.
- Brownouts and other degraded conditions do not automatically erase productive work.
- Starvation, blocking, equipment/resource unavailability, and deliberate disablement remain distinct.
- The model is entity-family-aware and resilient to Factorio's broad status vocabulary.
- Unknown/new statuses become visible coverage issues instead of semantic drift.
- Later utilization metrics can choose denominators explicitly rather than inheriting hidden assumptions.
- The same state series can support local bottleneck analysis without claiming that maximum local utilization is globally optimal.

### Negative / trade-offs

- Production-state instrumentation requires more than sampling `LuaEntity.status`.
- Craft-progress comparison requires careful wrap/completion handling and runtime regression tests.
- One-tick per-machine observation can be more expensive than low-frequency GUI polling.
- Additional entity families require explicit adapters rather than getting a generic status lookup for free.
- The richer activity/cause/headline model is slightly more complex than one flat enum.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- exact productive-time / starvation-time / blocked-time aggregation arithmetic;
- utilization denominators;
- whether state time is integrated by one-tick classified intervals or a more optimized equivalent implementation;
- metrics for performance magnitude during degraded power, e.g. 60% nominal speed;
- entity-set schema details;
- mining-drill, inserter, pump, train, or other resource adapters;
- scheduled-vs-unscheduled capacity concepts;
- UI colors/diodes for classified states;
- statistical aggregation across machines.

Those belong to later aggregation/utilization, visibility, and implementation ADRs.

## Acceptance criteria

The machine-state-classification portion of Issue #1 is complete when we agree that:

1. native Factorio status remains a primitive auditable observation;
2. classification is derived and entity-family-aware rather than one global raw-status lookup;
3. v1 canonical production-state classification focuses on explicitly supported crafting-machine resources;
4. machine state separates process activity from constraint/cause and exposes a convenience headline state;
5. productive operation is supported by observed craft progress, not `working` or `is_crafting` alone;
6. starvation means nonprogress caused by required process-input shortage;
7. blocking means nonprogress caused by output/downstream backpressure;
8. unavailable means nonprogress caused by enabling-resource/equipment availability rather than input/output flow;
9. deliberate control/script disablement is distinct from unavailable time;
10. low power can coexist with productive operation and therefore is represented as a degraded condition rather than automatically zero production;
11. idle/configuration states remain distinct from starvation/blocking/unavailability;
12. unknown statuses/entity families produce unclassified coverage rather than silent fallback;
13. classifier provenance is versioned with Factorio/FISL runtime information;
14. point status and interval progress evidence retain distinct temporal semantics;
15. canonical fixtures validate every supported state, including a brownout case.

## References

- Factorio Runtime API — `LuaEntity.status`, `is_crafting()`, `crafting_progress`, and `products_finished`.
- Factorio `defines.entity_status` documentation.
- Factorio Wiki, Electric system — insufficient generation causes electric machines to slow proportionally during brownouts.
