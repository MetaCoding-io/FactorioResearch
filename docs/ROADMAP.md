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

Confirmed runtime assumptions: RV-001/002/003/005/006/007/008/009; RV-004
(straight belts). Pending: RV-004 underground/splitter, RV-011 interactive,
RV-012.

---

## Current phase — "Lab 3 is a complete teachable unit, then Lab 4"

In dependency order (later items consume earlier ones):

| # | Work | Issue | Unlocks |
|---|---|---|---|
| 1 | `fisl compare` — side-by-side run debrief, no scalar score | [#6](https://github.com/MetaCoding-io/FactorioResearch/issues/6) | Lab 3 as a full experiment pair (**done**) |
| 2 | Machine-state classification (ADR 0007) + state fractions + RV-006/007 (**done** — 6/6 fixtures on real 2.0.77; wiring the metrics into Lab 2/4 scenarios happens with item 6, not fp03: adding them to fp03 would change its resolved hash and break comparability with existing runs) | [#7](https://github.com/MetaCoding-io/FactorioResearch/issues/7) | Labs 2 & 4 |
| 3 | Dynamic entity sets (ADR 0016, RV-012) — **implemented; remaining: run `FACTORIO_BIN=… python3 -m pytest tests/integration/test_dynamic_membership.py` on a Factorio-capable machine and commit evidence** | [#8](https://github.com/MetaCoding-io/FactorioResearch/issues/8) | mid-run redesign; pooled denominators |
| 4 | Demand/service cohorts + on-time item rate (ADR 0008) | [#9](https://github.com/MetaCoding-io/FactorioResearch/issues/9) | Lab 5 push/pull |
| 5 | Objectives + full visibility enforcement (ADR 0011/0012) | [#10](https://github.com/MetaCoding-io/FactorioResearch/issues/10) | Labs 5/6 evaluation |
| 6 | Lab content: builder generalization, Labs 0–2/4/6, RV partial fixtures, per-lab reference solutions + course chapters | [#11](https://github.com/MetaCoding-io/FactorioResearch/issues/11) | the rest of the course |

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
