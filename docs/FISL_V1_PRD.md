# FISL v1 Product Requirements Document

**Product:** Factorio Industrial Systems Laboratory (FISL)  
**Target:** First working deterministic Factory Physics laboratory  
**Primary handoff:** Codex / implementation agent  
**Status:** Ready for implementation after runtime-validation gate  
**Scientific contract:** ADRs 0001–0018 + `FISL_V1_SCHEMA.md`  
**Immediate POC:** GitHub Issue #2 + `RUNTIME_VALIDATION.md`

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

## 1.1 Post-review implementation posture

An independent design review identified a useful distinction:

```text
accepted scientific/design semantics
            !=
Factorio-specific implementation hypotheses already proven at runtime
```

The scientific contract remains accepted, but the first coding work must execute `docs/RUNTIME_VALIDATION.md` against Factorio 2.0.77.

If a runtime assumption fails, preserve evidence and either choose another implementation or propose a superseding ADR. Do not silently weaken measurement semantics.

## 1.2 Immediate POC is deliberately narrow

The first POC is **not full v1**.

It is successful when a user can:

1. validate/compile one real scenario;
2. launch a real Factorio 2.0.77 local-server experiment;
3. visibly move a conserved workpiece through normal Factorio inserter/belt/assembler mechanics;
4. produce exact source admissions and completion transactions;
5. obtain exact conservation-ledger WIP with independent physical-census validation;
6. compute average WIP, throughput, and Little's-Law-derived cycle time over matching windows;
7. receive a reproducible run dataset/report;
8. reset to the pristine baseline and repeat;
9. run a human-playable Lab 3 / Little's Law exercise end-to-end.

Demand/service, visibility enforcement, objective scoring, full capstone entity-set behavior, and polished Labs 0–2/4–6 remain full-v1 requirements but are intentionally deferred from the first vertical slice.

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

The immediate implementation should prove the laboratory using Lab 3 before building every later course feature.

---

# 4. Users

## 4.1 Learner

Needs to:

- launch/connect to a scenario;
- understand the task and experiment state;
- play Factorio normally;
- see only allowed live metrics/objective information where implemented;
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
- verify runtime assumptions against pinned Factorio versions;
- write headless integration fixtures;
- add new adapters/schedules/metrics without breaking accepted semantics.

---

# 5. Full v1 scope

Full v1 MUST provide:

1. Python scenario schema/compiler.
2. Python CLI/controller.
3. Local Factorio server orchestration with RCON control.
4. Graphical Factorio client connection for interactive runs.
5. FISL core Factorio mod in Lua.
6. Generic hardened FISL source/sink apparatus.
7. Exact experiment time/phases.
8. Rectangular zones and one primary zone per system.
9. Dynamic entity sets.
10. Source/sink port settlement.
11. Replenish and constant scheduled supply.
12. Zero/finite/unbounded external supply storage.
13. FIFO backlog customer demand.
14. Primitive scientific observations + ordered event stream.
15. Conserved-work-unit WIP using ADR 0017 conservation-ledger authority plus physical census validation/decomposition.
16. Throughput and boundary rates.
17. Crafting-machine state classification.
18. Customer on-time item service.
19. Little's-Law-derived cycle time + controlled probe method support.
20. Exact aggregation/window semantics.
21. Learner/instructor/debug disclosure rules.
22. Requirement/preference objectives.
23. Reproducible run datasets/manifests with separate `ResolvedScenario` and `RunConfiguration`.
24. Baseline reset/retry.
25. Headless deterministic integration tests.
26. Scenario support sufficient for Factory Physics Labs 0–6.

The fact that an item belongs to full v1 does not mean it belongs to the first POC issue.

---

# 6. Explicit v1 non-goals

Do NOT expand the implementation into these areas unless needed to complete a v1 contract requirement:

- stochastic demand/supply;
- equipment failure/repair simulation;
- economics/cost accounting;
- quality/yield/rework modeling beyond declared v1 loss boundaries;
- organizational roles/VSM;
- differential-information multiplayer experiments;
- arbitrary per-item digital identity through production recipes;
- train/logistic-robot physical census/decomposition as a canonical requirement;
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

`docs/RUNTIME_VALIDATION.md` defines the initial empirical gate.

The run manifest records the actual Factorio version.

---

# 8. Technology choices

## 8.1 Python controller/compiler

Use Python 3.12+.

Preferred libraries/approach:

```text
Pydantic 2.x     typed author/resolved/run schema validation
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
JSON   stable ResolvedScenario, per-run RunConfiguration, manifest, summary
JSONL or equivalent lossless stream encoding   authoritative telemetry/events
Markdown optional generated human report
```

Do not equate “authoritative telemetry” with one verbose JSON record for every unchanged object every tick. Exact counters, state-change intervals, run-length encoding and batching are allowed when scientifically lossless.

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

Canonical interactive POC profile follows ADR 0018:

```text
pause_policy = prohibited
server incidental zero-player auto-pause = disabled
unexpected required learner disconnect while RUNNING = abort + preserve data
```

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
│   ├── RUNTIME_VALIDATION.md
│   ├── POST_REVIEW_REVISIONS.md
│   ├── SCENARIO_MEASUREMENT_CONTRACT.md
│   └── adr/
├── python/
│   └── fisl/
│       ├── __init__.py
│       ├── cli.py
│       ├── scenario/
│       │   ├── author_models.py
│       │   ├── resolved_models.py
│       │   ├── run_models.py
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
│   │       ├── census.lua
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
│       ├── fp03-littles-law/
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
- canonical stable `ResolvedScenario` JSON/hash;
- per-attempt `RunConfiguration` construction;
- reproducibility fingerprint construction;
- Factorio process/server lifecycle;
- RCON protocol;
- run directory/manifest;
- telemetry collection/validation;
- authoritative post-run derived reporting where retained data permit recomputation;
- later comparison tools.

## 10.2 Lua answers

> What is happening in Factorio right now?

Lua owns:

- authoritative simulation tick/phase state;
- clean start/transition/end boundaries;
- runtime world bindings;
- source/sink settlement;
- supply/demand processes;
- dynamic entity-set membership where required;
- authoritative conservation-ledger state for conserved-flow WIP;
- physical census snapshots/decomposition where required;
- machine progress/state-classification inputs;
- exact streaming accumulators needed during the live run;
- objective state required in-game when implemented;
- learner UI;
- authoritative telemetry/event emission.

Lua does **not** need a production implementation of every post-run statistic merely because Python can compute it later.

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
- conservation-ledger WIP on a flow that cannot satisfy ADR 0017 conservation assumptions;
- Little's-Law CT with mismatched WIP/TH flow/window;
- throughput using non-sink completion interfaces;
- unqualified percentile weighting;
- bare utilization denominator;
- service cohort/horizon whose end is before the latest selected cohort deadline;
- objective threshold incompatible with metric dimension.

The service rule is the direct property:

```text
observation_horizon_end >= latest_selected_cohort_deadline
```

No arbitrary extra-tail heuristic is required.

## FR-SCHEMA-006 — Observation-plan compiler

Derive the primitive/runtime instrumentation required by declared metrics/objectives/live UI.

Do not force scenario authors to manually enumerate primitive measurements.

## FR-SCHEMA-007 — Stable `ResolvedScenario`

Generate a typed run-independent object containing explicit:

```text
ticks
windows
rational schedules
normalized capacities
resolved cross-references
metric/observation/objective/visibility semantics
semantic schema/compiler/protocol versions
```

It MUST NOT contain `run_id` or the actual execution seed.

## FR-SCHEMA-008 — `RunConfiguration`

Generate a separate per-attempt object containing at least:

```text
run_id
resolved_scenario_hash
actual experiment_seed
execution mode / behavior-affecting run profile
protocol envelope version
```

## FR-SCHEMA-009 — Canonical serialization/hash/fingerprint

Generate:

```text
canonical ResolvedScenario JSON
resolved_scenario_hash
run configuration
reproducibility fingerprint
```

where the fingerprint includes actual seed/environment but excludes `run_id`.

## FR-SCHEMA-010 — JSON Schema

Expose generated JSON Schema or equivalent machine-readable authoring contract for tooling/editor support.

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
metric summary
resolved_scenario_hash
```

## FR-CTRL-003 — Run creation

`fisl run <scenario>` must eventually:

1. validate/compile;
2. allocate unique run ID/workspace;
3. hash/verify baseline;
4. write `scenario.resolved.json`;
5. create `run-config.json` with actual seed/run profile;
6. write initial manifest;
7. allocate local game/RCON ports and RCON password;
8. launch Factorio server against a working baseline copy;
9. wait for RCON/runtime readiness;
10. negotiate protocol;
11. upload/verify resolved configuration/run envelope;
12. wait for Lua `READY`;
13. launch/connect graphical client unless headless;
14. monitor run lifecycle;
15. collect output artifacts;
16. finalize manifest/summary/report.

## FR-CTRL-004 — Local networking safety

Default RCON binds loopback.

Generate random per-run credentials.

Do not store RCON password in learner-facing reports or scientific telemetry.

## FR-CTRL-005 — Interactive connection profile

For canonical interactive POC:

- disable incidental/zero-player server auto-pause;
- require the learner connection while RUNNING;
- unexpected disconnect emits an authoritative event and aborts while preserving data.

See ADR 0018 / RV-011.

## FR-CTRL-006 — Headless mode

`fisl run ... --headless` must run the same authoritative server/config/runtime without a graphical client and support deterministic integration fixtures.

Headless mode explicitly disables the required-learner-connection rule.

## FR-CTRL-007 — Retry/reset

Provide a simple workflow such as:

```text
fisl retry <run_id>
```

or equivalent.

Retry always reloads the declared immutable baseline and creates a new run ID.

Unchanged resolved semantics retain the same `resolved_scenario_hash`; unchanged controlled inputs/environment may retain the same reproducibility fingerprint.

## FR-CTRL-008 — Report

Provide:

```text
fisl report <run_id>
```

that displays final metric values, coverage/validity, protocol flags, hashes, and relevant method/window metadata.

For the first POC this command is required.

## FR-CTRL-009 — Compare

Full v1 should provide:

```text
fisl compare <run-a> <run-b> [...]
```

The comparison must:

- warn about incompatible reproducibility/metric semantics;
- show requirement status;
- compare preference metrics;
- avoid inventing a scalar score.

`fisl compare` is explicitly deferred from the first vertical-slice issue.

---

# 13. Controller ↔ Lua protocol

Follow ADR 0015.

Required behavior for v1:

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

The transferred runtime envelope contains the stable resolved semantics plus separate run configuration; the stable hash applies only to the `ResolvedScenario`.

Interactive mode should normally allow the learner to start from the in-game READY screen rather than starting before the client connects.

The protocol transport is low-volume RCON. It never owns experiment timing.

RCON chunking must be validated by RV-008 before becoming load-bearing. A generated companion configuration mod is recorded in RV-010 as a fallback only if the real spike shows RCON transfer is materially inferior.

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
- resolve hardened port bindings;
- validate surfaces/zones;
- validate required prototypes/recipes;
- initialize entity selectors needed by the scenario;
- validate no stale active run state;
- initialize fresh ledgers/seed/sequence counters;
- perform initial physical WIP census for conserved-ledger flows;
- establish/validate `initial_WIP` (canonical baselines SHOULD normally be zero).

## FR-LIFE-002 — Start boundary

Start request becomes pending.

Lua begins experiment at next eligible clean simulation boundary and records `experiment_start_map_tick`.

## FR-LIFE-003 — Completion

At exclusive final boundary:

1. settle final interval;
2. update final ledger transactions;
3. capture required closing observations/final census;
4. finalize accumulators/objectives implemented by the scenario;
5. evaluate residual manual-carriage diagnostics/validity;
6. emit completion records;
7. enter COMPLETED;
8. pause/freeze continued drift where practical after scientific finalization;
9. allow final save capture.

No next-interval supply/demand should be created after experiment completion.

## FR-LIFE-004 — Abort

Abort preserves/flushes data and reason.

Do not erase run state.

Unexpected required-learner disconnect in the canonical interactive profile follows this path.

---

# 15. Authoritative tick pipeline

Implement ADR 0004 ordering as clarified by ADR 0017.

At checkpoint `T`:

1. ingest queued Factorio sensor events;
2. update/reconcile dynamic entity membership needed by the scenario;
3. settle physical interval `[T-1,T)` ports/activity;
4. emit exact interval primitive facts;
5. apply admission/completion/loss transactions to conserved WIP ledger;
6. if final boundary, finalize/complete rather than prepare another interval;
7. apply phase transition if boundary;
8. advance external supply/demand for `[T,T+1)`;
9. apply FISL-controlled source staging/replenishment mutations;
10. run integrity/protocol checks;
11. emit prepared ledger point state `WIP(T)` and other declared point observations;
12. run physical WIP census when its declared cross-check cadence is due;
13. record census agreement/discrepancy/coverage state without silently reconciling the ledger;
14. update exact runtime accumulators/minimal live UI state;
15. commit ordered/losslessly encoded telemetry batch.

Any implementation optimization must preserve these observable semantics.

Factorio event handlers act as sensors. They should not independently mutate authoritative experiment ledgers outside the coordinator except where unavoidable and explicitly normalized.

---

# 16. Ports and schedules

Follow ADR 0003 as strengthened for conserved-ledger flows by ADR 0017.

## FR-PORT-001 — Generic hardened apparatus

Provide visually distinct generic source and sink port prototypes suitable for automation by intended inserters/belts while protected from ordinary learner mining/destruction/manual inventory interaction.

For canonical conserved-ledger WIP these protections are load-bearing, not optional polish.

Where Factorio permits, standard apparatus MUST:

- be non-minable by learners;
- be non-destructible in normal scenario operation;
- be non-operable for direct player inventory interaction;
- enforce/filter declared material identity;
- expose only the intended transfer role/direction;
- make reverse transfer structurally difficult/impossible;
- surface detectable contamination/reverse-flow evidence.

Tag/mark ports as FISL apparatus.

## FR-PORT-002 — Binding

Resolve configured surface + position + expected prototype to exactly one endpoint during READY.

Record runtime entity ID/prototype/capacity in provenance.

Fail READY if canonical ledger apparatus cannot satisfy required one-way binding/protocol assumptions.

Loss of an authoritative port endpoint during RUNNING aborts rather than silently continuing.

## FR-PORT-003 — Source settlement

Measure input as documented net withdrawal from source staging.

For a conserved flow this exact normalized withdrawal is the admission transaction used by the WIP ledger.

Detect reverse flow as a protocol violation; RV-002 validates the standard apparatus against masked reverse-transfer risk.

## FR-PORT-004 — Sink settlement

Record tracked material as `sink_delivery`, remove/accept it, and return standard sink staging to empty each settlement.

For a completion port, normalized `sink_delivery` is the ledger completion transaction.

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

Full v1 supports:

```text
capacity = 0
capacity = finite integer
capacity = unbounded
```

Track pending quantity and loss when overflow exceeds configured storage.

These variants are deferred from the first POC unless needed by a runtime spike.

## FR-PORT-009 — Demand cohorts

Full v1 generates FIFO age cohorts for demand-created quantity.

Fulfillment allocates oldest-first and retains created tick/fulfilled tick/quantity.

Demand/service implementation is deferred from the first POC.

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

Full v1 implements ADR 0016 dynamic selectors.

A machine built during run joins at first canonical eligible interval; removed machine leaves future intervals.

Maintain eligibility intervals for pooled machine-time.

Only the entity-set behavior required by the first fixture is needed in Issue #2; capstone dynamic-redesign coverage comes later.

## FR-SET-002 — Overlap

Allow an entity to belong to multiple analytical sets.

---

# 18. WIP implementation

Follow ADR 0005 for dimensional/conserved-flow meaning and ADR 0017 for authoritative total-WIP implementation.

## FR-WIP-001 — Physical inventory vs WIP

Never sum unlike arbitrary Factorio items and label the result scalar WIP.

## FR-WIP-002 — Conserved flow mapping

Implement exact material→work-unit coefficients.

Canonical Factory Physics workpiece family uses 1:1 stage transformations.

## FR-WIP-003 — Authoritative conservation ledger

For a validated conserved flow:

```text
WIP(T)
  = initial_WIP
  + cumulative_admissions
  - cumulative_completions
  - cumulative_declared_losses
```

The ledger produces the authoritative prepared-boundary total `WIP(T)` each tick.

It MUST NOT depend on scanning every belt/machine/inserter every tick.

## FR-WIP-004 — READY initial census

Before READY, physically census tracked internal work and establish `initial_WIP`.

Canonical teaching baselines SHOULD normally establish:

```text
initial_WIP = 0
```

A nonzero initial state must be explicit and unambiguous.

## FR-WIP-005 — Required physical cross-check/decomposition census

A physical census independently validates/decomposes ledger WIP.

Initial canonical cadence:

```text
60 simulation ticks
```

Census adapters should cover the holders needed by the canonical fixture, including:

```text
internal containers/process inventories
active craft occupancy
unique belt/underground/splitter transport lines
inserter held stack
dropped tracked item entities
player-held tracked work
```

This census is required at READY and final boundary as well as the periodic cadence.

## FR-WIP-006 — No silent ledger/census reconciliation

When complete census differs from ledger beyond exact declared tolerance:

```text
wip_census_discrepancy = census - ledger
```

- preserve both values;
- keep ledger as recorded total-WIP authority;
- emit a first-class discrepancy event;
- conservatively mark the WIP-validity uncertainty interval since the prior successful cross-check when failure onset is unknown;
- strict metrics overlapping that interval become incomplete/flagged.

Do not overwrite ledger state from census automatically.

## FR-WIP-007 — Player carriage

Already-admitted tracked work in player inventory remains ledger WIP.

Transient carriage during legitimate redesign is diagnostic rather than automatic WIP-coverage failure.

Measure/report relevant diagnostics such as:

```text
manual_carriage_wip_current
manual_carriage_wip_item_ticks
manual_carriage_event
```

Tracked player-held work remaining at final boundary emits `manual_carriage_residual` and flags canonical experiment validity for comparisons/objectives requiring normal production flow.

## FR-WIP-008 — Belt/active-craft adapters

Belt deduplication and active-craft occupancy remain required for physical census/decomposition fixtures and runtime validation.

They are **not** authoritative every-tick total-WIP sources for conserved flows.

## FR-WIP-009 — Undeclared loss/destruction

If admitted tracked work disappears without a declared exact loss transaction, the next complete census should expose a ledger discrepancy.

Do not infer/patch a loss silently.

## FR-WIP-010 — Census validation provenance

Every WIP result retains at least:

```text
method = conservation_ledger
flow ID
initial WIP
admission/completion/loss methods
cross-check cadence
last successful census
census discrepancy/coverage events
strict validity coverage
```

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

RV-006/RV-007 empirically validate the Factorio progress/brownout assumptions before the classifier becomes load-bearing.

The runtime spike should collect enough raw evidence to validate this design, but full machine-state UI/aggregation is not required to complete the first Lab 3 vertical slice.

---

# 20. Metric engine requirements

Use this authority split:

```text
Lua
  authoritative simulation-time/boundary facts
  conservation ledger
  exact live/runtime accumulators actually needed during execution
  minimal live UI/objective values

Python
  authoritative post-run derived reporting/analysis where retained facts permit recomputation
  formatted report generation
  later cross-run comparison
```

Do not build two full metric engines merely to prove equivalence.

## FR-METRIC-001 — WIP point metric

Prepared state at `T` describes interval `[T,T+1)`.

Canonical conserved-flow method is `conservation_ledger` under ADR 0017.

## FR-METRIC-002 — WIP integration

For `[A,B)`:

```text
wip_unit_ticks = sum T=A..B-1 ledger_WIP(T)
average_wip = wip_unit_ticks / (B-A)
```

This is exact tick integration; the 60-tick census cadence does not create a sample-and-hold approximation in total WIP.

## FR-METRIC-003 — Throughput

```text
completion flow units in [A,B) / simulation duration
```

Numerator is normalized completion-sink `sink_delivery`.

No bare instantaneous throughput.

## FR-METRIC-004 — Service

Full v1 canonical service:

```text
on_time_item_rate = on-time quantity / created quantity
```

for demand cohorts created in an explicit cohort window and fully observed through deadlines.

Deferred from the first POC.

## FR-METRIC-005 — Demand wait distributions

Weight waits by demanded quantity.

Deferred from the first POC.

## FR-METRIC-006 — Cycle time

Canonical continuous method:

```text
CT_LL = average WIP / throughput
```

with same flow and same analysis window.

Method metadata must say `little_law_derived`.

Support an isolated `single_work_unit_probe` method later under explicit isolation guarantees.

## FR-METRIC-007 — State durations

Use classified one-tick intervals, not raw point status.

## FR-METRIC-008 — No bare utilization

Any state fraction must name its denominator.

## FR-METRIC-009 — Percentiles

Use weighted nearest-rank empirical quantile.

No implicit library interpolation.

## FR-METRIC-010 — Missing coverage / validity

Strict by default. Missing/invalid coverage does not become zero or silently shrink denominator.

Partial diagnostic values may be emitted only with explicit coverage metadata.

Ledger/census discrepancy uncertainty intervals participate in WIP validity.

## FR-METRIC-011 — Empty populations

Produce `undefined/no_data`, not zero or 100%.

---

# 21. Objectives

Follow ADR 0012 for full v1.

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

The full objective engine is deliberately deferred from the first Lab 3 vertical slice.

---

# 22. In-game GUI requirements

Keep the GUI small and Factorio-native.

## First POC READY panel

Show at least:

```text
scenario title
short task/instruction
run status READY
Start Experiment button (interactive mode)
```

## First POC RUNNING panel

Show at least:

```text
current phase
simulation elapsed/remaining time
current WIP / simple throughput if useful
```

Do not make polished disclosure/objective UI a blocker for Lab 3.

## Full-v1 disclosure

Later implement ADR 0011:

```text
learner_live
learner_post_run
instructor
debug
```

UI refresh cadence may be lower than scientific sampling cadence.

Do not build a web dashboard in v1.

---

# 23. Visibility

Follow ADR 0011 for full v1.

Visibility must never change collection or scientific calculation.

Visibility contributes to resolved experiment identity because disclosure can affect learner behavior.

V1 disclosure is pedagogical, not cryptographic protection from a user with local filesystem access.

Only minimal POC status/report UI is required before the first Lab 3 test.

---

# 24. Telemetry and run artifacts

## 24.1 Run directory

Required target:

```text
runs/<run_id>/
  manifest.json
  scenario.resolved.json
  run-config.json
  telemetry.jsonl        # or equivalent transparent/lossless authoritative encoding
  events.jsonl           # may be combined with telemetry if schema remains explicit
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

Authoritative scientific data MUST preserve enough information to recover:

```text
run ID / resolved scenario identity
schema version
experiment/map ticks as appropriate
ordered FISL sequence/event identity
observation/event type
subject/port/entity ID where applicable
quantity/value/unit
measurement method
interval/boundary semantics
validity/census information
```

## 24.3 Storage optimization

Prefer semantically lossless strategies such as:

- exact streaming counters/accumulators;
- state-change/run-length intervals;
- batched records;
- periodic physical census snapshots where the scientific method itself is periodic.

Do not emit millions of redundant records solely to mimic a logical tick series physically.

Python must retain enough authoritative data/exact accumulators to reproduce the reported v1 POC metrics.

RV-009 sizes/profiles this strategy against the real Factorio runtime.

## 24.4 Lua output

Use Factorio-supported `script-output` file writing for authoritative streams unless runtime validation demonstrates a better equivalent mechanism.

The Python controller collects/tails these files.

Live RCON responses are not the only scientific record.

---

# 25. Provenance / manifest

Implement revised ADR 0013.

Required manifest identity includes:

```text
run_id
spec version
scenario ID/version
scenario source hash
resolved_scenario_hash
actual experiment seed
baseline save hash
actual Factorio version
FISL core mod version/commit
controller/compiler version/commit
mod manifest
behavior-affecting run profile
reproducibility fingerprint
protocol version
start/end map ticks
experiment duration ticks
completion/abort status
protocol/coverage/WIP census-validity summary
artifact inventory/checksums
```

Every run stores both:

```text
scenario.resolved.json
run-config.json
```

`resolved_scenario_hash` excludes `run_id` and actual seed.

Reproducibility fingerprint includes actual seed/environment/run profile and excludes `run_id`.

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

The first POC must demonstrate retry/reset before expanding scope.

---

# 27. Factory Physics content mod

Create a small `fisl-factory-physics` content mod distinct from core runtime when practical.

It should initially provide purpose-built workpiece item/recipe families for rigorous conserved-flow labs.

The POC can start with the smallest family needed for one 1:1 assembly step, for example:

```text
fisl-rough-workpiece
  -> fisl-finished-workpiece
```

Full course content may later use:

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

Do not require all seven polished course baselines before proving the platform.

The first required human-facing scenario is Lab 3 / Little's Law, supported by smaller synthetic runtime fixtures.

---

# 29. Testing and runtime-validation strategy

Testing is a product requirement, not cleanup work, because scientific semantics depend on Factorio-specific behavior.

## 29.1 Runtime-validation spike comes first

Execute `docs/RUNTIME_VALIDATION.md` against Factorio 2.0.77 before substantial framework construction.

The one-workpiece vertical fixture should validate as much as possible in one real scenario:

```text
source -> inserter -> belt/underground/splitter -> inserter
       -> assembler 1:1 recipe -> inserter -> sink
```

At minimum Issue #2 targets RV-001 through RV-006, RV-008, RV-009 and RV-011 as applicable.

Record empirical evidence, not only mock tests.

## 29.2 Python unit tests

Initial POC unit tests:

- duration/rate parsing;
- `ResolvedScenario` canonical hash stability;
- `RunConfiguration` separation;
- reproducibility fingerprint exclusion of run ID;
- cross-reference validation;
- exact WIP integration;
- throughput arithmetic;
- Little's-Law compatibility;
- exact census-discrepancy validity logic.

Full v1 later adds:

- weighted nearest-rank quantiles;
- service cohort allocation;
- objective status;
- compare compatibility logic.

## 29.3 Pure logic Lua tests where practical

Keep modules such as rational schedule accumulators, ledgers, and validity state isolated enough to test outside Factorio when practical.

Do not treat mock tests as sufficient for Factorio entity behavior.

## 29.4 Factorio integration fixtures

Immediate POC fixtures:

1. clock/phase boundary;
2. source/sink settlement;
3. conserved ledger WIP;
4. physical census agreement;
5. deliberate ledger/census discrepancy;
6. belt transport-line deduplication census;
7. active-craft census continuity;
8. raw craft-progress/completion evidence;
9. RCON/config transfer;
10. telemetry/profile sizing;
11. interactive auto-pause/disconnect behavior;
12. reset/provenance.

Full v1 later adds the remaining fixture suite from `FACTORY_PHYSICS_LABS_V1.md`, including service, visibility, objectives and capstone dynamic entity sets.

## 29.5 Golden scientific result tests

For deterministic fixtures, store expected exact values such as:

```text
source withdrawals/admissions
sink deliveries/completions
ledger WIP point states
WIP unit-ticks
census check states/discrepancies
throughput numerator/window ticks
cycle-time numerator/denominator dependencies
```

Do not golden-test only formatted decimals.

## 29.6 Runtime version tests

Run Factorio-specific adapter fixtures against every Factorio patch version FISL claims to support.

Unknown raw statuses should cause classifier coverage failure rather than silently falling back.

---

# 30. Performance requirements

FISL must not make ordinary small/medium teaching factories unplayable.

No fixed UPS budget is asserted before profiling, but implementation must observe these principles:

- do not scan the whole world unnecessarily;
- conservation-ledger total WIP must not require every-tick full physical holder scans;
- physical WIP census starts at a 60-tick validation cadence and is profiled/tuned explicitly;
- maintain entity membership incrementally where useful;
- deduplicate belt transport lines for census;
- use exact streaming accumulators for high-frequency quantities;
- avoid filesystem writes for every unchanged low-level object when a lossless interval/change representation is equivalent;
- keep UI refresh slower than scientific state updates when useful;
- expose profiler/debug metrics to developers but not learners by default.

RV-009 records UPS, telemetry bytes/minute, write behavior and census cost for the first real fixture.

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
port apparatus cannot satisfy canonical one-way ledger assumptions
missing required item/recipe prototype
invalid metric compatibility
initial WIP cannot be established
```

Do not start the experiment.

## Runtime protocol/coverage/validity facts

Examples:

```text
boundary straddle
source reverse flow
unknown machine status
wip_census_discrepancy
wip_census_coverage_incomplete
manual_carriage_wip
manual_carriage_residual
missing holder adapter for a required census
prohibited pause / interactive disconnect
```

Preserve data and flag validity according to the relevant ADR.

Abort only when continued execution would be misleading or violates the canonical run profile, such as losing an authoritative port endpoint or required learner connection.

Missing measurement is never silently zero.

A census discrepancy never silently rewrites the conservation ledger.

---

# 32. CLI usability target

The exact syntax may evolve.

## First POC happy path

```text
$ fisl validate scenarios/factory-physics/fp03-littles-law/scenario.yaml
Scenario valid
Factorio target: 2.0.77
Resolved scenario: sha256:...

$ fisl run scenarios/factory-physics/fp03-littles-law
Run: 01...
Server ready
Launching Factorio client...

# learner plays small Little's Law experiment

Run completed
Average WIP: ... workpieces
Throughput: ... workpieces/min
Cycle time (Little's Law derived): ... s
WIP census validation: PASS

$ fisl report 01...
...

$ fisl retry 01...
...
```

The user should not need to manually manage server/RCON processes for normal operation.

Full v1 later adds richer service/objective output and `fisl compare`.

---

# 33. Immediate POC definition of done

GitHub Issue #2 is authoritative for the detailed live checklist.

The first POC is complete when these major conditions are true:

1. Relevant `RUNTIME_VALIDATION.md` assumptions have been tested against real Factorio 2.0.77 and evidence recorded.
2. `fisl validate` parses real authoring YAML and creates stable canonical `scenario.resolved.json` + `resolved_scenario_hash`.
3. A separate `run-config.json` binds a unique run ID, actual seed and interactive/headless run profile to that resolved scenario.
4. `fisl run` launches a local Factorio server from an immutable baseline working copy and verifies RCON configuration transport.
5. Interactive mode connects a graphical client, disables incidental server auto-pause and aborts/preserves data on unexpected required-learner disconnect.
6. Start occurs on an authoritative clean simulation tick.
7. Hardened generic source/sink apparatus performs deterministic settlement.
8. One conserved workpiece visibly travels through ordinary Factorio inserter/belt/assembler mechanics.
9. Source withdrawal creates exact ledger admission and sink delivery creates exact completion.
10. `conservation_ledger` WIP remains exactly one after admission and before completion for the one-workpiece fixture.
11. READY/final/60-tick physical censuses agree with the ledger in the canonical fixture.
12. A deliberate mismatch fixture proves discrepancy is flagged, ledger is not reconciled, and strict validity is conservatively marked.
13. Player-held admitted work remains ledger WIP; final residual player-held work produces the declared validity flag.
14. Average WIP is exact tick integration of ledger WIP.
15. Throughput uses completion-port delivery over the matching measured window.
16. Little's-Law-derived cycle time uses matching WIP/throughput and is labeled `little_law_derived`.
17. The run directory contains manifest, `scenario.resolved.json`, `run-config.json`, authoritative telemetry/events and summary.
18. `fisl report` explains metric method/window/exact numerator-denominator/validity provenance.
19. Retry reloads the pristine baseline, creates a new run ID and preserves stable resolved-scenario identity where appropriate.
20. A human can run one actual Lab 3 / Little's Law scenario end-to-end.

Explicitly deferred from this POC:

```text
demand/service cohorts
full visibility enforcement
objective engine
external-supply storage variants unless required by spike
full capstone dynamic entity-set behavior
polished Labs 0–2 / 4–6
fisl compare
web/database/dashboard work
```

The first POC earns the right to proceed to the rest of v1; it is not a synonym for v1.

---

# 34. Full v1 definition of done

V1 is ready for course use when:

- the narrow POC/Lab 3 vertical slice passes against the real runtime;
- the full deterministic integration fixture suite from `FACTORY_PHYSICS_LABS_V1.md` passes;
- service/visibility/objective features required for Labs 5–6 are implemented;
- all metric results preserve method/window/coverage/validity provenance;
- Python can recompute/verify final scientific summaries from retained run data as designed;
- controller error handling/reset is reliable enough for repeated classroom use;
- baseline/scenario versioning and revised hashing/fingerprinting work;
- at least Labs 0–6 can be instantiated without lab-specific runtime code;
- representative course scenarios have been calibrated so their intended conceptual phenomena are visible;
- README/user docs explain installation, `validate`, `run`, `retry`, `report`, and eventual `compare`.

---

# 35. Open implementation choices Codex may decide

Codex should make reasonable engineering choices and record ADRs if any choice changes architectural/scientific behavior.

Implementation choices intentionally left open include:

- exact Python package manager/build tooling;
- exact YAML parser;
- third-party Source-RCON library vs small internal client;
- exact run-ID implementation (ULID vs UUIDv7);
- exact canonical JSON library/settings, provided deterministic hashing is tested;
- exact Lua module split;
- exact custom source/sink art/prototype base;
- exact lossless telemetry compression strategy;
- exact Rich CLI presentation;
- exact local server/client port allocation strategy;
- exact Git LFS policy for saves;
- implementation sequence inside the Issue #2 vertical slice.

Accepted ADRs define intended semantics, but Factorio-specific assumptions marked Pending must be empirically validated.

If an assumption fails:

1. document the actual runtime evidence;
2. prefer another implementation if the semantic remains feasible;
3. propose a new/superseding ADR if the semantic itself must change.

Do not contort around an impossible runtime assumption, and do not silently weaken the contract.

---

# 36. Source-of-truth hierarchy

When implementation questions arise, use this order:

1. Later Accepted/superseding ADRs in `docs/adr/` — specific scientific/architectural decisions.
2. `docs/FISL_V1_SCHEMA.md` — current scenario/compiler/runtime-identity contract.
3. `docs/RUNTIME_VALIDATION.md` — empirical status and required Factorio validation spikes.
4. GitHub Issue #2 — **immediate POC scope only**.
5. `docs/POST_REVIEW_REVISIONS.md` — review-cycle summary/explicit supersessions.
6. This PRD — full-v1 product/runtime requirements.
7. `docs/ARCHITECTURE.md` — broader rationale/long-term direction.
8. `docs/FACTORY_PHYSICS_LABS_V1.md` — course-level validation and integration scenarios.
9. `docs/RESEARCH_NOTES.md` — intellectual/research provenance.

If two documents conflict, later accepted ADRs supersede earlier illustrative examples.

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
0017 Conservation-Ledger WIP and Physical Census Semantics
0018 Local-Server Pause and Disconnect Profile
```

Codex should read the corresponding ADR before implementing a subsystem and consult `RUNTIME_VALIDATION.md` for Factorio-specific assumptions still marked pending.

---

# 38. Closing product definition

The v1 system should make this statement true:

> A FISL scenario can take a known Factorio world, declare a controlled deterministic experiment around it, let a human modify the factory using normal Factorio mechanics, and produce an auditable/reproducible scientific record of how the production system behaved.

The first proof of that statement is intentionally small: one conserved workpiece flow and one Little's Law lab running against the real Factorio runtime.

The durable engineering artifact is the laboratory platform and its scenario contract—not one course script or one hard-coded factory.
