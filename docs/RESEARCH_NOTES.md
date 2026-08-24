# FISL Research Notes and Precedents

This document preserves the research context that motivated the Factorio Industrial Systems Laboratory (FISL) architecture. It is not the normative architecture specification; see [`ARCHITECTURE.md`](ARCHITECTURE.md) for that.

## 1. Existing educational precedents

### MCI Innsbruck — Factorio: Serious Project Management

MCI Innsbruck has offered an interdisciplinary elective titled **Factorio – Serious Project Management**, using Factorio as a simulation environment for project-management topics such as planning, dependencies, resource allocation, workflow organization, risk, milestones, iterative improvement, teamwork, and communication.

This is important because it establishes that Factorio has already crossed the line from informal systems-thinking game into an actual university teaching environment.

Reference: <https://www.mci.edu/>

### Boardman / Krejci — production and inventory control with Factorio

Bonnie Boardman and Caroline Krejci presented work on using Factorio to teach production and inventory control. The educational material included production-line design, inventory control, Theory of Constraints, and Little's Law.

This is the closest direct precedent for the initial FISL Factory Physics direction.

Search title: **Simulation of Production and Inventory Control using the Computer Game Factorio** (ASEE Gulf-Southwest, 2021).

### University of Bath — management games in operations/supply-chain education

The University of Bath School of Management has advertised research work investigating management games—including Factorio—in Operations and Supply Chain Management education.

This is useful as evidence that the pedagogical question itself is an active research topic rather than only a game-community intuition.

Reference: <https://www.bath.ac.uk/guides/school-of-management-phd-projects/>

---

## 2. Factorio as an optimization / systems research environment

Several research projects treat Factorio as more than a game and use it as a formal problem environment for logistics, automation, planning, optimization, or systems engineering.

Relevant examples include:

- **The Factory Must Grow: Automation in Factorio** — formal optimization/automation framing around Factorio logistics and production.
- Research on Factorio splitter networks using mathematical/network-flow concepts.
- Research on Factorio blueprint layout and production optimization.
- **Factorio Learning Environment (FLE)** — a Factorio-based environment for testing long-horizon AI planning, automation, and resource reasoning.

FLE: <https://github.com/JackHopkins/factorio-learning-environment>

These projects support a core FISL assumption: Factorio is structured enough to act as a serious experimental substrate.

---

## 3. Why the initial 20-chapter idea was rejected

An early concept treated the project as roughly one twenty-chapter course moving from flow and Little's Law through cybernetics, Stafford Beer, and multiplayer organizational experiments.

That structure was rejected for three reasons.

### 3.1 It was two or three different pedagogical projects stapled together

Deterministic Factory Physics is a coherent single-player course with strong existing precedent.

Variability/control introduces a new class of phenomena that vanilla Factorio largely suppresses.

Organizational cybernetics introduces human communication, authority, partial information, coordination, and interpretation. Multiplayer exercises have different logistics and validity constraints than single-player Factory Physics labs.

Therefore the project was separated into:

1. Factory Physics Through Factorio.
2. Variability / Control / Cybernetic Systems.
3. Organizational Cybernetics Laboratory / research seminar.

### 3.2 Vanilla Factorio has a determinism problem for variability and cybernetics

Factorio is excellent at feedback and deterministic flows, but much of Factory Physics and cybernetics is concerned with how systems behave under uncertainty and disturbance.

Vanilla Factorio largely lacks:

- random machine failures;
- stochastic processing yields;
- unreliable suppliers;
- stochastic customer demand;
- transport-time variation of the kind an instructor can control;
- information delay and distortion.

This means vanilla Factorio alone cannot honestly demonstrate the variability half of Factory Physics or Ashby's requisite variety.

This limitation became the key reason for building FISL.

### 3.3 The organization analogy can become anti-teaching

Assemblers do not:

- misunderstand instructions;
- resist redesign;
- have conflicting goals;
- hoard information;
- game metrics;
- suffer bounded rationality;
- reinterpret routines.

Therefore analogies such as "blueprint = organizational routine" must be handled carefully. They are useful only if the course also asks where the analogy breaks.

This led to the recurring design question:

> **What does the simulation assume away?**

That question is now part of the FISL architecture itself.

---

## 4. The variability insight: the deterministic optimum should fail

The strongest proposed Course II sequence is:

1. Give students a deterministic environment.
2. Let them optimize it aggressively.
3. Introduce controlled variability.
4. Let the elegant deterministic solution become brittle.
5. Observe queues, starvation, blocking, lateness, and service failure.
6. Introduce the formal theory only after the experience.

This is closely aligned with the way variability is motivated in Factory Physics, except Factorio lets students experience the problem rather than only reason about it abstractly.

---

## 5. The buffering correction

An important correction to the early cybernetics design was that students should **not** be artificially prevented from solving variability by overbuilding.

Inventory and excess capacity are real ways of absorbing variation.

The more honest framework is the Variability Buffering Law: variability must be buffered by some combination of:

- **inventory**;
- **capacity**;
- **time**.

The educational question then becomes one of tradeoffs.

A future FISL experiment can allow students to respond naturally with more chests, more machines, or longer queues—and later assign costs to those responses.

Better control and information are valuable because they can reduce avoidable variability and allow the system to achieve required performance with a better allocation of inventory, capacity, and time.

This produces the conceptual progression:

**variability → buffering → regulation → requisite variety**

rather than treating feedback control as a magical alternative to buffering.

---

## 6. Why the absence of money is initially useful

Factorio has no native monetary accounting system. This initially appeared to be a gap, but the project ultimately treats it as useful for the first course.

Learners must reason in physical quantities:

- units per time;
- inventories;
- machine capacity;
- energy;
- transport capacity;
- response time.

Only after the physical behavior is understood should a later FISL experiment attach economic values such as carrying cost, capacity cost, energy cost, lateness penalties, or selling price.

That creates a powerful transition: the highest-throughput physical system may stop being the best system when the objective function changes.

The physical-first emphasis also has an intellectual connection to operational cybernetics and Project Cybersyn, where operational quantities and indicators were important representations of industrial state rather than only monetary summaries.

A useful historical overview of Project Cybersyn is available from MIT Press: <https://thereader.mitpress.mit.edu/project-cybersyn-chiles-radical-experiment-in-cybernetic-socialism/>

---

## 7. Measurement as a bridge to cybernetics

The production-statistics screen and Factorio circuit network make measurement unusually visible.

A critical question for the learner is:

> What must I measure to know whether this factory is healthy?

This connects Factory Physics to:

- observability;
- management information systems;
- control;
- feedback;
- exception reporting;
- eventually organizational information design.

The sequence is naturally:

**measure → compare → decide → actuate → measure again**

This is one reason FISL treats measurement semantics as part of the scientific API rather than just UI telemetry.

---

## 8. Organizational cybernetics: debrief before measurement science

A future structured multiplayer exercise might divide responsibility among roles such as:

- production divisions;
- logistics;
- operations;
- planning;
- policy/management.

The system can then create information pathologies: one group knows a local cause while another sees only a lagging aggregate symptom.

The first objective should not be to produce statistically clean claims about centralized hierarchy versus a Viable System Model organization. Six-person teams create enormous confounds in skill, communication, personality, and leadership.

Instead, the initial product is the **debrief**.

A useful post-run reconstruction could ask:

- When did the physical disturbance occur?
- Who first had information about it?
- Which information crossed which boundary?
- When did another role become aware?
- What was escalated?
- What did management believe was happening?
- When did an intervention occur?
- How long until recovery?

Telemetry should support that debrief rather than pretend to replace qualitative organizational analysis.

Repeated standardized runs may eventually support more formal research.

---

## 9. The teaching mod/platform is the durable deliverable

Another major design conclusion was that the durable artifact is not primarily a textbook.

A course tied to one instructor's hand-edited saves is difficult to reproduce.

A scenario platform can encode:

- baseline worlds;
- experiment parameters;
- timing;
- controlled demand and supply;
- measurement semantics;
- random seeds;
- learner-visible metrics;
- authoritative telemetry;
- reset/replay behavior.

That allows another instructor or institution to run materially the same laboratory.

This is the line between "a clever class using Factorio" and a reusable experimental teaching platform.

---

## 10. Factorio API feasibility

Factorio's Lua runtime provides the general primitives required for FISL's proposed architecture, including event/tick-driven execution, persistent mod state, entity inspection, GUI construction, file output, forces/charting, and deterministic random-number facilities.

Current API documentation: <https://lua-api.factorio.com/latest/>

The design deliberately avoids requiring the external Python controller to be the precise real-time clock; phase transitions that matter to the experiment should occur inside the Factorio simulation according to ticks.

---

## 11. Current research thesis

The project can be summarized as follows:

> Factorio is already good enough to teach a significant deterministic subset of Factory Physics. FISL makes that instruction reproducible and measurable, then selectively relaxes Factorio's simplifying assumptions so that variability, control, and later information/organizational experiments become possible without replacing the native simulation.

Or, more compactly:

> **Factorio is the simulation engine. FISL is the experimental apparatus. Scenarios are the experiments. Courses are sequences of those experiments.**
