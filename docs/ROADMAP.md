# FISL Roadmap and Status

**Maintenance rule:** this is the *living plan document*. Update it in the
same commit whenever a phase completes, an issue below opens/closes, or the
sequencing changes. Like `USER_GUIDE.md` (and unlike the ADRs), this file is
expected to change constantly. GitHub issues carry the detailed scope; this
file is the map.

Relationship to other planning documents:

- `FISL_V1_PRD.md` — the **destination** (full v1 product requirements).
- `POST_REVIEW_REVISIONS.md` — the post-design-review sequencing addendum
  (its phase-1 gate is now complete; source-of-truth order still applies).
- `RUNTIME_VALIDATION.md` — which Factorio assumptions are empirically proven.
- `CONCEPT_COVERAGE.md` — the MECE audit of Hopp & Spearman's *Factory
  Physics* against the course sequence (what's taught where, what's a
  non-goal, what's an open gap).
- **This file** — where we are, what's next, in what order, and why.

---

## Done (evidence on `main`)

| Milestone | Record |
|---|---|
| Design review + revision pass (ADR 0017/0018, hash split, RV gate) | `DESIGN_REVIEW.md`, `POST_REVIEW_REVISIONS.md` |
| Runtime-validation spike vs real 2.0.77 — 5 findings, all resolved | [#2](https://github.com/MetaCoding-io/FactorioResearch/issues/2), `RUNTIME_VALIDATION.md` § Spike findings, `tests/integration/evidence/` |
| Compiler / controller / Lua runtime / conservation-ledger WIP / census / telemetry / provenance | Issue [#2](https://github.com/MetaCoding-io/FactorioResearch/issues/2) Stage B checklist |
| Verified fp03 Lab 3 baseline (builder + acceptance run) | [#4](https://github.com/MetaCoding-io/FactorioResearch/issues/4), `scenarios/factory-physics/fp03-littles-law/verification-summary.json` |
| **First human-played experiment** (COMPLETED, cross-verified, bit-identical to headless verification) | run `01M0XP8VJ78KXRC8DB6BATBW39`, closing comment on [#2](https://github.com/MetaCoding-io/FactorioResearch/issues/2) |
| Living user guide | `USER_GUIDE.md` |
| `fisl compare` + scripted reference solutions (`--solution`) + fp03 solution A | [#6](https://github.com/MetaCoding-io/FactorioResearch/issues/6), `scenarios/.../solutions/a-pull-signal/` |
| Course text scaffold (Quarto book, Lab 3 chapter drafted) | `course/` |
| Machine-state classification (ADR 0007): classifier + runtime adapter + `production_state`/`state_fraction` metrics, **all six per-state fixtures passed on real 2.0.77** (incl. RV-007 brownout: productive + energy_limited) | [#7](https://github.com/MetaCoding-io/FactorioResearch/issues/7), `factorio/fisl-core/fisl/classify.lua`, `tests/integration/test_machine_state.py` |

Confirmed runtime assumptions: RV-001/002/003/005/006/007/008/009/012;
RV-004 (straight belts). Pending: RV-004 underground/splitter, RV-011
interactive.

---

## Current phase — "Lab 3 is a complete teachable unit, then Lab 4"

In dependency order (later items consume earlier ones):

| # | Work | Issue | Unlocks |
|---|---|---|---|
| 1 | `fisl compare` — side-by-side run debrief, no scalar score | [#6](https://github.com/MetaCoding-io/FactorioResearch/issues/6) | Lab 3 as a full experiment pair (**done**) |
| 2 | Machine-state classification (ADR 0007) + state fractions + RV-006/007 (**done** — 6/6 fixtures on real 2.0.77; wiring the metrics into Lab 2/4 scenarios happens with item 6, not fp03: adding them to fp03 would change its resolved hash and break comparability with existing runs) | [#7](https://github.com/MetaCoding-io/FactorioResearch/issues/7) | Labs 2 & 4 |
| 3 | Dynamic entity sets (ADR 0016, RV-012) — **done** (RV-012 confirmed on real 2.0.77; full integration suite 16/16) | [#8](https://github.com/MetaCoding-io/FactorioResearch/issues/8) | mid-run redesign; pooled denominators |
| 4 | Demand/service cohorts + on-time item rate (ADR 0008) — **done** (fixtures 2/2 on real 2.0.77; fp05 baseline verified; three-run reference dataset committed — push/pull-tuned identical 100% on-time & 3.02 s p95 at 2.7× WIP difference; over-tight pull 22.5% on-time with censored p95, exactly the backlog arithmetic) | [#9](https://github.com/MetaCoding-io/FactorioResearch/issues/9) | Lab 5 push/pull |
| 5 | Objectives + full visibility enforcement (ADR 0011/0012) — **done** (requirement/preference objectives, PASS/FAIL/UNDETERMINED with conjunction, report + compare feasibility framing, allowlist-driven post-run GUI, objective-rule disclosure; fp05 now declares the canonical service requirement + WIP preference, which **changes its resolved hash — regenerate**: `fisl build-baseline scenarios/factory-physics/fp05-push-and-pull` then `fisl solutions … --run --json --svg`) | [#10](https://github.com/MetaCoding-io/FactorioResearch/issues/10) | Labs 5/6 evaluation |
| 6 | Lab content: builder generalization, Labs 0–6, RV partial fixtures, per-lab reference solutions + course chapters — **in progress: all seven labs authored and measured through Lab 5; Lab 6 (capstone) authored; all six theory interludes + notation/readings appendices authored (the lab-course-book structure — see `CONCEPT_COVERAGE.md`)** (fp06 scenario: scheduled supply 36/min into a finite 100+10 warehouse + 33/min demand vs the 30/min constraint; new `supply_loss` metric + telemetry; buffer-vs-upgrade reference solutions where the buffer run is INFEASIBLE by the declared objectives; chapter + LAB6 layout registered. Remaining: **regenerate fp05** (objectives changed its hash): `fisl build-baseline scenarios/factory-physics/fp05-push-and-pull` then re-run its solutions dataset; **build fp06**: `fisl build-baseline scenarios/factory-physics/fp06-system-optimization` then `fisl solutions scenarios/factory-physics/fp06-system-optimization --run --json course/data/lab-06-comparison.json --svg …`, cite measured numbers in the Lab 6 chapter + solution READMEs; screenshots (`fisl snap`); RV-004 underground/splitter fixtures; external-learner gate) | [#11](https://github.com/MetaCoding-io/FactorioResearch/issues/11) | the rest of the course |

**Approved course-expansion plan (in order):**

1. **N00b on-ramp** (three phases, approved 2026-08-27): ① *Before the
   First Lab* front-matter chapter (**done**); ② `fp-sandbox` "Operator
   Training" — LAB0 world + stocked toolbox, six drills graded post-run
   by a read-only `drills/check.lua` over RCON (new controller drills
   module; Drill card in `fisl report`; drills deliberately outside the
   metrics pipeline) + *The Practice Range* chapter (**built — needs
   first `fisl build-baseline scenarios/factory-physics/fp-sandbox` and
   a human drill session to validate the six predicates on real
   2.0.77**); ③ "hands you'll need" callouts in Labs 3–6 referencing
   drill ids (**done**).
2. **Scenario Author's Guide** — **done**: `docs/AUTHORING_GUIDE.md`
   (workflow, physics-design judgment incl. the fp06 transient case
   study, per-section guidance, metrics catalog with compiler
   guardrails, objective unit rules, hash discipline, layout
   registration, solution/drill doctrine, worked example, pre-flight
   checklist); `FISL_V1_SCHEMA.md` gained the missing §13.11
   `supply_loss`.
3. **Course II (variability)** and **Course III (organizational)** as
   scoped in `CONCEPT_COVERAGE.md`, plus its four open gap decisions
   (WIP-sweep lab, EOQ/batching, quality/scrap, scheduling).

**Gate carried over from the design review:** before polishing Labs 5–6
machinery, one learner who is not the maintainer runs Lab 3 end-to-end and
their friction gets folded back in (tracked in [#11](https://github.com/MetaCoding-io/FactorioResearch/issues/11)).
The freeplay-intro ambush was found only because a human sat down; every new
layer earns the same test.

---

## After v1 (unchanged from the architecture)

Layer II (controlled variability, buffering, control) and Layer III
(organizational cybernetics) remain future scenario-model extensions, not
current work — see `ARCHITECTURE.md` §21–§22 and the deferred-ADR list in
`adr/README.md`.
