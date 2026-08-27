# Course II Scope — Variability

**Status:** draft for review (first written 2026-08-27). Once agreed,
this becomes the plan of record for Course II the way `ROADMAP.md`'s
plan tracks Course I; the ADRs it calls for are where decisions get
settled.

Anchors: `ARCHITECTURE.md` §4.2 (Layer II — the disturbance list and
the Variability Buffering Law) and §21 (the three buffer currencies);
`CONCEPT_COVERAGE.md` (the Hopp & Spearman chapters this course owns:
8, 9, the stochastic halves of 2/10/18, plus the ch. 12 scrap decision).

---

## 1. Thesis

Course I ends on a deliberately planted cliff, three times over: Lab 6's
40/min homework ("what do you buy insurance with — inventory, capacity,
or time?"), Lab 7's knee ("operating *at* W₀ is the last thing
determinism can teach"), and every chapter's closing "what the
simulation assumed away: variability." Course II is the payoff:

> **In a deterministic world, every buffer above the minimum is waste.
> In a variable world, buffering is the law — and the only choices are
> which currency, how much, and where.**

The learner promise: by the end, you can look at a system with declared
variability and answer the §21 question — *the least costly combination
of inventory, spare capacity, response time, and control sophistication
that keeps the factory viable* — with measurements, not vibes.

## 2. First principles (carried over, one changed)

Everything in Course I's measurement discipline survives unchanged:
declared boundaries, half-open windows, explicit denominators, censoring
honesty, objectives without scores, conservation audited by census. One
principle is *transformed*:

- **Determinism becomes seeded randomness.** Variability is never
  ambient noise: every random stream is declared in the scenario
  (distribution + parameters) and derived from the run's seed. The same
  seed reproduces the run bit-for-bit — a "random" experiment is still
  an experiment. Different seeds are different *controlled conditions*
  of the same experiment: identical resolved scenario hash, different
  reproducibility fingerprint. (The existing identity model already
  expresses this — `experiment_seed` is in `RunConfiguration`, not the
  scenario hash. Course II finally uses that door.)

Two new disciplines join:

- **One seed proves nothing.** Course I could cite a single run because
  determinism made it the population. Course II reports are per-seed;
  *claims* require seed sweeps, and the tooling must make "n = 10 seeds,
  mean ± CI" as easy as one run is today.
- **Warmup becomes a real question.** Course I's warmup filled belts;
  Course II's must approach steady state under randomness, and
  "transient vs steady-state window" becomes part of validity reporting
  rather than a fixed convention.

## 3. The physics curriculum

| Concept | H&S | Where it lands |
|---|---|---|
| Variability described honestly: distributions, CV/SCV, why the mean lies | ch 8 | II-0, II-1 |
| Queueing behavior: waits explode nonlinearly near full utilization (VUT/Kingman, qualitatively then quantitatively) | ch 8 | II-2 |
| Propagation: variability flows downstream; departure processes; why *where* the wobble sits matters | ch 8 | II-3 |
| The Buffering Law: inventory / capacity / time as the three currencies | ch 9, ARCH §21 | II-4 |
| Practical worst case; the TH(w) curve family completed on Lab 7's axes | ch 7 | II-5 |
| Push vs pull robustness: CONWIP's real argument | ch 10 | II-5 |
| Yield/scrap as a variability source (resolves coverage gap #3 → Course II) | ch 12 | II-3½ or II-6 |
| Inventory under uncertainty: EOQ → base stock → (Q,r) → newsvendor (resolves gap #2 → the deterministic EOQ opens this arc, then uncertainty arrives) | ch 2 | II-6 |
| Safety capacity/utilization economics | ch 18 | II-2, II-6 |

Explicitly *not* Course II: multi-product scheduling (gap #4 — needs a
different scenario-model axis; Course III or a dedicated arc), bullwhip
(multi-echelon; strong Course III candidate), Ashby/requisite variety
(the ARCH §4.2 progression ends there, but regulation-as-subject is
Course III's opening, not Course II's closing).

## 4. Proposed lab sequence

Seven labs, mirroring Course I's arc (measure → law → control → decide):

- **II-0 — The Same Factory, Twice.** Stochastic demand only, Course I's
  line. Same seed → bit-identical (prove it); new seed → different
  numbers (accept it); many seeds → distributions with structure.
  Teaches: seeds as controlled conditions, replications, confidence
  intervals, the death of "the number." *The measurement-discipline
  chapter of the course.*
- **II-1 — The Cost of Wobble.** One machine with declared failures
  (MTTF/MTTR). Availability arithmetic (effective capacity), and the
  first sighting of the core phenomenon: mean throughput falls a little,
  waits grow a lot.
- **II-2 — The Utilization Cliff.** Sweep arrival rate against fixed
  capacity (Lab 7's sweep-by-solutions pattern, reused): CT vs
  utilization traces the hockey stick; then hold u fixed and sweep
  variability to see the V in VUT. The lab where "run everything at
  100%" dies formally.
- **II-3 — Where the Wobble Sits.** Same total variability placed
  upstream vs at vs downstream of the constraint; departure-process CV
  measured at each stage. (Optional half-lab here or folded into II-6:
  **scrap** — the inspect stage fails a seeded fraction; yield becomes a
  flow-basis question and the conservation ledger meets its first loss
  port.)
- **II-4 — The Three Buffers.** fp06's homework made real: a jittery
  supplier and a fixed service requirement; three reference solutions
  buy feasibility with inventory, capacity, and time respectively —
  same objective conjunction, three different bills. The Buffering Law
  as a comparison table.
- **II-5 — Push, Pull, and the Practical Worst Case.** Lab 7's CONWIP
  gate, unmodified, in a variable world: sweep w again, overlay the new
  TH(w) points on Course I's deterministic curve — the PWC gap *is* the
  cost of variability, drawn on axes the learner already owns. Then
  push vs CONWIP under failures: which degrades gracefully, and why.
- **II-6 — Capstone: Viable Under Uncertainty.** The §21 question as a
  scenario: uncertain demand + failures + a service requirement +
  (new) declared *costs* on inventory, capacity, and lateness — the
  first time overbuilding is priced rather than prevented (ARCH §4.2's
  instruction). Objectives machinery already handles the feasibility
  side; a cost *report* (not a score — costs are measurements, the
  requirement/preference split stays) handles the rest. The inventory
  arc (EOQ→(Q,r)→newsvendor) lives in this lab's interludes.

Interludes continue the Course I pattern (theory the labs earned, claims
the next lab tests): distributions & CIs (before II-0/II-1), the VUT
relationship (before II-2), the Buffering Law (before II-4), inventory
models (before II-6).

## 5. Engineering scope

New capability, in dependency order. Each numbered item wants an ADR
before code; none moves an existing scenario's hash (new resolved keys
appear only when a scenario uses the feature — the compiler discipline
already in force).

1. **Randomness semantics** (the foundation ADR): named random streams
   declared per consumer (`supply.schedule.type: poisson|...`,
   `failures:`, `yield:`), each stream's sequence derived from
   (experiment_seed, stream name) via a runtime PRNG we own (a simple
   LCG/PCG in fisl-core Lua — engine-independent, portable to the lupa
   stub for unit fixtures). Determinism contract: same seed + same
   resolved scenario → identical telemetry, cross-checked like
   everything else.
2. **Stochastic schedules** for supply and demand: at minimum
   exponential/Poisson and a bounded-uniform; declared like constant
   schedules, resolved into the observation plan.
3. **Availability injection** (failures): runtime toggles
   `entity.active` per seeded MTTF/MTTR draws; machine-state
   classification already has the right bucket (`unavailable`) and
   eligibility semantics — a failure is *not* a membership change.
   Needs a runtime-validation fixture (RV: does `entity.active = false`
   behave as clean preemption on 2.0.77 — craft progress frozen,
   inserters blocked, status readable?).
4. **Scrap/yield**: seeded per-craft loss at a declared stage; flow
   schema already carries `loss_ports` — this activates it, with
   conservation extended (admissions = completions + losses + ΔWIP) and
   census still exact.
5. **Replication orchestration**: `fisl sweep` (or `fisl solutions
   --seeds n`) running a seed matrix; summary statistics
   (mean/CI/percentiles per metric) as a first-class artifact;
   `fisl compare` learning to compare *distributions* (per-seed points
   + interval) rather than only single runs. Report validity gains
   steady-state/transient annotations.
6. **Costed reporting** (II-6 only): declared unit costs; a cost
   statement in the report as measurement, never folded into a score.

Runtime-validation additions before any lab ships: the `entity.active`
fixture (item 3), PRNG determinism across save/load and headless-vs-
interactive, and a performance check (per-tick seeded draws at the
scale of one line are trivial, but prove it).

## 6. What Course II is not

No multi-product flows, no scheduling, no bullwhip/multi-echelon, no
workforce/learning effects, no monetary optimization (costs are
*reported* in II-6, not optimized), no attempt at Ashby — regulation as
a subject belongs to Course III, which opens where II-6's comparison
table ends.

## 7. Sequencing and gates

1. Finish Course I's outstanding measurements (fp07 dataset, sandbox
   positive drill session).
2. **The external-learner gate comes first** — carried from the design
   review and still unmet: one person who is not the maintainer runs
   Lab 3 (now ideally Labs 0–3) end to end before we build a second
   course on top of the first. Course II design can proceed on paper in
   parallel; Course II *code* waits for the gate.
3. ADR for randomness semantics (item 5.1) → runtime spike + RV fixtures
   (5.2–5.4 minimally) → II-0 built end to end as the template lab →
   remaining labs in order, one at a time, measured before authored —
   the Course I discipline unchanged.

## 8. Open questions (decision needed, in rough order)

1. **Distribution vocabulary**: start with exponential + uniform only
   (fits every II-0..II-5 lab), or include deterministic-with-outliers
   (a "rare long stop" mode that teaches SCV vividly)? Lean: start
   minimal; add when a lab needs it.
2. **Scrap placement**: half-lab after II-3 or folded into II-6? Lean:
   II-3½ standalone — the loss-port conservation story deserves its own
   run.
3. **Costs in II-6**: declared in the scenario (hash-bearing) or a
   report-side overlay? Lean: scenario-declared — the course's whole
   ethic is that the experiment declares its terms.
4. **Course II book**: same volume (Part II of the existing book) or a
   second Quarto book? Lean: same volume, new part — one site, one
   discipline, and the cross-references (Lab 7 ↔ II-5) stay live links.
