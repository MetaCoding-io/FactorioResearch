# The Viable Factory — a VSM Exploration

**Status:** daydream (first written 2026-08-28). This is an exploration
memo, not a plan of record. It changes nothing about the Course I
(Factory Physics) or Course II (Variability, `COURSE_II_SCOPE.md`)
tracks, commits no engineering, and jumps no gates. Its purpose is to
capture a line of thinking about Stafford Beer's Viable System Model
(VSM) and Factorio well enough that it can be judged, improved, or
shelved deliberately.

Anchors: `ARCHITECTURE.md` §4.3 (Layer III — Organizational Cybernetics
Laboratory), `RESEARCH_NOTES.md` §8 (debrief before measurement
science), `COURSE_II_SCOPE.md` §3 ("regulation as a subject belongs to
Course III"), ADR 0011 (disclosure audiences).

---

## 1. The gap this daydream lives in

The existing documents hold two positions about organizational
cybernetics, both correct:

1. **Layer III is the destination.** The architecture names it; the
   research notes sketch its roles, information pathologies, and
   debrief.
2. **Layer III is methodologically treacherous.** A six-person
   multiplayer exercise confounds structure with skill, personality,
   communication, and leadership. `RESEARCH_NOTES.md` §8 is blunt: the
   first objective cannot be clean claims about hierarchy versus VSM;
   the first product is the debrief.

Between those two positions there is an unclaimed middle, and it is
where this daydream lives:

> **The VSM can be studied in Factorio *before* humans enter the
> loop — as worked examples: a family of factories with identical
> physics and different control structure, subjected to the same
> disturbance ensemble, whose viability measurably differs.**

Call these **viability variants**. Each variant is an ordinary FISL
scenario plus a scripted control structure. Because the "organization"
is circuits and declared policies rather than people, variants are
reproducible, hashable, and sweepable — every methodological property
Layer III lacks, the in-silico version has for free. The confound
problem is not solved; it is *routed around*, and (§8 below) the
scripted variants later become the control condition that makes the
human exercises interpretable.

This is the one genuinely new move in this memo. Everything else is
elaboration.

---

## 2. Why Factorio wants to be a VSM

Beer's model, in one breath: a system is viable when it can maintain a
separate identity within its environment. Viability requires five
interlocking subsystems — operations (S1), coordination (S2),
operational management (S3, with its audit channel S3\*), intelligence
(S4), and policy/identity (S5) — repeated recursively: every S1 is
itself a whole viable system at the next level down.

The mapping onto a Factorio base is unreasonably good. Not because
Factorio was designed for it, but because every player who scales a
base past one bus rediscovers these functions under other names:

| VSM | Beer's gloss | Factorio-native form |
|---|---|---|
| **S1** | Operational units doing the primary activity, each embedded in its own environment | Production divisions: a smelting column, a circuit block, a science block, a mining outpost. Each locally sensible on its own. |
| **S2** | Coordination / anti-oscillation between S1s | Rail signals and train schedules; circuit interlocks on shared resources; power priority; the conventions (belt sides, bus lanes) that stop divisions from fighting. |
| **S3** | "Inside and now": the resource bargain, synergy, accountability | Allocation of shared ore, power, and bots among divisions; quota circuits; reallocating input to the lagging line. The main bus is an S3 artifact. |
| **S3\*** | Sporadic audit bypassing routine reporting | Going and *looking* — or in FISL terms: the census, ground truth against division-reported dashboards. |
| **S4** | "Outside and then": intelligence, environment, future | Radar (literally), prospecting for new patches, watching biter evolution, research investment, planning the next outpost. |
| **S5** | Identity, policy, closure; balancing S3 against S4 | What is this factory *for*? The declared objective conjunction; the standing rule that arbitrates "iron to ammo now" versus "iron to labs and expansion". |
| **Algedonic channel** | Pain signal that bypasses the hierarchy | The programmable speaker: an alarm wired from a failing element straight to the top, interrupting normal reporting. |
| **Recursion** | Every S1 contains the whole model | A mining outpost has its own S1s (drills), S2 (signals), S3 (local balancing), S4 (patch monitoring), S5 (its charter from the base). |

Two Factorio folk-failures make the mapping vivid before any theory is
stated. The **coal-power death spiral** (defense drains power → miners
slow → less coal → less power) is a textbook cross-subsystem positive
feedback loop that S2/S3 exist to break. The **oil-cracking deadlock**
(one product backs up, the refinery stalls, everything downstream
starves while every machine is individually "fine") is a coordination
failure that no amount of local optimization at S1 can repair. Every
experienced player has debugged both; neither has ever had a name in
the game. Beer supplies the names.

There is also a theoretical hinge, and it is the reason this material
belongs *after* the regulation arc that `COURSE_II_SCOPE.md` already
assigns to Course III's opening: **the VSM is Ashby's law applied
recursively.** A single line can have a single regulator with requisite
variety. A province of divisions cannot — no one regulator can hold
enough variety to meet the whole environment. The only remaining fix is
*structural*: attenuate variety downward (autonomy — most disturbances
absorbed inside the S1 that meets them), amplify variety upward
(exception reporting, algedonics), and put a metasystem over the
residue. VSM is what requisite variety forces on you at scale. That is
a claim the laboratory can *show*, not just assert.

---

## 3. Viability as a measurement

For this to be a FISL subject rather than an essay, "viable" must be an
operationalized word, and the existing machinery is almost sufficient.
A working definition:

> A system is **viable over a horizon, under a declared disturbance
> ensemble and endowment**, to the extent that it keeps its declared
> objective conjunction satisfied — and recovers it when breached —
> without external intervention.

Everything load-bearing in that sentence is already a FISL concept:

- **Declared objective conjunction** — the objectives machinery,
  unchanged. Identity *is* the requirement set; this is
  objectives-without-a-score doing S5 duty. (Beer's POSIWID — the
  purpose of a system is what it does — becomes checkable: declared
  purpose versus measured behavior.)
- **Disturbance ensemble** — Course II's seeded streams: failures,
  stochastic supply/demand, scrap, `supply_loss`, plus the
  environmental-drift knobs of §7.
- **Horizon- and endowment-relative** — deliberately so; see §6 on the
  overbuilding steelman.

Candidate headline metrics, all derivable from existing telemetry
semantics:

- **Requirement-holding fraction** — share of the observation window in
  which the conjunction holds.
- **Time to loss of identity** — first unrecovered breach; the
  survival-analysis quantity. Censoring discipline (a run that ends
  still-viable is censored, not "infinitely viable") carries over from
  Course I's rules of evidence untouched.
- **Recovery-time distribution** per disturbance class.
- **Detection latency** — disturbance onset to first policy response.
  Notably, `RESEARCH_NOTES.md` §8's debrief questions ("when did the
  disturbance occur, who first had information, when did intervention
  occur") stop being interview questions and become *timestamps*.

And a deliberate continuity gift: Beer's Cybersyn triad is built from
quantities Courses I and II already own. **Potentiality** is design
capacity (Lab 1), **capability** is effective capacity under current
availability and resources (Course II's availability arithmetic),
**actuality** is measured throughput (Lab 0 onward). Performance,
productivity, and latency indices per division are ratios of things the
learner has personally measured. Cybersyn's ops-room indicators arrive
as *old friends arranged in a new pattern* — the same trick Course II
plays by drawing the practical-worst-case gap on Lab 7's axes.

---

## 4. The gallery: viability variants as worked examples

The heart of the daydream. One physical setting; a family of control
structures; one shared disturbance ensemble swept across all of them;
one comparison table at the end. Ablation studies for organizations.

**The setting ("the Province"):** three or four production divisions
(say: plates, circuits, a science or ammunition line) plus a logistics
artery, sharing ore fields, a power grid, and a construction-bot pool.
Service requirement: sustain a declared product mix to an external sink.
Environment: seeded failures and demand wobble (Course II machinery),
plus slow environmental drift — patch depletion, and at least one
mid-horizon demand-mix shift (the "market" changes what it wants).

Each variant is *the same province* with control structure added or
removed. Predicted failure signatures are stated up front — the
variants are only worth building if the signatures are behaviorally
distinct and land where the theory says they land.

- **V0 — The Mob of Divisions.** S1s only. Each division locally
  well-built; shared resources unarbitrated — no power priority, no
  interlocks, no quotas. *Predicted signature:* oscillation and
  deadlock — mutual-starvation cycles, the death spiral, the
  cracking-style stall — with every division individually healthy by
  its local metrics until the collapse. *Lesson:* the failure lives
  **between** units; S2's job exists.

- **V1 — The Scheduled Province.** V0 plus S2: interlocks, priorities,
  schedules, fixed quotas. *Predicted signature:* stable under nominal
  load, but **rigid** — a seeded failure in one division cannot pull
  slack from the others; a demand-mix shift strands capacity behind
  fixed allocations. Degrades more than the physics requires.
  *Lesson:* coordination is not management; the resource bargain (S3)
  is a distinct function.

- **V2 — The Managed Province.** V1 plus S3: a declared reactive
  policy reallocating shared inputs toward the lagging division,
  per-division accountability metrics — and S3\* as a periodic census
  audited against division-reported dashboards. A sub-variant
  miscalibrates one division's own sensor (it honestly misreports), and
  only the audit channel catches the divergence — machinery ADR 0011
  and the census discipline already provide. *Predicted signature:*
  robust "inside and now" — rides out failures and mix shifts within
  existing capability — followed by **slow drift onto a cliff** as
  patches deplete and the environment shifts, with dashboards green
  nearly to the end. *Lesson:* an organization perfectly managed for
  today dies of tomorrow; there is no S4.

- **V3 — The Prospecting Province.** V2 plus S4: radar coverage, a
  prospecting policy that triggers outpost construction when reserves
  cross thresholds, research/retooling investment ahead of the
  anticipated mix shift. *Predicted signature:* survives the drift that
  kills V2. The first variant that is viable rather than merely stable.

- **V4 — The Two Captains.** S3 and S4 both present, **unarbitrated**:
  operations and expansion draw on one resource pool with no policy
  layer above them. Two sub-variants: S4 dominant (expansion
  cannibalizes operations; the service requirement fails *now*) and S3
  dominant (expansion perpetually deferred; the province dies *later*,
  V2's death in slow motion). *Predicted signature:* V0's oscillation
  reappearing one recursion up, at metasystem timescale. *Lesson:* S5
  is not a chairman's portrait; it is the standing arbitration of
  inside-and-now against outside-and-then. In silico it is honestly
  thin — a declared investment ratio plus the objective conjunction —
  and §6 owns that thinness.

- **V5 — The Silent Province.** Full structure; vary only the
  **channel design**. In one arm, exception signals travel the routine
  reporting path — aggregated, sampled, lagged. In the other, an
  algedonic bypass: a speaker alarm wired from the failing element
  straight to the policy layer. Same disturbance, measured difference
  in detection latency and recovery time. *Lesson:* variety engineering
  of channels; filtering by exception; why the pain signal must be
  allowed to jump the hierarchy. (This is also the most Cybersyn lab:
  its second half builds the ops room — triad indices per division,
  exception thresholds — from FISL reports.)

- **V6 — Recursion (coda).** Zoom into one outpost of V3 and find the
  whole model again at the smaller scale, ending with the observation
  that the Province itself is an S1 of something larger. The recursion
  theorem *seen*, not asserted. No new machinery; a guided reading of
  an existing run.

The course-level deliverable mirrors Lab 7: where Course I ends on
characteristic *curves*, this ends on characteristic **failure
signatures** — one comparison table, per variant per disturbance class,
of holding fraction, time to identity loss, recovery time, detection
latency. Structure, not effort, is the independent variable.

---

## 5. The learner's role

Three modes, in order of ambition:

1. **Diagnose.** The learner receives a variant's telemetry — with
   role-appropriate visibility, per ADR 0011 — and must name the
   missing or broken subsystem *before* seeing the build. Beer's
   *Diagnosing the System for Organizations* is nearly a lab workbook
   for this; the failure-signature table is the answer key. This is the
   in-silico version of the debrief discipline of `RESEARCH_NOTES.md`
   §8, run against ground truth.

2. **Design.** Start from V2; build S4 out of radars, circuits,
   thresholds, and construction bots until the province survives the
   depletion ensemble. Or start from V0 and earn S2. The Course I
   ethic — measured before authored, reference solutions, objectives
   without scores — transfers whole.

3. **Inhabit (the bridge to Layer III).** Replace one scripted
   subsystem with a human or a small team; keep the rest scripted.
   The scripted variants now serve as **control conditions**: the
   multiplayer question stops being the confounded "hierarchy versus
   VSM in six-person teams" and becomes the tractable "does your human
   S3 beat the scripted S3 on the same ensemble, and where does the
   telemetry say the difference lived?" This is the cleanest answer
   this project has yet had to the §8 confound problem — Layer III
   inherits a baseline instead of a vocabulary.

---

## 6. Honesty section: where this can go wrong

**The Potemkin risk.** The failure mode of all VSM writing is
relabeling: calling a thermostat an S3 adds words, not insight. The
acceptance test for every lab in §4 is *behavioral*: the ablation must
produce a failure signature that is distinct, predicted in advance, and
attributable to the missing function. A variant whose removal changes
nothing measurable is a variant the course must not teach.

**The rigged-demo risk.** Ablation studies invite strawmen. Each
variant must be a *steelman* of its own structure — V2's S3 must be a
genuinely good S3, or its death proves nothing. This is the buffering
correction (`RESEARCH_NOTES.md` §5) applied to organization: do not
forbid the honest workaround. In particular: **can V2 survive by
overbuilding?** Yes — with a large enough endowment, S4-lessness looks
viable on any finite horizon. That is not a bug in the course; it is
the deepest lesson in it. Buffers substitute for structure — for a
while, at a price. Course II teaches three buffer currencies
(inventory, capacity, time); `ARCHITECTURE.md` §21 already names the
fourth — *control sophistication* — and this course is the fourth
currency at organizational scale. Viability claims are therefore
always horizon- and endowment-relative, and the comparison table should
say so on its face.

**S5 is thin in silico.** Scripted policy is a constant; real S5 —
contested identity, renegotiated purpose — needs humans and stays in
Layer III. The in-silico course should say plainly: S1–S3 map crisply,
S4 decently (the environment genuinely changes: depletion, evolution,
demand shifts), S5 by construction only. V4 teaches S5's *function*
(arbitration), not its *life*.

**Factorio's environment is narrow.** Beer's environment contains
markets, competitors, regulators, publics. Factorio natively offers
depletion and biters; everything else is injected (demand-mix shifts do
the heaviest lifting as "the market"). The course should not claim more
environmental variety than the ensemble declares — the same honesty
rule Course II applies to randomness.

**Scope gravity.** `ARCHITECTURE.md` §23 lists "VSM simulator" under
explicit non-goals, and that line stays true: nothing here is a
simulator *of* the VSM. It is the same laboratory, same schema
discipline, same measurement contract, pointed at control structure as
the independent variable. If a proposed feature only makes sense for
this course and not as a general scenario capability, that is the smell
that scope gravity has won.

---

## 7. What FISL would actually need

Read as a dependency wishlist, not commitments. Striking how much is
Course II's machinery plus a short tail:

1. **Everything in `COURSE_II_SCOPE.md` §5** — seeded streams,
   failures, stochastic schedules, replication orchestration. The
   disturbance ensemble *is* Course II's apparatus.
2. **Reactive policy as a declared artifact.** Reference solutions
   today are scripted *builds*; viability variants need scripted
   *behaviors* — closed-loop policies (S3 reallocation, S4 expansion
   triggers) declared in the scenario, hash-bearing, executed by
   circuits where possible and fisl-core runtime where not. This is
   the big new primitive, and it is also exactly "control
   sophistication" becoming a first-class, declarable buffer — likely
   wanted by late Course II/III regulation labs anyway.
3. **Environmental drift knobs.** Parameterized patch richness or
   accelerated depletion; scheduled demand-mix shifts; possibly
   abstracted attack pressure via `supply_loss`-style ports rather
   than live biters (determinism and measurement stay clean).
4. **Long horizons.** Viability is a long-run property; runs are
   longer than any current lab. Headless speed helps; the
   steady-state/transient validity discipline Course II introduces
   becomes load-bearing.
5. **Role-scoped visibility.** ADR 0011's audiences extended toward
   named roles — already anticipated by the ADR itself and
   `ARCHITECTURE.md` §22.
6. **Multi-product flows.** The honest big-ticket item: divisions
   producing a *mix* is what makes the resource bargain and demand
   shifts non-trivial, and multi-product scheduling is explicitly
   parked as coverage gap #4 / "a different scenario-model axis." The
   VSM course inherits that work. It cannot be smuggled in as a side
   effect; it is a prerequisite with its own design arc.

---

## 8. Where it could slot (without moving anything)

The settled sequence is untouched: Course I (deterministic physics) →
Course II (variability and buffering) → Course III opening with
regulation as a subject (Ashby). Two options for what follows that
opening:

- **Option A — Course III is "Regulation and the Viable Factory."**
  Ashby's law and regulator design first (as planned), then the §4
  gallery as the second half: requisite variety forcing structure, the
  variants, Cybersyn instrumentation, the recursion coda. The
  multiplayer organizational laboratory becomes Course IV — or more
  honestly, the *research seminar* that `ARCHITECTURE.md` §29 already
  insists it should initially be — now equipped with control
  conditions from Course III.
- **Option B — a parallel worked-examples strand.** No course
  apparatus: the gallery as an essay-plus-scenario series (the
  "variants gallery"), built opportunistically as demos when machinery
  happens to exist, harvested into Course III later if it earns it.

Lean: **A as the destination, B as the on-ramp.** One variant pair —
V0 versus V1, which needs no stochastics at all, only a province with
and without interlocks — would already make a striking demonstration
and could in principle be built with today's deterministic machinery.
Even that waits behind the standing gates: Course I's external-learner
gate first, Course II's foundations second. Daydreams queue like
everything else.

---

## 9. Readings shelf

The course-text anchors, playing the role Hopp & Spearman play for
Courses I–II:

- Stafford Beer, *Brain of the Firm* (2nd ed.) and *The Heart of
  Enterprise* — the model itself.
- Stafford Beer, *Diagnosing the System for Organizations* — the
  workbook; nearly a lab manual for §5 mode 1.
- Stafford Beer, *Designing Freedom* — the short, humane statement of
  why any of this matters.
- Eden Medina, *Cybernetic Revolutionaries* — Cybersyn as history;
  pairs with the MIT Press overview already cited in
  `RESEARCH_NOTES.md` §6.
- Espejo & Reyes, *Organizational Systems* — the modern systematic
  treatment, useful where Beer is oracular.
- Pickering, *The Cybernetic Brain*, for intellectual context.

---

## 10. Open questions (for whenever this stops being a daydream)

1. **Is the failure-signature claim true?** The entire course rests on
   ablations producing distinct, predicted signatures. The cheapest
   falsification probe is the V0/V1 pair under determinism — worth
   doing as a spike long before any course commitment.
2. **Policy representation.** Circuits only (learner-legible, in-world,
   but limited) versus runtime Lua policies (expressive, but the
   organization becomes partly invisible)? Lean: circuits wherever
   variety permits — an organization you can *walk through* is the
   pedagogical point — with runtime policies reserved for S4-scale acts
   (blueprint placement) that circuits cannot express.
3. **Live biters or abstracted pressure?** Live evolution is vivid and
   genuinely environmental; abstracted `supply_loss`-style pressure is
   measurable and deterministic-friendly. Possibly: abstracted for
   claims, live for the trailer.
4. **Where does the multi-product axis get designed?** Here, or as its
   own arc that this course consumes (as Course III scheduling was
   sketched)? The answer decides how real Option B's on-ramp is.
5. **Naming.** "The Viable Factory" is this memo's working title for
   the gallery/course; better titles welcome.
