# Factorio Industrial Systems Laboratory (FISL)

## Architecture and Design Rationale

**Status:** Foundational architecture document  
**Initial target:** Factory Physics education  
**Long-term target:** Extensible experimental environment for operations, variability/control, and organizational cybernetics  

---

## 1. Purpose

The **Factorio Industrial Systems Laboratory (FISL)** is an experimental layer built on top of Factorio.

Its purpose is not to replace Factorio mechanics with educational abstractions. Factorio already provides an unusually rich model of physical production: machines, recipes, belts, buffers, rail, power, logistics, construction, circuit networks, and production statistics.

FISL exists because serious teaching and research require capabilities that vanilla Factorio either does not provide, keeps effectively constant, or exposes in a form that is not sufficiently controlled or reproducible.

The foundational rule is:

> **Use Factorio to model the system. Use FISL to model the experiment.**

This distinction should govern architecture, pedagogy, and implementation.

Examples:

- If the learner needs more buffer capacity, they should build a Factorio chest or storage system.
- If the learner needs greater production capacity, they should build more machines.
- If the learner needs a feedback controller, they should use Factorio's native circuit-network mechanics whenever those mechanics represent the concept adequately.
- If the instructor needs demand to be exactly 60 units/minute, or to change at minute 10, that belongs to FISL.
- If the experiment needs machine failures, stochastic supply, information delay, a service-level objective, or reproducible telemetry, that belongs to FISL.

FISL should therefore feel like **Factorio with a laboratory bench attached**, not like a separate educational game rendered inside Factorio.

---

## 2. Why FISL Is Necessary

Factorio is particularly strong for teaching deterministic production systems, but gameplay makes several assumptions that become limitations for serious instruction.

Vanilla Factorio tends to assume or encourage a world in which:

- machine behavior is deterministic;
- recipe yields and processing rates are known;
- equipment does not randomly fail;
- supply does not arrive according to an instructor-defined stochastic process;
- customer demand is not an explicit external process;
- most system information is immediate and accurate;
- player visibility is broad;
- inventory and spare capacity have no explicit economic carrying cost;
- controlled experiment reset/replay is not the primary usage model;
- arbitrary educational metrics are not defined with scientific measurement semantics.

For introductory Factory Physics, many of these assumptions are helpful. They give us a clean world in which students can learn flow, capacity, bottlenecks, WIP, Little's Law, starvation, blocking, pull systems, and system optimization.

For later work, however, we need to selectively relax those assumptions.

FISL exists to make the assumptions **controllable experimental variables**.

---

## 3. Pedagogical Thesis

The core educational idea is **scenario before theory**.

Rather than beginning with a definition or equation and then searching for an example, the learner first encounters a deliberately constructed production problem in Factorio.

The intended sequence is:

1. Encounter the system behavior.
2. Attempt to diagnose or improve it.
3. Observe measurable consequences.
4. Introduce the formal concept or theory.
5. Re-run or redesign the system using the new conceptual tools.
6. Compare results and explain why they changed.

For example, rather than beginning with the Theory of Constraints, a learner may first encounter a factory whose local machine upgrades produce almost no system-level throughput improvement. The learner experiences the failure of local optimization before receiving the vocabulary for bottlenecks and constraints.

Similarly, the later variability course should first let the learner construct an elegant deterministic factory and then introduce variability so that the previously optimal design becomes brittle.

This is the project’s most important pedagogical principle. The course content exists to structure experiences in the laboratory; FISL exists to make those experiences controlled and reproducible.

---

## 4. Intellectual Scope: Three Layers of Work

The project began as a broad idea connecting Factorio to industrial management, organizational management, and cybernetics. Deeper analysis suggests these are not one course. They should be treated as progressively more ambitious layers.

### 4.1 Layer I — Factory Physics Through Factorio

This is the first and most immediately buildable curriculum.

It focuses on concepts Factorio already represents well:

- stocks and flows;
- rates and conservation;
- capacity;
- utilization;
- bottlenecks and constraints;
- throughput;
- work in process (WIP);
- cycle time;
- Little's Law;
- starvation and blocking;
- buffers and decoupling;
- push and pull;
- demand signaling;
- Kanban/WIP limits;
- production balancing;
- logistics and material handling;
- modularity, standardization, and interfaces;
- measurement and instrumentation;
- local versus global optimization;
- robustness and redundancy.

This layer should remain mostly deterministic.

### 4.2 Layer II — Variability, Control, and Cybernetic Systems

The second layer focuses on what vanilla Factorio largely **hides** by keeping it constant.

The central pedagogical move is:

> Optimize the deterministic factory; then introduce variability and observe the consequences.

Possible future disturbances include:

- stochastic demand;
- supply variation;
- transport delay;
- equipment failure and stochastic repair time;
- yield or quality variation;
- delayed information;
- resource shocks;
- changing priorities.

A key theoretical spine is the **Variability Buffering Law**: variability must ultimately be buffered using some combination of inventory, capacity, and time.

The course should not artificially prevent the natural Factorio response of overbuilding. Excess capacity and inventory are legitimate ways to absorb variety. Instead, later experiments should make the tradeoff visible by attaching costs or constraints.

The learner can then discover:

- inventory as a buffer;
- spare capacity as a buffer;
- response/queue time as a buffer;
- better sensing, routing, forecasting, and control as ways to use those buffers more effectively and reduce avoidable variability.

This creates a strong conceptual progression:

**variability → buffering → regulation → requisite variety**

Only after the learner has experienced the need for a regulator with more possible responses should concepts such as Ashby's Law of Requisite Variety be introduced.

### 4.3 Layer III — Organizational Cybernetics Laboratory

The third layer is not initially a conventional course and should not pretend to be controlled measurement science.

A single-player Factorio factory is not an organization. Assemblers do not have conflicting incentives, misunderstand instructions, hoard information, resist restructuring, experience bounded rationality, game metrics, or reinterpret routines.

Structured multiplayer scenarios may nevertheless become an experimental environment for organizational cybernetics if FISL can deliberately control:

- roles;
- authority;
- information access;
- communication pathways;
- local autonomy;
- escalation rules;
- dashboards;
- planning information;
- operational disturbances.

An initial multiplayer run should be treated as a **structured exercise plus debrief**, not as a clean A/B experiment proving one organizational form superior to another.

Telemetry can support the debrief, e.g.:

- when a local problem first occurred;
- which role first had information about it;
- when another role became aware;
- when the issue escalated;
- when management intervened;
- when the system recovered.

Over many standardized runs, such exercises may eventually support publishable empirical research. That is a future research program, not a v1 requirement.

A useful summary is:

> **Layer I teaches what the model shows.**  
> **Layer II teaches what the model hides.**  
> **Layer III investigates what the model cannot contain.**

FISL controls the boundary among those three.

---

## 5. Epistemological Safeguard: What Does the Simulation Assume Away?

Factorio makes production systems unusually legible. Real organizations and industrial systems are not.

This creates a risk of **anti-teaching**: learners may internalize an implicit view in which systems are deterministic, metrics are truthful, instructions are interpreted perfectly, and redesigns are executed faithfully.

Every serious FISL experiment should therefore make its representational limits explicit.

A recurring course and scenario element should answer:

- What does Factorio represent directly?
- What does Factorio abstract or omit?
- What assumptions does this scenario modify?
- What important phenomena remain absent?
- What conclusions are warranted from the experiment?
- What conclusions are not warranted?

Examples:

| Factorio assumption | Real-world complication |
|---|---|
| Machines execute instructions perfectly | Human interpretation and execution vary |
| Blueprints copy losslessly | Organizational routines mutate, drift, and are misapplied |
| Production statistics are truthful | Measurement changes behavior and metrics can be gamed |
| Components have no interests | Organizational actors have goals and incentives |
| Production rates are deterministic | Real systems exhibit process and demand variation |
| Full system visibility is easy | Information is partial, delayed, filtered, and political |

The limitations of the simulation should become part of the curriculum rather than something hidden from students.

---

## 6. High-Level Architecture

FISL should be a **two-layer system**, not a single monolithic Factorio mod.

```text
                    COURSE / LAB MATERIAL
                            |
                            | uses
                            v
                  FISL SCENARIO PACKAGE
             +--------------+--------------+
             |                             |
      scenario definition              baseline save
             |                             |
             +--------------+--------------+
                            v
                  FISL CONTROLLER
                     Python / CLI
                            |
              configure / launch / collect
                            |
                            v
+-----------------------------------------------------------+
|                      FACTORIO                             |
|                                                           |
|   +---------------------------------------------------+   |
|   |                 FISL CORE MOD                     |   |
|   |                                                   |   |
|   | Experiment clock     Measurement engine           |   |
|   | Scenario runtime     Source/sink ports            |   |
|   | Zone registry        Objective tracking           |   |
|   | Student UI           Telemetry/event logging      |   |
|   +---------------------------------------------------+   |
|                           |                               |
|                    Factorio mechanics                     |
|                           |                               |
|       belts / machines / chests / circuits / trains       |
|                                                           |
+-----------------------------------------------------------+
                            |
                            v
                     RUN DATASET
              manifest + telemetry + result
                            |
                            v
                    DEBRIEF / ANALYSIS
```

### 6.1 In-game Lua runtime

The FISL core mod runs inside Factorio and owns everything that must remain synchronized with the simulation tick:

- experiment clock;
- scenario runtime state;
- phase transitions;
- entity/zone observation;
- source and demand port behavior;
- metric primitives;
- objective state that depends on simulation events;
- student-facing in-game UI;
- authoritative event/telemetry emission.

### 6.2 External controller

A separate Python controller owns orchestration and experiment metadata:

- scenario parsing and validation;
- scenario compilation/preparation;
- Factorio launch and process control;
- baseline save selection;
- mod configuration;
- run identifiers;
- run manifest creation;
- collection of output datasets;
- post-run calculation and reports;
- instructor/debrief tooling.

The external process should **not** be the authoritative real-time experiment clock.

If the experiment changes phase at simulation tick 18,000, the Lua runtime should make that transition. The experiment must not depend on RCON/network/process scheduling being perfectly timely.

---

## 7. Responsibility Boundary

A useful implementation rule is:

- **Lua answers:** What is happening in Factorio right now?
- **Python answers:** What experiment are we running, and what do the resulting data mean?
- **Scenario files answer:** What did the instructor intend?

This division should remain visible in the repository structure and code review.

---

## 8. The Scenario Is the Primary FISL Abstraction

A FISL scenario is not merely a save file.

It is:

> **A Factorio world + a declared experiment + a measurement specification + learning metadata.**

A conceptual v1 scenario might look like:

```yaml
spec: fisl/v1

scenario:
  id: fp-05-pull-production
  version: 1.0.0
  title: "Production to Demand"

factorio:
  baseline_save: fp-05.zip
  version: "2.0.x"

experiment:
  warmup_seconds: 300
  duration_seconds: 1200

system:
  zones:
    factory:
      area:
        left_top: [-50, -30]
        right_bottom: [50, 30]

ports:
  iron_supply:
    type: source
    item: iron-plate
    schedule:
      type: constant
      rate_per_minute: 180

  customer:
    type: demand
    item: electronic-circuit
    schedule:
      type: constant
      rate_per_minute: 60
    shortage_policy: backlog

metrics:
  - throughput
  - service_level
  - wip
  - productive_time
  - starved_time
  - blocked_time

objectives:
  service_level:
    minimum: 0.95

  wip:
    direction: minimize

visibility:
  student_live:
    - throughput
    - service_level

  post_run:
    - wip
    - productive_time
    - starved_time
    - blocked_time
```

The final schema will be defined in the scenario/measurement contract. The example exists to capture the architectural intent, not to freeze syntax prematurely.

---

## 9. Baseline World and Experiment Must Be Separate

The same physical Factorio save should be reusable under multiple experiments.

For example, a production line might be used first with deterministic demand:

```yaml
schedule:
  type: constant
  rate_per_minute: 60
```

and later with stochastic demand:

```yaml
schedule:
  type: stochastic
  mean_per_minute: 60
  cv: 0.40
```

The student-facing factory need not change.

This separation is one of the primary mechanisms through which v1 remains extensible.

---

## 10. Ports: Controlled Boundaries Between Experiment and Factory

**Ports** are intended to be a core FISL abstraction.

A port is a declared interface at which the experimental environment interacts with the physical factory.

Initial types:

- **source port** — FISL supplies an item into the system according to a schedule;
- **demand/sink port** — FISL requests or consumes an output according to a schedule/policy.

Conceptually:

```text
 FISL                           STUDENT FACTORY                       FISL

 supply                                                               demand
 schedule                                                              process
    |                                                                     |
    v                                                                     v
+---------+      +------+      +----------+      +------+       +---------+
| SOURCE  |----->| belt |----->|production|----->| belt |------>| DEMAND  |
|  PORT   |      |/rail |      |  system  |      |/rail |       |  PORT   |
+---------+      +------+      +----------+      +------+       +---------+
```

Where possible, ports should be built from or attached to native Factorio entities rather than introducing magical educational machinery.

Ports are especially valuable because FISL can know boundary quantities with high confidence:

- input supplied;
- demand requested;
- output received;
- backlog;
- fulfillment timing;
- service level.

The same port abstraction should survive later extensions to stochastic supply, batch orders, interruptions, seasonality, and demand shocks.

---

## 11. System Boundaries and Zones

Every serious experiment must define what counts as **the system**.

FISL v1 should support at least simple rectangular zones.

```text
+------------------------------------------------+
|                                                |
|                SYSTEM BOUNDARY                 |
|                                                |
|  raw -> smelting -> intermediates -> assembly  |
|                                                |
|       belts / buffers / machines / etc.        |
|                                                |
+------------------------------------------------+
       ^                                  |
       |                                  v
   SOURCE PORT                        DEMAND PORT
```

The explicit boundary prevents common measurement ambiguities. If inventory is stored inside the declared system boundary, it may count as WIP even if the student moves it far from the production line.

Later versions may support:

- multiple zones;
- nested zones;
- named entity groups;
- ownership by organizational role;
- logical rather than geometric boundaries.

Those are extensions of the same concept and are not required for v1.

---

## 12. Measurement Is a First-Class Architectural Concern

FISL should never display a derived number unless the system can explain what it means and how it was measured.

Terms such as **utilization**, **cycle time**, **WIP**, and even **throughput** have context-sensitive definitions.

The measurement engine should therefore prefer relatively primitive observations and build declared metrics from those observations.

Candidate primitive observations include:

| Primitive | Meaning |
|---|---|
| `productive_time` | entity observed in productive operation |
| `starved_time` | unable to operate because required input is unavailable |
| `blocked_time` | unable to complete/unload because downstream capacity is unavailable |
| `no_power_time` | unavailable due to insufficient power |
| `disabled_time` | disabled by circuit/script/player policy |
| `input_count` | material entering through a declared source boundary |
| `output_count` | product crossing a declared output/demand boundary |
| `inventory` | declared WIP materials in the system boundary |
| `demand` | quantity requested by the demand process |
| `fulfilled` | requested quantity supplied under the scenario policy |

Derived metrics must declare their semantics.

For example:

```text
effective_utilization = productive_time / experiment_time
```

is different from:

```text
utilization_while_available =
  productive_time /
  (productive_time + starved_time + blocked_time)
```

Both may be useful. Neither should be silently labeled only `utilization`.

The scenario/measurement contract must formalize these definitions.

---

## 13. Cycle Time Is a Special Measurement Problem

Factorio items are generally fungible. Once many identical items enter a production system and are transformed by recipes, FISL cannot honestly claim to know the exact path and age of every output item unless a scenario was specifically designed to make that observable.

Therefore FISL v1 should **not** pretend that arbitrary item-level cycle time is directly measurable.

A scenario should instead declare the measurement method, for example:

- direct order response time;
- cohort completion time;
- transport-only traversal time;
- Little's-Law-derived mean cycle time.

A result should retain that method as metadata, conceptually:

```json
{
  "metric": "cycle_time",
  "value": 84.2,
  "unit": "seconds",
  "method": "little_law_derived"
}
```

This is not merely technical bookkeeping. Measurement semantics are part of the educational content.

---

## 14. Experiment Phases and Time

Experiments should be driven by simulation time, not wall-clock orchestration.

A scenario may eventually contain phases such as:

- setup;
- warm-up;
- baseline observation;
- intervention;
- post-intervention measurement;
- completion.

The Lua runtime should own phase transitions that depend on Factorio ticks.

This provides:

- deterministic timing;
- save/resume safety;
- reproducible phase boundaries;
- independence from RCON latency;
- reliable event ordering.

The scenario contract should distinguish wall-clock descriptions useful to humans from canonical simulation-tick semantics used internally.

---

## 15. Telemetry and the Authoritative Run Record

FISL should create an authoritative, append-oriented record of each run.

Real-time display is useful, but live transport should not be the only source of truth. If a future live UDP or dashboard feed drops data, the scientific record should remain intact.

A conceptual run directory:

```text
runs/
  <run-id>/
    manifest.json
    telemetry.jsonl
    events.jsonl
    summary.json
    final-save.zip
```

The run manifest should include enough provenance to reproduce or audit the experiment:

- run ID;
- scenario ID and version;
- scenario content/hash;
- baseline save hash;
- Factorio version;
- FISL version;
- installed mod names and versions;
- experiment seed;
- simulation start/end ticks;
- learner/team identifier if appropriate;
- relevant configuration values.

Reproducibility should be a data-model feature, not a README promise.

---

## 16. Randomness and Future Reproducibility

FISL v1 is deliberately deterministic, but it should establish the infrastructure for controlled randomness immediately.

Every run should have an **experiment seed** even if v1 uses it minimally.

FISL should expose a dedicated experiment RNG abstraction rather than allowing future features to invoke random behavior ad hoc.

This will allow later experiments such as:

```text
Run A, control strategy 1, seed 739211
Run B, control strategy 2, seed 739211
```

to experience the same disturbance sequence.

This becomes essential for comparing responses to variability.

---

## 17. Persistent State Should Be Boring Data

FISL's in-save persistent state should favor simple reconstructible values:

- strings;
- numbers;
- booleans;
- tables;
- IDs;
- entity unit numbers;
- counters;
- seeds;
- scenario parameters;
- phase state.

Avoid elaborate runtime object graphs or state that cannot be safely reconstructed after load/migration.

Anything reconstructible should be reconstructed.

This principle should make save/reload behavior, schema migrations, debugging, and long-lived scenario compatibility significantly easier.

---

## 18. Student Visibility Is Part of the Experiment

Even in v1, the scenario should distinguish between:

- metrics visible to the learner during the run;
- metrics retained only for post-run debrief;
- instructor/debug-only information.

This prevents teaching scenarios from becoming trivial because the instrumentation reveals the answer.

For example, a bottleneck exercise may expose system throughput while withholding detailed machine-state breakdown until after the run.

The same visibility concept can later expand into Course III information architecture:

- operators see local state;
- logistics sees transport state;
- operations sees aggregates and exceptions;
- planning sees forecasts;
- no role necessarily sees the entire system.

The full organizational implementation is not part of v1, but the scenario model should not assume that all measurements are visible to everyone.

---

## 19. Objectives Versus Measurements

FISL should keep **measurement** separate from **objective**.

A metric answers:

> What happened?

An objective answers:

> According to this experiment, what outcome are we trying to achieve?

For example:

```yaml
metrics:
  - throughput
  - service_level
  - wip

objectives:
  service_level:
    minimum: 0.95
  wip:
    direction: minimize
```

This separation becomes important later when costs are introduced. The same physical metrics may be evaluated under very different objective functions.

---

## 20. Economics Is a Later Layer, Not a Missing Foundation

Factorio's lack of money is not necessarily a defect for the first course.

It forces learners to reason in physical quantities:

- units/time;
- inventory;
- energy;
- machine capacity;
- transport capacity;
- time.

That is pedagogically valuable and compatible with the cybernetic tradition of managing real operational variables rather than reducing every signal immediately to an accounting abstraction.

Later, an experiment can attach costs to already-understood physical behavior:

- capacity cost;
- energy cost;
- inventory carrying cost;
- lateness cost;
- downtime cost;
- selling price;
- control/information-system cost.

At that point the learner can discover that the highest-throughput physical system is not necessarily the economically preferred system.

Economics should therefore appear as a **new objective layer**, not be hard-coded into the core physical simulation.

---

## 21. Course II Extension Model: Buffering and Requisite Variety

Future variability experiments should permit, rather than prohibit, the natural Factorio strategy of overbuilding.

Three principal currencies absorb variability:

| Buffer | Typical Factorio expression |
|---|---|
| Inventory | chests, stockpiles, in-process material |
| Capacity | extra machines, spare transport, reserve production |
| Time | queues, waiting, lateness, longer response time |

Control and better information do not eliminate the need for buffering. They can reduce avoidable variability and improve the way those buffers are allocated.

A future experiment might therefore ask:

> Given the same uncertain environment and service requirement, what is the least costly combination of inventory, spare capacity, response time, and control sophistication that keeps the factory viable?

That creates a natural route from Factory Physics to cybernetics.

---

## 22. Course III Extension Model: Information Architecture

Structured multiplayer organizational exercises may eventually add scenario constructs such as:

```yaml
players:
  - role: operations
    information_policy: ops-dashboard

  - role: logistics
    information_policy: logistics-local

  - role: planning
    information_policy: forecast-only
```

Potential future concerns include:

- per-player GUI views;
- map/chart visibility;
- restricted operational information;
- communication channels;
- authority boundaries;
- escalation;
- role-level controls;
- debrief timelines.

These should extend the existing scenario notions of **visibility**, **control**, **events**, and **zones**, rather than requiring a separate experimental architecture.

---

## 23. Relationship to the Factorio Learning Environment (FLE)

The **Factorio Learning Environment (FLE)** is an important adjacent project and useful source of implementation ideas. It provides infrastructure for AI agents interacting with Factorio, including Python-side environment tooling, Factorio process/cluster control, experimentation/evaluation support, and instrumentation.

FISL and FLE, however, have different primary abstractions:

- FLE: a software/AI agent acts on Factorio through an agent/tool environment.
- FISL: a human learner plays ordinary Factorio while a controlled experiment surrounds the game.

FISL should therefore **not require FLE as a runtime dependency**.

Where technically and legally appropriate, FISL may reuse or adapt ideas or permissively licensed components from FLE, particularly around launching, RCON, automated testing, or experiment infrastructure.

In the future, FLE-like agents could be extremely useful for automated FISL scenario regression testing, state construction, and validation.

Relevant project: <https://github.com/JackHopkins/factorio-learning-environment>

---

## 24. FISL v1 Scope

The governing v1 rule is:

> **V1 implements deterministic experimental control and measurement. Future versions add new sources of variety, new control mechanisms, and new information structures—not a new architecture.**

### 24.1 Required in v1

FISL v1 should support:

1. Reproducible scenario packages.
2. Baseline Factorio saves.
3. Deterministic experiment phases/timing.
4. Explicit system zones/boundaries.
5. Controlled deterministic source ports.
6. Controlled deterministic demand/sink ports.
7. Measurement primitives sufficient for the initial Factory Physics labs.
8. Explicit derived metric semantics.
9. Student-live versus post-run metric visibility.
10. Simple objectives.
11. Run manifests and provenance.
12. Append-oriented telemetry/event logs.
13. Experiment seed plumbing.
14. Reset/re-run workflow.
15. Post-run summary/debrief data.

### 24.2 Explicitly out of scope for v1

Do **not** build the following merely because they may be useful later:

- stochastic disturbances;
- machine-reliability simulation;
- stochastic supplier model;
- economics engine;
- custom web instructor dashboard;
- LMS integration;
- mandatory database server;
- organizational roles;
- multiplayer differential information;
- VSM simulator;
- general-purpose statistics package;
- automatic semantic understanding of arbitrary factories;
- a replacement for the Factorio circuit network;
- a large industrial-engineering ontology;
- a dependency on advanced expansion mechanics unless a specific scenario requires them.

The architecture must leave room for these capabilities without implementing them prematurely.

---

## 25. Initial Factory Physics Lab Sequence

The first labs should drive v1 requirements.

| Lab | Core idea | Primary FISL capability |
|---|---|---|
| **0. Measuring the Factory** | boundaries, rates, observation | zones, telemetry, metric definitions |
| **1. Flow & Capacity** | process rates, system capacity | throughput measurement |
| **2. The Constraint** | bottlenecks, local vs. system capacity | entity-state measurement |
| **3. WIP & Little's Law** | WIP, throughput, cycle time | WIP sampling + declared cycle-time method |
| **4. Starvation & Blocking** | buffers, decoupling | machine-state classification |
| **5. Push & Pull** | demand, WIP control, signals | demand ports + service level |
| **6. System Optimization** | throughput vs. WIP vs. service | objectives + comparative run reports |

These labs deliberately avoid stochastic variability. The learner should first develop a strong mental model of deterministic production.

The later variability course then removes one major assumption rather than introducing an unrelated world.

---

## 26. Scenario Evolution Should Be Additive

The architecture is considered extensible when future concepts are expressed primarily as **new scenario components or policies**.

For example, deterministic v1 demand:

```yaml
schedule:
  type: constant
  rate_per_minute: 60
```

Later variability:

```yaml
schedule:
  type: stochastic
  mean_per_minute: 60
  cv: 0.4
```

Later disturbances:

```yaml
disturbances:
  - type: machine_failure
    process: exponential
    mtbf_seconds: 1200
    repair:
      distribution: lognormal
      mean_seconds: 180
```

Later economics:

```yaml
costs:
  inventory_item_minute: 0.08
  late_item_minute: 3.00
  capacity_unit_minute: 40.00
```

Later organizational experiments:

```yaml
roles:
  operations:
    visibility: aggregate-kpis
  logistics:
    visibility: transport-local
```

The implementation may grow, but the conceptual architecture should remain recognizable.

---

## 27. Proposed Repository Structure

The intended repository shape is approximately:

```text
FactorioResearch/
|
+-- README.md
+-- docs/
|   +-- ARCHITECTURE.md
|   +-- SCENARIO_MEASUREMENT_CONTRACT.md
|   +-- adr/
|       +-- README.md
|
+-- factorio/
|   +-- fisl-core/
|       +-- control.lua
|       +-- fisl/
|           +-- experiment.lua
|           +-- ports.lua
|           +-- zones.lua
|           +-- metrics.lua
|           +-- telemetry.lua
|           +-- objectives.lua
|           +-- gui.lua
|
+-- python/
|   +-- fisl/
|       +-- cli.py
|       +-- scenario/
|       |   +-- schema.py
|       |   +-- compiler.py
|       |   +-- validator.py
|       +-- controller/
|       |   +-- factorio.py
|       |   +-- run.py
|       +-- telemetry/
|       |   +-- reader.py
|       |   +-- metrics.py
|       +-- report/
|           +-- debrief.py
|
+-- scenarios/
|   +-- factory-physics/
|       +-- fp00-measurement/
|       +-- fp01-capacity/
|       +-- fp02-constraint/
|       +-- fp03-littles-law/
|       +-- fp04-buffering/
|       +-- fp05-pull/
|       +-- fp06-capstone/
|
+-- tests/
    +-- schema/
    +-- lua/
    +-- integration/
    +-- scenarios/
```

This is a direction, not an instruction to create empty implementation scaffolding before the contracts are understood.

---

## 28. FISL v1 Completion Criterion

FISL v1 should be considered successful when a student can run a scenario such as **Push & Pull** and obtain a reproducible experimental record.

Conceptually:

```text
$ fisl run fp-05-pull-production
```

The learner receives the same baseline factory as other students.

FISL supplies controlled input and external customer demand.

The student modifies the system using native Factorio mechanics.

Only instructor-selected live measurements are visible during the experiment.

At the end, FISL can report results with explicitly defined semantics, for example:

```text
Demand:                1,200 units
Fulfilled:             1,158
Service level:         96.5%

Average WIP:           437 units
Throughput:            57.9/min

Machine state time:
  productive:          71%
  starved:             11%
  blocked:             18%
```

The student can reset to the baseline and try a different strategy.

Two runs can be compared because the system records exactly which world, scenario, measurement semantics, code versions, and run conditions produced them.

If FISL does this cleanly for Labs 0–6, v1 has achieved its purpose.

---

## 29. Architectural Decisions We Are Intentionally Deferring

The following should be resolved through the scenario/measurement contract or later ADRs rather than guessed now:

- exact scenario serialization format and schema versioning;
- exact mapping between scenario time and Factorio ticks;
- exact mechanism used to identify entities as source/demand ports;
- whether ports use normal chests, custom entities, or scenario tags;
- exact definition of WIP for transformed multi-stage material;
- sampling frequency and aggregation semantics;
- exact status mapping for productive/starved/blocked states;
- exact handling of pauses, save/reload, and manual time acceleration;
- entity selection semantics for machine metrics;
- authoritative telemetry encoding;
- Python packaging and CLI framework;
- RCON/process-launch implementation;
- integration-test strategy;
- licensing of any reused FLE components.

These are not omissions. They are the next design layer.

---

## 30. The Next Design Artifact: Scenario / Measurement Contract

Before implementation, FISL needs a precise contract defining its **scientific API**.

The next document should settle the semantics of at least:

- `scenario`;
- `experiment`;
- `phase`;
- `zone`;
- `source`;
- `demand` / `sink`;
- `throughput`;
- `WIP`;
- `service_level`;
- `productive`;
- `starved`;
- `blocked`;
- cycle-time measurement methods;
- metric aggregation;
- objective evaluation;
- metric visibility;
- run provenance;
- reset/replay semantics.

This contract is more important than immediately writing Lua or Python code. If the measurement semantics are ambiguous, implementation will simply encode ambiguity more quickly.

---

## 31. Governing Principles

The current design can be summarized by the following principles.

### P1. Factorio models the system; FISL models the experiment.
Do not duplicate native mechanics without a compelling experimental reason.

### P2. Scenario before theory.
Learners should encounter system behavior before receiving the formal vocabulary whenever pedagogically appropriate.

### P3. Measurement semantics are part of the curriculum.
A metric must say what it measures and how it was derived.

### P4. The system boundary must be declared.
Rates, WIP, and performance cannot be interpreted without knowing what system is being measured.

### P5. Reproducibility is a first-class feature.
Scenario versions, baseline state, seeds, software versions, and measurement definitions must travel with the run result.

### P6. Simulation time is authoritative.
Experiment events should be synchronized to Factorio ticks rather than external process timing.

### P7. Persistent state should be boring data.
Prefer simple, auditable, migratable state representations.

### P8. Visibility is an experimental variable.
Not every measurement must be visible to the learner during the run.

### P9. V1 is deterministic by design.
Learn the deterministic system deeply before adding variability.

### P10. Future capability should extend the scenario model.
New disturbance, economic, control, or organizational features should add components rather than replace the architecture.

### P11. Do not hide the limits of the simulation.
Every scenario should state what Factorio represents, what it omits, and what conclusions the learner may safely draw.

### P12. The teaching platform is the durable deliverable.
The syllabus and textbook can evolve; reproducible scenario infrastructure is what makes the pedagogy portable across instructors and institutions.

---

## 32. Research and Teaching Positioning

The first concrete audience should be narrow:

- upper-level undergraduate industrial engineering;
- introductory graduate industrial engineering;
- operations management;
- manufacturing/systems engineering;
- introductory operations research where the scenarios fit.

The initial promise should be correspondingly modest and credible:

> **Factory Physics Through Factorio: an experiential, reproducible laboratory for learning production-system behavior.**

Variability/control work follows once the deterministic laboratory is validated.

Organizational cybernetics should initially be presented as a research/seminar program, not marketed as an already validated course.

---

## 33. Closing Definition

FISL is the layer upon which the rest of the project is built because it makes Factorio experimentally controllable without replacing the qualities that make Factorio pedagogically valuable.

**Factorio is the simulation engine.**  
**FISL is the experimental apparatus.**  
**Scenarios are the experiments.**  
**Courses are sequences of those experiments.**

The v1 mission is deliberately constrained:

> Build a rigorous deterministic Factory Physics laboratory whose contracts are strong enough that variability, economics, control, and organizational information structures can later be added without redesigning the foundation.
