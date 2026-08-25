# FISL v1 Product Requirements Document

**Product:** Factorio Industrial Systems Laboratory (FISL)  
**Target:** First working deterministic Factory Physics laboratory  
**Primary handoff:** Codex / implementation agent  
**Status:** Ready for implementation  
**Scientific contract:** ADRs 0001–0016 + `FISL_V1_SCHEMA.md`

---

# 1. Executive summary

FISL is an experimental layer built around Factorio.

The governing definition is:

> **Factorio is the simulation engine. FISL is the experimental apparatus. Scenarios are experiments. Courses are sequences of experiments.**

The governing implementation rule is:

> **Use Factorio to model the system. Use FISL to model the experiment.**

FISL must preserve ordinary Factorio gameplay as the learner's way of changing the production system. Learners add machines, belts, inserters, buffers, and circuit controls using normal Factorio mechanics.

FISL adds what a serious laboratory needs around that world:

- reproducible baseline/reset;
- explicit experiment time/phases;
- declared system boundaries;
- controlled material supply and customer demand;
- authoritative boundary transactions;
- rigorous WIP/throughput/cycle-time semantics;
- machine-state classification;
- explicit aggregation/window rules;
- objectives and controlled metric disclosure;
- run provenance and reproducible datasets;
- deterministic integration-test fixtures.

V1 is intentionally deterministic. It is the foundation for later stochastic variability, reliability, economics, and organizational-cybernetics experiments.

The POC is successful when a user can run a real Factorio scenario from the CLI, play the factory normally, finish a controlled experiment, and receive a reproducible run dataset/report whose WIP, throughput, cycle time, machine state, demand service, and objectives follow the accepted ADR semantics.

---

# 2. Product thesis

Factorio is already an unusually strong physical production-system model. FISL should not replace that model with generic educational widgets.

Examples:

- More production capacity → learner builds/upgrades Factorio machines.
- More buffer capacity → learner builds Factorio belts/chests/storage.
- Pull/feedback control → learner uses Factorio circuits when suitable.
- Exact 60-unit/min customer demand → FISL.
- Exact measurement window → FISL.
- Reproducible source/sink accounting → FISL.
- Machine failures/stochastic demand later → FISL.

The desired feel is:

> **Factorio, but with a laboratory bench attached.**

Not:

> An educational application that happens to use Factorio graphics.

---

# 3. Pedagogical model

The instructional method is **scenario before theory**.

Expected learner sequence:

1. Encounter a deliberately problematic production system.
2. Diagnose or modify it using normal Factorio mechanics.
3. Observe controlled measurements.
4. Receive/learn the formal concept.
5. Re-run/redesign using the new conceptual model.
6. Compare outcomes and explain the difference.

FISL must therefore support repeated runs from a pristine baseline and preserve every attempt for comparison.

The first course is deterministic Factory Physics. Later layers are outside v1 but must remain architecturally possible:

```text
Layer I   Factory Physics / deterministic flow
Layer II  Variability, buffering, control, cybernetics
Layer III Organizational cybernetics / role + information experiments
```

A useful intellectual constraint:

> **Layer I teaches what the model shows. Layer II teaches what the model hides. Layer III investigates what the model cannot contain.**

---

# 4. Users

## 4.1 Learner

Needs to:

- launch/connect to a scenario;
- understand the task and experiment state;
- play Factorio normally;
- see only allowed live metrics/objective information;
- complete a run;
- review post-run metrics and compare attempts;
- reset/retry easily.

The learner should not need to understand FISL internals, YAML, RCON, or telemetry files.

## 4.2 Scenario author / instructor

Needs to:

- create/edit `scenario.yaml`;
- choose a baseline save;
- define system, ports, flows, metrics, objectives, visibility;
- validate before launch;
- inspect detailed post-run diagnostics;
- create deterministic baseline/expected fixtures;
- tune instructional parameters without editing FISL runtime code.

## 4.3 FISL developer / researcher

Needs to:

- reproduce runs from manifests;
- inspect primitive observations and metric provenance;
- verify Lua/Python calculation equivalence;
- write headless integration fixtures;
- add new adapters/schedules/metrics without breaking accepted semantics.

---

# 5. V1 scope

V1 MUST provide:

1. Python scenario schema/compiler.
2. Python CLI/controller.
3. Local Factorio server orchestration with RCON control.
4. Graphical Factorio client connection for interactive runs.
5. FISL core Factorio mod in Lua.
6. Generic FISL source/sink apparatus.
7. Exact experiment time/phases.
8. Rectangular zones and one primary zone per system.
9. Dynamic entity sets.
10. Source/sink port settlement.
11. Replenish and constant scheduled supply.
12. Zero/finite/unbounded external supply storage.
13. FIFO backlog customer demand.
14. Primitive scientific observations + ordered event stream.
15. Conserved-work-unit WIP.
16. Throughput and boundary rates.
17. Crafting-machine state classification.
18. Customer on-time item service.
19. Little's-Law-derived cycle time + controlled probe method support.
20. Exact aggregation/window semantics.
21. Learner/instructor/debug disclosure rules.
22. Requirement/preference objectives.
23. Reproducible run datasets/manifests.
24. Baseline reset/retry.
25. Headless deterministic integration tests.
26. Scenario support sufficient for Factory Physics Labs 0–6.

---

# 6. Explicit v1 non-goals

Do NOT expand the initial implementation into these areas unless needed to complete a v1 contract requirement:

- stochastic demand/supply;
- equipment failure/repair simulation;
- economics/cost accounting;
- quality/yield/rework modeling;
- organizational roles/VSM;
- differential-information multiplayer experiments;
- arbitrary per-item digital identity through production recipes;
- train/logistic-robot authoritative WIP;
- fluid/energy/info ports as first-class boundary interfaces;
- order/customer objects;
- lost-sales demand;
- LMS integration;
- custom web dashboard;
- database requirement;
- cloud service;
- general statistical-analysis package;
- generalized automatic understanding of arbitrary Factorio factories;
- replacement of Factorio circuits/logistics mechanics;
- exact human-input replay;
- preserving vanilla Factorio achievements.

Raw data should remain useful for future external analysis, but these are not v1 product requirements.

---

# 7. Initial runtime target

Initial tested Factorio target:

```text
Factorio stable 2.0.77
```

The code should avoid unnecessary coupling to one patch version, but scientific adapters/classifier tables must be validated against versions FISL claims to support.

Do not silently use experimental 2.1 API behavior when implementing a 2.0.77 runtime path.

The run manifest records the actual Factorio version.

---

# 8. Technology choices

## 8.1 Python controller/compiler

Use Python 3.12+.

Preferred libraries/approach:

```text
Pydantic 2.x     typed author/resolved schema validation
Typer            CLI
Rich             readable CLI status/results
pytest           unit/integration orchestration
standard hashlib canonical SHA-256 provenance
```

The YAML parser and RCON client library are implementation choices. Hide them behind small adapters so they can be replaced.

Do not introduce a database in v1.

## 8.2 Factorio runtime

Factorio mod code uses the Factorio runtime's modified Lua 5.2 environment.

Use normal Factorio runtime APIs and lifecycle conventions.

Persistent state should contain boring serializable data; transient LuaObject references/indexes are reconstructed.

## 8.3 Serialization

```text
YAML   scenario authoring
JSON   resolved scenario, manifest, summary
JSONL  authoritative telemetry/event streams
Markdown optional generated human report
```

## 8.4 Process topology

Canonical interactive topology:

```text
+--------------------+
| Python controller  |
| CLI/compiler       |
+---------+----------+
          |
          | launch / RCON
          v
+--------------------+
| Local Factorio     |
| authoritative      |
| server + FISL mod  |
+---------+----------+
          |
          | Factorio multiplayer protocol
          v
+--------------------+
| Graphical Factorio |
| learner client     |
+--------------------+
```

Headless tests omit the graphical client.

---

# 9. Repository target structure

Recommended structure:

```text
FactorioResearch/
├── README.md
├── pyproject.toml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FISL_V1_PRD.md
│   ├── FISL_V1_SCHEMA.md
│   ├── FACTORY_PHYSICS_LABS_V1.md
│   ├── SCENARIO_MEASUREMENT_CONTRACT.md
│   └── adr/
├── python/
│   └── fisl/
│       ├── __init__.py
│       ├── cli.py
│       ├── scenario/
│       │   ├── author_models.py
│       │   ├── resolved_models.py
│       │   ├── compiler.py
│       │   ├── validators.py
│       │   ├── canonical.py
│       │   └── units.py
│       ├── controller/
│       │   ├── process.py
│       │   ├── rcon.py
│       │   ├── protocol.py
│       │   ├── run.py
│       │   └── client.py
│       ├── telemetry/
│       │   ├── models.py
│       │   ├── reader.py
│       │   └── validate.py
│       ├── metrics/
│       │   ├── aggregation.py
│       │   ├── throughput.py
│       │   ├── service.py
│       │   ├── cycle_time.py
│       │   └── objectives.py
│       └── report/
│           ├── run_report.py
│           └── compare.py
├── factorio/
│   ├── fisl-core/
│   │   ├── info.json
│   │   ├── data.lua
│   │   ├── control.lua
│   │   └── fisl/
│   │       ├── lifecycle.lua
│   │       ├── protocol.lua
│   │       ├── experiment.lua
│   │       ├── phases.lua
│   │       ├── zones.lua
│   │       ├── entity_sets.lua
│   │       ├── ports.lua
│   │       ├── schedules.lua
│   │       ├── observations.lua
│   │       ├── wip.lua
│   │       ├── machine_state.lua
│   │       ├── demand.lua
│   │       ├── accumulators.lua
│   │       ├── objectives.lua
│   │       ├── telemetry.lua
│   │       └── gui.lua
│   └── fisl-factory-physics/
│       ├── info.json
│       ├── data.lua
│       └── prototypes/
│           └── workpieces.lua
├── scenarios/
│   └── factory-physics/
│       ├── fp00-measurement/
│       │   ├── scenario.yaml
│       │   ├── baseline.zip
│       │   └── README.md
│       └── ...
└── tests/
    ├── unit/
    ├── schema/
    ├── fixtures/
    └── integration/
```

Do not create meaningless empty modules solely to match this tree. Let implementation structure converge around responsibilities while preserving the architecture boundary.

---

# 10. Core architectural responsibilities

## 10.1 Python answers

> What experiment are we running, and what do the resulting data mean?

Python owns:

- authoring YAML parsing;
- schema/type validation;
- dimensional/cross-reference validation;
- exact time/rate compilation;
- observation-plan dependency closure;
- canonical resolved JSON;
- experiment hashes/fingerprints;
- Factorio process/server lifecycle;
- RCON protocol;
- run directory/manifest;
- telemetry collection/validation;
- post-run recomputation;
- report/comparison tools.

## 10.2 Lua answers

> What is happening in Factorio right now?

Lua owns:

- authoritative simulation tick/phase state;
- clean start/transition/end boundaries;
- runtime world bindings;
- source/sink settlement;
- supply/demand processes;
- dynamic entity-set membership;
- WIP holder observations;
- machine progress/state classification inputs;
- deterministic runtime accumulators;
- objective state required in-game;
- learner UI;
- authoritative telemetry/event emission.

## 10.3 Scenario answers

> What did the instructor intend?

Scenario configuration owns:

- baseline world identity;
- system boundary;
- experimental phases;
- external input/demand policy;
- flows/work units;
- metrics/windows;
- objectives;
- disclosure;
- pedagogical metadata.

---

# 11. Scenario compiler requirements

The compiler MUST implement `docs/FISL_V1_SCHEMA.md`.

## FR-SCHEMA-001 — Strict typed authoring model

Reject unknown fields/invalid unions by default.

Validation messages should identify scenario path and reason clearly.

## FR-SCHEMA-002 — Exact duration compilation

Convert duration syntax to exact integer ticks.

Reject non-integral ticks.

## FR-SCHEMA-003 — Exact rate compilation

Convert rates to exact rational schedule representation; no floating-point items-per-tick drift.

## FR-SCHEMA-004 — ID/cross-reference validation

Validate all references:

```text
phases
zones
systems
entity sets
ports
demand IDs
flows
metrics
objectives
visibility
```

before Factorio launch.

## FR-SCHEMA-005 — Scientific compatibility validation

Reject invalid combinations such as:

- scalar WIP without work-unit basis;
- Little's-Law CT with mismatched WIP/TH flow/window;
- throughput using non-sink completion interfaces;
- unqualified percentile weighting;
- bare utilization denominator;
- service cohort/horizon that cannot resolve deadlines in canonical configuration;
- objective threshold incompatible with metric dimension.

## FR-SCHEMA-006 — Observation-plan compiler

Derive the primitive/runtime instrumentation required by declared metrics/objectives/live UI.

Do not force scenario authors to manually enumerate primitive measurements.

## FR-SCHEMA-007 — Resolved model

Generate typed resolved models containing explicit:

```text
ticks
windows
rational schedules
normalized capacities
actual seed
resolved protocol/spec version
```

## FR-SCHEMA-008 — Canonical serialization/hash

Generate deterministic canonical JSON + SHA-256 resolved experiment hash.

## FR-SCHEMA-009 — JSON Schema

Expose a generated JSON Schema or equivalent machine-readable authoring contract for tooling/editor support.

---

# 12. Controller / process requirements

## FR-CTRL-001 — Environment discovery

Locate configured Factorio server/client binaries, mod directory, and run workspace.

Configuration may come from CLI flags and/or a user config file.

Do not hard-code machine-specific absolute paths in scenarios.

## FR-CTRL-002 — `fisl validate`

Validate/compile a scenario without launching Factorio.

Output:

```text
success/failure
resolved phase timing
baseline existence/hash
required software/mod expectations
metric/objective summary
```

## FR-CTRL-003 — Run creation

`fisl run <scenario>` must:

1. validate/compile;
2. allocate unique run ID/workspace;
3. hash/verify baseline;
4. write initial manifest + resolved JSON;
5. allocate local game/RCON ports and RCON password;
6. launch Factorio server against a working baseline copy;
7. wait for RCON/runtime readiness;
8. negotiate protocol;
9. upload resolved configuration in verified chunks;
10. wait for Lua `READY`;
11. launch/connect graphical client unless headless;
12. monitor run lifecycle;
13. collect output artifacts;
14. finalize manifest/summary/report.

## FR-CTRL-004 — Local networking safety

Default RCON binds loopback.

Generate random per-run credentials.

Do not store RCON password in learner-facing reports or scientific telemetry.

## FR-CTRL-005 — Headless mode

`fisl run ... --headless` must run the same authoritative server/config/runtime without a graphical client and support deterministic integration fixtures.

## FR-CTRL-006 — Retry/reset

Provide a simple workflow such as:

```text
fisl retry <run_id>
```

or equivalent.

Retry always reloads the declared immutable baseline and creates a new run ID.

## FR-CTRL-007 — Report

Provide:

```text
fisl report <run_id>
```

that displays final metric values, coverage, objectives, protocol flags, hashes, and relevant method/window metadata.

## FR-CTRL-008 — Compare

Provide:

```text
fisl compare <run-a> <run-b> [...]
```

The comparison must:

- warn about incompatible reproducibility/metric semantics;
- show requirement status;
- compare preference metrics;
- avoid inventing a scalar score.

---

# 13. Controller ↔ Lua protocol

Follow ADR 0015.

Required behavior:

```text
protocol version query
begin config transfer
append config chunks
commit config/hash verification
READY status
start request (headless/controller option)
abort request
status query
final save request
```

Interactive mode should normally allow the learner to start from the in-game READY screen rather than starting before the client connects.

The protocol transport is low-volume RCON. It never owns experiment timing.

---

# 14. Lua lifecycle

Lifecycle state machine:

```text
INITIALIZING
   -> READY
   -> RUNNING
   -> COMPLETED

or
   -> ABORTED
```

Validity/protocol flags are metadata, not destructive terminal states.

## FR-LIFE-001 — READY validation

Before READY:

- validate runtime protocol/config;
- resolve port bindings;
- validate surfaces/zones;
- validate required prototypes/recipes;
- initialize entity selectors;
- validate no stale active run state;
- initialize fresh ledgers/seed/sequence counters.

## FR-LIFE-002 — Start boundary

Start request becomes pending.

Lua begins experiment at next eligible clean simulation boundary and records `experiment_start_map_tick`.

## FR-LIFE-003 — Completion

At exclusive final boundary:

1. settle final interval;
2. capture required closing observations;
3. finalize accumulators/objectives;
4. emit completion records;
5. enter COMPLETED;
6. pause/freeze continued drift where practical;
7. allow final save capture.

No next-interval supply/demand should be created after experiment completion.

## FR-LIFE-004 — Abort

Abort preserves/flushes data and reason.

Do not erase run state.

---

# 15. Authoritative tick pipeline

Implement ADR 0004 ordering.

At checkpoint `T`:

1. ingest queued Factorio sensor events;
2. update/reconcile dynamic entity membership;
3. settle physical interval `[T-1,T)` ports/activity;
4. emit interval primitive facts;
5. if final boundary, finalize/complete;
6. apply phase transition if boundary;
7. advance external supply/demand for `[T,T+1)`;
8. apply FISL-controlled source staging/replenishment mutations;
9. run integrity/protocol checks;
10. capture prepared point-state observations at `T`;
11. update metric accumulators/objective/live UI state;
12. commit ordered telemetry batch.

Any implementation optimization must preserve these observable semantics.

Factorio event handlers act as sensors. They should not independently mutate authoritative experiment ledgers outside the coordinator except where unavoidable and explicitly normalized.

---

# 16. Ports and schedules

Follow ADR 0003.

## FR-PORT-001 — Generic apparatus

Provide visually distinct generic source and sink port prototypes suitable for automation by inserters/belts while protected from ordinary learner mining/destruction/manual inventory interaction as practical.

Tag/mark them as FISL apparatus.

## FR-PORT-002 — Binding

Resolve configured surface + position + expected prototype to exactly one endpoint during READY.

Record runtime entity ID/prototype/capacity in provenance.

Loss of an authoritative port endpoint during RUNNING aborts/invalidates according to contract rather than silently continuing.

## FR-PORT-003 — Source settlement

Measure input as documented net withdrawal from source staging.

Detect reverse flow as protocol violation.

## FR-PORT-004 — Sink settlement

Record tracked material as `sink_delivery`, remove/accept it, and return standard sink staging to empty each settlement.

## FR-PORT-005 — Demand distinction

Calculate separately:

```text
sink_delivery
demand_fulfilled
surplus_delivery
demand_backlog
```

Surplus cannot satisfy future demand.

## FR-PORT-006 — Replenish source

Maintain target staging quantity after settlement while active.

## FR-PORT-007 — Scheduled source

Use exact constant rate accumulator.

## FR-PORT-008 — External source storage

Support:

```text
capacity = 0
capacity = finite integer
capacity = unbounded
```

Track pending quantity and loss when overflow exceeds configured storage.

## FR-PORT-009 — Demand cohorts

Generate FIFO age cohorts for demand-created quantity.

Fulfillment allocates oldest-first and retains created tick/fulfilled tick/quantity.

---

# 17. Zones / systems / entity sets

## FR-SYS-001 — Zones

Static rectangular surface-qualified zones with half-open position membership.

## FR-SYS-002 — System

One primary zone per v1 system.

Geometry does not itself define material crossing; ports do.

## FR-SYS-003 — Boundary containment diagnostics

Use entity position for membership and collision box for straddling/integrity diagnostics.

Do not compute fractional entity membership.

## FR-SET-001 — Dynamic entity sets

Implement ADR 0016 dynamic selectors.

A machine built during run joins at first canonical eligible interval; removed machine leaves future intervals.

Maintain eligibility intervals for pooled machine-time.

## FR-SET-002 — Overlap

Allow an entity to belong to multiple analytical sets.

---

# 18. WIP implementation

Follow ADR 0005.

## FR-WIP-001 — Physical inventory vs WIP

Never sum unlike arbitrary Factorio items and label the result scalar WIP.

## FR-WIP-002 — Conserved flow mapping

Implement exact material→work-unit coefficients.

Canonical Factory Physics workpiece family uses 1:1 stage transformations.

## FR-WIP-003 — Supported holder adapters

V1 canonical holder coverage:

```text
internal containers/buffers
crafting-machine process inventories
active craft occupancy
belt/underground/splitter transport lines
inserter held stack
dropped tracked item entities inside system
```

Exclude FISL source/sink apparatus.

## FR-WIP-004 — Unsupported carriers

Tracked work entering player inventories, trains, logistic bots, or unsupported vehicles during canonical WIP runs produces coverage/protocol flags rather than silent zero.

## FR-WIP-005 — Belt deduplication

Count unique underlying transport lines, not every belt owner reference.

## FR-WIP-006 — Active craft continuity

Ensure one workpiece does not disappear/double-count when inputs become committed to a craft and output does not yet exist.

This requires runtime-version-specific integration tests.

## FR-WIP-007 — Conservation diagnostic

Maintain/check:

```text
initial WIP + admitted - completed - declared losses = current WIP
```

Emit `wip_balance_error` diagnostic.

---

# 19. Machine-state classification

Follow ADR 0007.

Initial supported adapter: `crafting_machine`.

Record raw Factorio status + progress evidence.

Classified dimensions:

```text
activity:
  progressing
  not_progressing
  unknown

cause/constraint:
  none
  input_shortage
  output_blocked
  energy_limited
  energy_unavailable
  disabled_control
  configuration
  equipment_unavailable
  other
  unknown

headline:
  productive
  starved
  blocked
  unavailable
  disabled
  idle_other
  unclassified
```

Productive is established from actual craft progress/completion evidence, not only `working` or `is_crafting`.

Low power may be productive + energy-limited.

Keep classifier mapping versioned by Factorio/FISL adapter version.

---

# 20. Metric engine requirements

Lua may maintain streaming values needed for live UI/objectives. Python must be able to independently recompute/verify final results from authoritative data where retained data permit.

## FR-METRIC-001 — WIP point metric

Prepared state at `T` describes interval `[T,T+1)`.

## FR-METRIC-002 — WIP integration

For `[A,B)`:

```text
wip_unit_ticks = sum T=A..B-1 WIP(T)
average_wip = wip_unit_ticks / (B-A)
```

## FR-METRIC-003 — Throughput

```text
completion flow units in [A,B) / simulation duration
```

Numerator is normalized completion-sink `sink_delivery`.

No bare instantaneous throughput.

## FR-METRIC-004 — Service

Canonical service:

```text
on_time_item_rate = on-time quantity / created quantity
```

for demand cohorts created in an explicit cohort window and fully observed through deadlines.

## FR-METRIC-005 — Demand wait distributions

Weight waits by demanded quantity.

## FR-METRIC-006 — Cycle time

Canonical continuous method:

```text
CT_LL = average WIP / throughput
```

with same flow and same analysis window.

Method metadata must say `little_law_derived`.

Support an isolated `single_work_unit_probe` method under explicit isolation guarantees.

## FR-METRIC-007 — State durations

Use classified one-tick intervals, not raw point status.

## FR-METRIC-008 — No bare utilization

Any state fraction must name its denominator.

## FR-METRIC-009 — Percentiles

Use weighted nearest-rank empirical quantile.

No implicit library interpolation.

## FR-METRIC-010 — Missing coverage

Strict by default. Missing data does not become zero or silently shrink denominator.

Partial diagnostic values may be emitted only with explicit coverage metadata.

## FR-METRIC-011 — Empty populations

Produce `undefined/no_data`, not zero or 100%.

---

# 21. Objectives

Follow ADR 0012.

Supported v1:

```text
requirement minimum
requirement maximum
requirement range
preference minimize
preference maximize
```

No implicit weighted score.

Overall requirements:

```text
PASS if all pass
FAIL if any definitively fail
UNDETERMINED if none fail but any unresolved
```

Protocol validity is separate.

Preferences remain a vector for comparison.

---

# 22. In-game GUI requirements

Keep the GUI small and Factorio-native.

## READY panel

Show at least:

```text
scenario title
short task/instruction
run status READY
Start Experiment button (interactive mode)
```

Optional:

```text
phase plan
allowed objective targets
```

## RUNNING panel

Show:

```text
current phase
simulation elapsed/remaining time as allowed
learner_live metrics only
allowed objective target/provisional status
```

Do not expose hidden diagnostics through tooltips or alternate views.

UI refresh cadence may be lower than scientific sampling cadence.

## COMPLETED panel

Show `learner_post_run`:

```text
metric results
objective results
method/window labels where important
run ID
```

Provide a clear pointer that full report/comparison is available through controller tooling.

Do not build a web dashboard in v1.

---

# 23. Visibility

Follow ADR 0011.

The runtime/compiler must maintain separate disclosure lists for:

```text
learner_live
learner_post_run
instructor
debug
```

Visibility must never change collection or scientific calculation.

Visibility contributes to experiment identity.

V1 disclosure is pedagogical, not cryptographic protection from a user with local filesystem access.

---

# 24. Telemetry and run artifacts

## 24.1 Run directory

Required target:

```text
runs/<run_id>/
  manifest.json
  scenario.resolved.json
  telemetry.jsonl
  events.jsonl
  summary.json
```

Recommended:

```text
  final-save.zip
  server.log
  report.md
```

The controller may store working server files elsewhere and copy only final artifacts into the run directory.

## 24.2 Telemetry properties

Authoritative scientific stream MUST preserve:

```text
run ID / stream identity
schema version
experiment/map ticks as appropriate
monotonic FISL sequence number
observation/event type
subject/port/entity ID
quantity/value/unit
measurement method
interval/boundary semantics
```

## 24.3 Storage optimization

The contract is logically tick-resolution where specified, but physical logs MAY use lossless semantic compression:

- state-change/run-length intervals;
- exact streaming accumulators;
- compact per-holder change records;

provided integration tests prove equivalence to canonical one-tick semantics.

Do not sacrifice auditability merely to minimize file size.

## 24.4 Lua output

Use Factorio-supported `script-output` file writing for authoritative streams.

The Python controller collects/tails these files.

Live RCON responses are not the only scientific record.

---

# 25. Provenance / manifest

Implement ADR 0013.

Required manifest fields include:

```text
run_id
spec version
scenario ID/version
scenario source hash
resolved experiment hash
baseline save hash
actual Factorio version
FISL core mod version/commit
controller/compiler version/commit
mod manifest
experiment seed
reproducibility fingerprint
protocol version
start/end map ticks
experiment duration ticks
completion/abort status
protocol/coverage summary
artifact inventory/checksums
```

Wall timestamps are operational metadata only.

The learner/team ID is optional and does not enter reproducibility fingerprint by default.

---

# 26. Reset / retry

Implement ADR 0014.

Reset = reload immutable baseline.

Never implement arbitrary entity-by-entity world undo for v1.

Final saves do not become baselines implicitly.

Every retry receives new run ID.

Same fingerprint means same controlled input condition, not identical learner behavior.

Canonical measured runs should not support mid-run save/resume as a normal workflow.

---

# 27. Factory Physics content mod

Create a small `fisl-factory-physics` content mod distinct from core runtime when practical.

It should initially provide purpose-built workpiece item/recipe families for rigorous conserved-flow labs.

Example:

```text
fisl-rough-workpiece
  -> fisl-machined-workpiece
  -> fisl-inspected-workpiece
  -> fisl-finished-workpiece
```

Recipes used in canonical Little's Law scenarios preserve one logical workpiece exactly.

Avoid productivity, probabilistic outputs, quality transformations, and other yield-changing behavior in these canonical recipes.

The learner still uses normal Factorio assemblers, belts, inserters, buffers, and circuits.

---

# 28. Scenario packages / baselines

Each course scenario should contain at least:

```text
scenario.yaml
baseline.zip
README/instructor/course material as desired
```

Baseline saves are immutable inputs and SHA-256 hashed.

Binary save versioning may use Git LFS if appropriate; tooling choice is not part of the scientific contract.

Do not require all seven polished course baselines before proving the platform. Integration fixtures can be smaller synthetic saves.

---

# 29. Testing strategy

Testing is a product requirement, not cleanup work, because scientific semantics depend on Factorio-specific behavior.

## 29.1 Python unit tests

Test:

- duration/rate parsing;
- Pydantic schema variants;
- canonical serialization/hash stability;
- cross-reference validation;
- exact aggregation;
- weighted nearest-rank quantiles;
- service cohort allocation;
- objective status;
- compare compatibility logic.

## 29.2 Pure logic Lua tests where practical

Keep modules such as rational schedule accumulators, ledger allocation, and simple classifiers isolated enough to test outside Factorio when practical.

Do not treat mock tests as sufficient for Factorio entity behavior.

## 29.3 Factorio headless integration tests

Required fixtures from `FACTORY_PHYSICS_LABS_V1.md`:

1. clock/phase boundary fixture;
2. port settlement fixture;
3. supply overflow storage fixture;
4. WIP holder continuity fixture;
5. belt transport-line deduplication fixture;
6. machine-state fixture set;
7. aggregation fixture;
8. demand cohort/deadline fixture;
9. cycle-time direct-vs-derived fixture;
10. visibility fixture;
11. objective fixture;
12. dynamic entity-set fixture;
13. reset/provenance fixture;
14. RCON/config/telemetry fixture.

## 29.4 Golden scientific result tests

For deterministic fixtures, store expected exact values such as:

```text
source withdrawals
sink deliveries
WIP unit-ticks
state ticks
service numerator/denominator
throughput numerator/window ticks
objective outcome
```

Do not golden-test only formatted decimals.

## 29.5 Runtime version tests

Run Factorio-specific adapter fixtures against every Factorio patch version declared supported.

Unknown raw statuses should cause classifier coverage failure rather than silently falling back.

---

# 30. Performance requirements

FISL must not make ordinary small/medium teaching factories unplayable.

No fixed UPS budget is asserted before profiling, but implementation must observe these principles:

- compile an observation plan; do not scan the whole world unnecessarily;
- maintain entity membership incrementally where possible;
- deduplicate belt transport lines;
- use exact streaming accumulators for high-frequency aggregate state;
- avoid expensive filesystem writes for every low-level object if a lossless interval/change representation is equivalent;
- keep UI refresh slower than scientific sampling when useful;
- expose profiler/debug metrics to developers but not learners by default.

Performance optimizations MUST be validated against canonical semantics.

---

# 31. Error handling / validity

FISL should fail early when the scientific contract cannot be satisfied.

## Pre-run hard failures

Examples:

```text
invalid schema
missing baseline
unsupported Factorio version
protocol mismatch
missing/ambiguous port binding
missing required item/recipe prototype
invalid metric compatibility
```

Do not start the experiment.

## Runtime protocol/coverage flags

Examples:

```text
boundary straddle
tracked work in player inventory
source reverse flow
unknown machine status
WIP balance error
missing holder adapter
pause when prohibited
```

Preserve data and flag validity according to the relevant ADR; abort only when continued measurement would be misleading (for example losing an authoritative port endpoint).

Missing measurement is never silently zero.

---

# 32. CLI usability target

The exact syntax may evolve, but the happy path should be approximately:

```text
$ fisl validate scenarios/factory-physics/fp05-pull/scenario.yaml
Scenario valid
Factorio: 2.0.77
Measured phase: 72,000 ticks
Metrics: 10
Objectives: 2

$ fisl run scenarios/factory-physics/fp05-pull
Run: 01...
Server ready
Launching Factorio client...

# learner plays experiment

Run completed
Service requirement: PASS (97.2%)
Average WIP: 118.4 workpieces
Throughput: 60.1 workpieces/min
Cycle time (Little's Law derived): 118.2 s

$ fisl retry 01...
...

$ fisl compare 01... 01...
```

The user should not need to manually manage server/RCON processes for normal operation.

---

# 33. POC definition of done

A working POC does **not** require all polished course content.

The POC is complete when all of the following are true:

1. `fisl validate` parses a real authoring YAML scenario and generates canonical resolved JSON/hash.
2. `fisl run` launches a local Factorio server from a baseline copy with the FISL mod.
3. Python and Lua negotiate protocol and transfer resolved configuration through RCON.
4. A graphical client can connect and the learner sees a READY/Start UI.
5. Start occurs on an authoritative clean simulation tick.
6. At least one generic source and sink work with per-tick settlement.
7. A conserved workpiece can travel through a normal belt/inserter/assembler line.
8. FISL measures source admission, sink completion, point WIP, average WIP, and throughput.
9. At least one crafting machine is classified productive/starved/blocked correctly in integration fixtures.
10. A demand-enabled sink records FIFO backlog and computes an on-time item rate.
11. Little's-Law-derived cycle time is computed from matching average WIP and throughput and labeled as derived.
12. A service requirement + minimize-WIP preference evaluates correctly.
13. Learner-live visibility hides at least one collected diagnostic that appears post-run.
14. The run directory contains resolved config, manifest, authoritative telemetry/events, and summary.
15. `fisl report` presents the result with coverage/method/window metadata.
16. Retry reloads the baseline and creates a new run ID.
17. Headless integration tests cover the critical clock/port/WIP/state/service/aggregation semantics.

Once this works, building/tuning Labs 0–6 is primarily scenario/content work rather than redesigning FISL.

---

# 34. Full v1 definition of done

V1 is ready for course use when:

- all POC requirements pass;
- the deterministic integration fixture suite from `FACTORY_PHYSICS_LABS_V1.md` passes;
- all metric results preserve method/window/coverage provenance;
- Python can verify/recompute final scientific summaries from retained run data as designed;
- controller error handling/reset is reliable enough for repeated classroom use;
- baseline/scenario versioning and hashing work;
- at least Labs 0–6 can be instantiated without lab-specific runtime code;
- representative course scenarios have been calibrated so their intended conceptual phenomena are visible;
- README/user docs explain installation, `validate`, `run`, `retry`, `report`, and `compare`.

---

# 35. Open implementation choices Codex may decide

Codex should make reasonable engineering choices and record ADRs if any choice changes architectural/scientific behavior.

Implementation choices intentionally left open include:

- exact Python package manager/build tooling;
- exact YAML parser;
- whether to use a third-party Source-RCON library or a small internal client;
- exact run-ID implementation (ULID vs UUIDv7);
- exact canonical JSON library/settings, provided deterministic hashing is tested;
- exact Lua module split;
- exact custom source/sink art/prototype base;
- exact lossless telemetry compression strategy;
- exact Rich CLI presentation;
- exact local server/client port allocation strategy;
- exact Git LFS policy for saves;
- implementation sequence.

Do not reopen accepted scientific semantics merely because an implementation shortcut would be easier. If an accepted semantic proves impossible against Factorio 2.0.77, document the evidence and propose a new/superseding ADR rather than silently changing behavior.

---

# 36. Source-of-truth hierarchy

When implementation questions arise, use this order:

1. Accepted ADRs in `docs/adr/` — specific scientific/architectural decisions.
2. `docs/FISL_V1_SCHEMA.md` — scenario/compiler contract.
3. This PRD — product/runtime requirements.
4. `docs/ARCHITECTURE.md` — broader rationale/long-term direction.
5. `docs/FACTORY_PHYSICS_LABS_V1.md` — course-level validation and integration scenarios.
6. `docs/RESEARCH_NOTES.md` — intellectual/research provenance.

If two documents conflict, accepted later ADRs supersede earlier illustrative examples.

---

# 37. ADR index relevant to implementation

```text
0001 Experiment Time and Phase Semantics
0002 Zones and System Boundary Semantics
0003 Material Ports, Supply, Demand, and Boundary Transactions
0004 Primitive Observations and Tick-Pipeline Semantics
0005 WIP, Inventory, and Flow-Unit Semantics
0006 Throughput and Boundary Flow-Rate Semantics
0007 Production Machine State Classification
0008 Service-Level and Demand-Cohort Semantics
0009 Cycle-Time and Flow-Time Measurement Methods
0010 Aggregation and Observation-Window Semantics
0011 Metric Visibility and Disclosure Semantics
0012 Objectives and Evaluation Semantics
0013 Run Provenance and Reproducibility Semantics
0014 Reset, Repeat, and Replay Semantics
0015 Python Controller ↔ Factorio Runtime Transport
0016 Entity-Set Selection and Membership Semantics
```

Codex should read these before implementing the corresponding subsystem.

---

# 38. Closing product definition

The v1 system should make this statement true:

> A FISL scenario can take a known Factorio world, declare a controlled deterministic experiment around it, let a human modify the factory using normal Factorio mechanics, and produce an auditable/reproducible scientific record of how the production system behaved.

The durable engineering artifact is the laboratory platform and its scenario contract—not one course script or one hard-coded factory.
