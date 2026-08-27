# Concept Coverage Map — Factory Physics ↔ FISL Courses

**Maintenance rule:** living planning document, like `ROADMAP.md`. Update it
whenever a lab/interlude is authored, a course is scoped, or a mapping
decision changes. This is an *authoring tool*, not learner-facing content;
the learner-facing distillation of it is the per-interlude "Further
reading" notes and (planned) readings-map appendix in `course/`.

## Purpose

Two commitments, in tension, both deliberate:

1. **Not a companion.** The course is not structured by Hopp & Spearman's
   *Factory Physics* (3rd ed.), does not follow its chapter order, and
   never reproduces its text. Our spine is the lab sequence and the
   measurement discipline (boundaries, windows, denominators, validity).
2. **MECE against it.** Every concept the book teaches should map to
   exactly one place in our course sequence — this course (Course I,
   deterministic), the planned variability course (Course II, Layer II in
   `ARCHITECTURE.md` §21), the planned organizational course (Course III,
   Layer III §22) — or to an **explicit non-goal with a stated reason**.
   No concept silently unaccounted for.

The table below is that audit. "Gap" rows are concepts with no home yet —
each needs a decision, not a shrug.

## The map (H&S 3rd ed. → FISL)

Status: ✅ taught now · 🔜 planned in a scoped course · ❌ explicit
non-goal · ⚠️ gap (decision needed).

| H&S | Concept cluster | Where in FISL | Status |
|---|---|---|---|
| Ch 1 — Manufacturing in America | Industrial history, the American production narrative | Non-goal as content; interludes may cite it for context. Reason: history is not lab-teachable and the book already tells it well — this is exactly what "readings map" pointers are for. | ❌ |
| Ch 2 — Inventory Control: From EOQ to ROP | EOQ / setup-vs-holding trade, Wagner–Whitin, (Q,r) reorder points, news vendor | Split: **EOQ/batching is deterministic** and lab-able — candidate Course I extension lab (changeover cost modeled as a recipe-swap delay, batch size as the dial). (Q,r) and news vendor need stochastic demand → Course II inventory unit. | ⚠️ / 🔜 II |
| Ch 3 — The MRP Crusade | MRP/MRP II/ERP mechanics, push planning logic | Mechanics are a non-goal (software archaeology, not physics). The *push-control idea* MRP embodies is taught: Lab 3 run 1 and Lab 5's push reference run are MRP-style admission made visible. | ❌ (idea ✅ Labs 3/5) |
| Ch 4 — From the JIT Revolution to Lean | JIT, kanban, lean, waste | Pull-as-admission-control ✅ Lab 3 (pull gate) + Lab 5 (pull vs push under a customer). Kanban *card mechanics* vs CONWIP comparison → Course II (their difference only matters under variability). Lean's waste taxonomy → Course I interlude candidate (we already price queue-waste exactly via Little's Law). | ✅ partial, 🔜 II |
| Ch 5 — What Went Wrong? | Why slogans failed; the case for laws over fads | This is the course's founding argument — `course/index.qmd` and the interlude program carry it. No lab needed. | ✅ (framing) |
| Ch 6 — A Science of Manufacturing | Models vs reality, laws, objectives, "the essence is trade-offs" | ✅ Deeply: FISL's whole apparatus (declared boundaries, validity, ADR 0011 no-scalar-score, ADR 0012 objectives, Lab 6's INFEASIBLE framing) *is* this chapter operationalized. Named explicitly in the Rules of Evidence and Objectives interludes. | ✅ |
| Ch 7 — Basic Factory Dynamics | TH, WIP, CT, Little's Law, r_b, T_0, W_0, best/worst/practical-worst-case curves | Core of Course I: Labs 0–4 + interlude "The Accounting of Flow" (derives Little's Law, defines r_b/T_0/W_0, states the best-case curves). **Practical worst case requires variability → Course II.** Gap worth closing in Course I: a WIP-sweep lab tracing TH(w)/CT(w) empirically (pull gate at w = 1, 2, 4, 8, …) — the data would draw H&S's signature curves from live runs. | ✅ / ⚠️ sweep lab / 🔜 II (PWC) |
| Ch 8 — Variability Basics | CV, process/flow variability, Kingman (VUT), propagation, pooling | Course II core. Layer II scenario models (controlled stochastic craft times / supply jitter) are the planned apparatus. Not teachable in Course I by design — determinism is Course I's stated assumption. | 🔜 II |
| Ch 9 — The Corrupting Influence of Variability | Buffering law (inventory/capacity/time), degradation laws, variability pays | Course II core. Hook already planted: Lab 6's 40/min homework ends on "what do you buy insurance with — inventory, capacity, or time?" verbatim setup for the buffering law. | 🔜 II |
| Ch 10 — Push and Pull Production Systems | Push vs pull defined by WIP cap, CONWIP, robustness | Definition + behavior ✅ Labs 3/5 (admission control, WIP cap, over-tight throttle failure mode). CONWIP-vs-kanban-vs-MRP *robustness* comparison needs variability → Course II. | ✅ partial, 🔜 II |
| Ch 11 — The Human Element | Motivation, learning, people in systems | Course III (organizational cybernetics, Layer III) candidate; mostly a non-goal for simulation (FISL measures systems, not people). The one Course I touchpoint: the labs' own pedagogy (learner as operator) — not curriculum content. | 🔜 III / ❌ |
| Ch 12 — Total Quality Manufacturing | Quality, SPC, quality–variability link | Gap. Factorio has no native defects; FISL could model inspection/scrap probabilistically (the `inspect-workpiece` stage is already in every line — a Layer II scrap recipe makes yield a measurable flow). Decision needed: Course II unit (quality as a variability source) vs non-goal. | ⚠️ |
| Ch 13 — A Pull Planning Framework | Hierarchical planning with pull foundations | Course II/III synthesis material; premature before variability exists. | 🔜 II/III |
| Ch 14 — Shop Floor Control | CONWIP loops in practice, statistical throughput control | Course II (needs variability for the "statistical" half; CONWIP loop mechanics could preview in the Course I WIP-sweep lab if built). | 🔜 II |
| Ch 15 — Production Scheduling | Sequencing, dispatching, makespan, bottleneck scheduling | Gap. Deterministic scheduling *is* lab-able (it's Course I physics) but needs multi-product scenarios — a real scenario-model extension (multiple flows, shared machines, changeovers). Decision: scope a "Course I.5" multi-product arc or defer to Course II. | ⚠️ |
| Ch 16 — Aggregate and Workforce Planning | LP planning, workforce sizing over horizons | Non-goal for the simulation courses (planning math over quarters doesn't fit a 13-minute run). Candidate for Course III reading-only treatment. | ❌ / 🔜 III |
| Ch 17 — Supply Chain Management | Multi-echelon inventory, bullwhip, positioning | Seed planted ✅ Lab 6 (external scheduled supplier, finite buffer, supply loss — the first two-party system). Bullwhip proper needs multi-echelon + information delay → strong Course II/III scenario candidate (Factorio chains of factories are a natural fit). | ✅ seed, 🔜 II/III |
| Ch 18 — Capacity Management | Capacity setting, utilization economics | Deterministic capacity ✅ Labs 1, 2, 4, 6 (installed vs achieved, constraint, capacity as the fix that works). Utilization economics under variability (why 100% is dangerous, not just pointless) → Course II. | ✅ partial, 🔜 II |
| Ch 19 — Synthesis | Pulling the laws together on cases | Lab 6 is Course I's synthesis; each course should end with one. | ✅ (per course) |

## Reverse direction — what we teach that the book doesn't

MECE runs both ways; these are ours, and they are why the course isn't a
companion:

- **Measurement discipline as first-class content**: declared boundaries,
  half-open windows, explicit denominators, validity flags, censoring
  (Lab 5's p95 refusing to print), conservation-ledger cross-checks.
  H&S *assumes* clean numbers; we teach where numbers come from.
- **Reproducibility as apparatus**: bit-identical replication, resolved
  hashes, the run as an auditable scientific record.
- **Objectives without scores** (ADR 0011): feasibility conjunctions,
  UNDETERMINED as an honest verdict, INFEASIBLE framing — H&S ch 6 gestures
  at trade-offs; we operationalize the refusal to collapse them.
- **Instrumentation ethics**: what the operator may see mid-experiment
  and why (visibility allowlists, no provisional verdicts).

These threads now have their interludes: measurement discipline and
reproducibility in "The Rules of Evidence", censoring in "The Customer's
Clock", objectives in "Objectives Without a Score" — with the notation
appendix as the formal spine and the readings-map appendix as the
learner-facing distillation of this file's forward direction.

## Open decisions (the ⚠️ rows)

1. **WIP-sweep lab** (ch 7 curves): cheap to build — fp03's world, pull
   gate thresholds swept, plot TH(w) and CT(w). Strong candidate for the
   first post-v1 Course I addition.
2. **EOQ/batching lab** (ch 2): deterministic, teachable, needs a
   changeover mechanic. Medium effort.
3. **Quality/scrap** (ch 12): needs Layer II randomness; decide whether it
   joins Course II as a variability source or is a non-goal.
4. **Scheduling arc** (ch 15): needs multi-product scenario models — the
   largest scoping question on this list.
