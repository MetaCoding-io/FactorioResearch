# FISL Scenario Author's Guide

**Audience:** anyone creating or modifying a scenario — a lab, a variant,
a sandbox, a future course's experiment.
**Maintenance rule:** living document, like `USER_GUIDE.md`. Any change to
the authoring workflow, compiler guardrails, or package layout must update
this guide in the same commit.

Division of labor between documents:

| Question | Document |
|---|---|
| What fields exist and what do they mean? | `FISL_V1_SCHEMA.md` (the format reference, with a complete canonical example) |
| Why do the semantics work this way? | the ADRs (`docs/adr/`) |
| How do I run/build/debug what I authored? | `USER_GUIDE.md` |
| **How do I design, author, and validate a scenario well?** | **this guide** |

---

## 1. What you are building

A scenario package is a directory:

```text
scenarios/<family>/<scenario-dir>/
    scenario.yaml               # the experiment definition — the identity
    baseline.zip                # the pristine world every attempt starts from
    verification-summary.json   # recorded proof the baseline works (generated)
    solutions/<id>/             # optional scripted reference interventions
        README.md               #   course-facing rationale
        *.lua                   #   ordered steps, applied after READY
    drills/check.lua            # optional post-run practice grading (sandboxes)
```

Two ideas govern everything else:

- **The scenario and the world are separate.** `scenario.yaml` defines the
  *experiment* (boundaries, clocks, metrics, rules); `baseline.zip` is the
  *apparatus*. Editing one usually does not require rebuilding the other.
- **Identity is a hash.** The compiler canonicalizes every semantic field
  into the resolved scenario hash. Two runs are comparable iff hashes
  match. Everything in this guide ultimately serves that comparability.

## 2. The authoring workflow

In order, with no steps skipped:

1. **Design on paper first.** Choose the phenomenon, then derive the
   arithmetic (§3) — rates, buffer capacities, when the interesting thing
   becomes visible. Write down predicted numbers for the baseline and for
   each intended intervention *before touching YAML*.
2. **Write `scenario.yaml`** (§4). Start by copying the closest existing
   scenario — `fp00` is the minimal line, `fp-sandbox` the minimal
   package, `fp06` the full stack (scheduled supply, demand, objectives).
3. **`fisl validate <scenario-dir>`** after every edit. The compiler is
   deliberately strict (§5); a scenario that validates has exact tick
   arithmetic, resolved cross-references, and a printed hash.
4. **Register the world** (§6): a `LabLayout` in
   `python/fisl/controller/baseline_builder.py` plus an entry in the unit
   tests' `SCENARIO_DIRS`. Run `python3 -m pytest tests/unit -q` — the
   layout tests catch overlaps, zone escapes, and flow-direction mistakes
   before Factorio ever runs.
5. **`fisl build-baseline <scenario-dir>`** on a machine with Factorio:
   builds the world, verifies entity counts in-game, then runs the full
   scenario headlessly and requires a completed lifecycle, clean census,
   Lua/Python agreement, and (if you declared machine-state metrics)
   complete classification coverage. Commit `baseline.zip` **and**
   `verification-summary.json`, with the baseline sha256 in the message.
6. **Author reference solutions** (§7) and produce the reference dataset:
   `fisl solutions <scenario-dir> --run --json ...`.
7. **Compare measured numbers against your step-1 predictions.** A
   mismatch is a finding, never a formatting problem: either your physics
   was wrong (fix the scenario or the prediction — see the fp06 story in
   §3) or the apparatus is (find it now, not after learners do).
8. Only then: cite measured numbers in course material.

## 3. Designing the physics

Everything in a FISL world is deterministic, so a scenario is designed
with arithmetic, and the arithmetic is checkable at the whiteboard.

**Machine rates.** Craft time = recipe seconds ÷ machine speed; rate =
60 ÷ craft time per minute:

| | speed | machine (2 s) | inspect (1 s) | finish (1 s) |
|---|---|---|---|---|
| assembling-machine-1 | 0.5 | 4.0 s → 15/min | 2.0 s → 30/min | 2.0 s → 30/min |
| assembling-machine-2 | 0.75 | 2.67 s → 22.5/min | 1.33 s → 45/min | 1.33 s → 45/min |
| assembling-machine-3 | 1.25 | 1.6 s → 37.5/min | 0.8 s → 75/min | 0.8 s → 75/min |

**Buffer inventory is part of your design whether you meant it or not.**
A belt holds ~4 items per lane per tile; machine input slots buffer more;
the FISL port chest holds exactly 100 items (its prototype has one slot).
Sum the capacity between any two points before predicting when a queue
becomes visible.

**The transient can hide your phenomenon** — the case study every author
should internalize: fp06 was designed to overflow its warehouse
(supplier 36/min vs a 30/min line, ~110 units of warehouse capacity) and
its first real run measured only 0.8% loss over a 10-minute window. The
cold-start belt fill and machine buffers drained the warehouse during
warmup, and the structural 6/min surplus spent ~12 minutes refilling that
space before any loss occurred. The fix was a 15-minute window; the
lesson is general: **compute how much buffer space the cold start
creates, and make the measured window long enough to outlive it — or
make the masking itself the lesson, as Lab 6 now does.**

**Phase roles.** `warmup` exists to hand the measured window a filled,
steady line (and to make Little's Law near-exact — equal inventory at the
window's edges). A tail phase (`service_tail`) exists to observe
deadlines: any `on_time_item_rate` must satisfy the compiler's deadline
property — the horizon must reach the *last* selected cohort's deadline —
so budget `max_wait` past the cohort window's end.

**Wires reach 9 tiles** and `connect_to()` returns false without raising.
Any circuit design (in a solution or expected of learners) must place
relays accordingly and check return values.

## 4. Writing `scenario.yaml` — judgment per section

Format details live in `FISL_V1_SCHEMA.md`; this is what to *decide*.
Unknown fields are rejected everywhere (`extra: forbid`) — a typo fails
validation instead of silently becoming a different experiment.

- **`experiment.phases`** — half-open, tick-exact, ids unique. Durations
  accept `"90s"`, `"10m"`, `"600t"`. Think in the three roles above.
- **`zones`** — the declared boundary. Must contain the whole layout
  *and* everything learners will plausibly build (toolbox, drill space);
  `entity_containment: flag` reports escapes rather than preventing them.
- **`ports`** — a source must declare supply; sinks must not. `replenish`
  (target N) models an infinitely patient supplier; `scheduled` (constant
  rate + optional finite `external_buffer`) models one who ships on a
  clock — required if you ever want `supply_loss`. Sink `demand` ids are
  globally unique (each is a distinct demand process, ADR 0008).
- **`flows`** — every port material needs a positive coefficient in the
  conserved basis; entry/completion ports must exist, match direction,
  and belong to the flow's system. The conservation ledger and census are
  only as honest as this mapping.
- **`entity_sets`** — need at least one positive selector; membership is
  dynamic (ADR 0016), so machines learners add/remove mid-run join and
  leave eligibility correctly. Keep `exclude_roles: [fisl_apparatus]`.
- **`metrics`** — the catalog with each type's compile-time contract:

| type | needs | the compiler will reject |
|---|---|---|
| `wip` | a flow; census cadence (e.g. `every: 60t`, tolerance 0) | unknown flow; bad census duration |
| `current_value` | a `wip` source | non-point-state sources |
| `aggregate` | source + aggregation + phase window | unknown window/source |
| `throughput` | flow + window; `boundary: completion` (default) or `entry` | unknown flow/window |
| `cycle_time` (`little_law_derived`) | a `time_mean` aggregate of a ledger WIP + a **completion**-boundary throughput, same flow, same window | entry-boundary throughput ("admission rate is not system throughput"); mismatched flows; unlike windows (ADR 0010 §26) |
| `production_state` | an entity set; `crafting_machine` adapter | unknown entity set |
| `state_fraction` | a `production_state` source + one headline state + window | non-production-state source. (`coverage_missing` is not a state and cannot be requested) |
| `on_time_item_rate` | a demand id + cohort window + `max_wait` + observation horizon | horizon short of the last cohort's deadline — extend the tail phase; `max_wait` < 1 tick |
| `demand_wait_percentile` | demand + windows + `p` in (0,1) | as above; percentile prints `censored` at runtime if any selected unit is unfulfilled |
| `supply_loss` | a source port with **scheduled** supply and a **finite** external buffer + window | replenish supply (nothing scheduled to lose); unbounded buffer (loss impossible) |

- **`objectives`** — requirements take exactly one of
  `minimum`/`maximum`/`range` (range needs min < max); preferences take
  only a direction. Thresholds are in the metric's canonical unit:
  fractions in [0, 1] for `on_time_item_rate`/`state_fraction`/
  `supply_loss`, `"55/min"` strings for throughput, `"30 s"` durations
  for cycle time and wait percentiles, work units for aggregates. String
  thresholds are only valid for rate/time metrics. Metric types outside
  that list have no scalar objective semantics and are rejected. There is
  no weight field and never will be (ADR 0012).
- **`visibility`** — allowlists per audience; every referenced metric and
  objective must exist. Decide deliberately what the learner sees live
  (usually just `current_wip`), what the post-run panel can honestly
  finalize, and remember: objective *rules* may be disclosed, verdicts
  appear only in the report.
- **`learning`** — free-form and excluded from the hash: the one section
  you can edit without consequences.

## 5. Hash discipline

The resolved hash is the experiment's identity. In practice:

- Semantic edits (phases, ports, metrics, objectives, visibility) change
  it; `learning` and YAML comments don't. `fisl validate` prints the hash
  — check it moved (or didn't) as you intended.
- Once a scenario has shipped runs or a reference dataset, a hash change
  **orphans them**: re-run `build-baseline` (if the world changed) and
  regenerate the dataset, and say so in the commit message. fp05's
  objectives retrofit is the worked precedent.
- New *compiler features* must not move existing hashes: new resolved
  keys are emitted only when the feature is used. If you extend the
  compiler, add a hash-pin test like the existing FP03/FP04 pins.
- The reproducibility fingerprint additionally pins the baseline sha256,
  seed, versions — that's what makes reruns bit-identical evidence.

## 6. Building the world

Register a `LabLayout` (see `LABSANDBOX` for the minimal example): ports,
machines `(x, prototype, recipe)`, substations, `toolbox_items` (what
learners may build with — never measured), and `expected_counts` — an
independent in-game census the builder checks before saving. The layout
unit tests then enforce, per layout: no overlapping footprints, nothing
outside the zone, bindings matching `scenario.yaml`, recipes forming a
prefix of the conserved chain, and west→east flow monotonicity.

If your scenario needs geometry the shared `line_placements()` can't
express, extend the builder rather than hand-editing a save: the whole
point is that worlds are reproducible from code.

## 7. Scripted reference solutions

Each `solutions/<id>/*.lua` step is sent as **one** `/silent-command`
line: full-line `--` comments are stripped, inline `--` is rejected,
3500 chars max per step, and every step must end by printing exactly
`solution-step-ok` — anything else fails the run loudly. Doctrine,
learned the hard way (fp03 v2's silent no-op):

- **Check every fallible return.** `connect_to()` reach failures,
  `create_entity` nils, missing finds — convert each into a loud
  `solution-step-fail: <why>`.
- Wrap risky spans in `pcall` and print the error; never let a step
  half-apply silently.
- Solutions run after READY, before start — same scenario, same baseline,
  so `fisl compare` attributes the whole delta to the intervention. Step
  hashes land in run provenance automatically.

## 8. Drill checks (sandboxes)

A package may carry `drills/check.lua`: a *read-only* world inspection
run over RCON after an interactive run completes, printing one JSON
document (`{"drills": [{"id", "passed", "detail"}…]}` via
`helpers.table_to_json`). Same transmission rules as solution steps.
Drills grade practice and are deliberately outside the metrics pipeline:
no metric, no validity, no hash, and a crashing check degrades to a
warning. If a drill constant depends on the layout (fp-sandbox's baseline
belt count), add a lockstep unit test.

## 9. Worked example — designing a small lab from scratch

Say we want a two-machine lab about *where a buffer helps*: M1 fast
(asm-3, machining, 37.5/min) feeding M2 slow (asm-1, inspect, 30/min).

1. **Physics first.** Constraint 30/min; M1 blocked ≈ 1 − 30/37.5 = 20%
   of the time at steady state. Cold start: with ~20 belt tiles between
   ports (~80 items of lane capacity) the line swallows roughly a minute
   of supply before steady state — so warmup ≥ 90 s, and a 5-minute
   measured window gives 150 completed workpieces (comfortably beyond
   census noise, which is zero anyway — this is about learner-visible
   magnitudes).
   Predictions to write down: TH 30/min exactly; a chest spliced above M2
   drops M1's blocked fraction toward 0 while TH stays 30/min and average
   WIP rises by ≈ the chest's steady contents.
2. **YAML.** Copy `fp01` (already two unequal machines); rename ids; set
   phases `warmup: 90s`, `measured: 5m`. Metrics: `line_wip` (census
   60t/0), `current_wip`, `average_wip` (time_mean, measured),
   `measured_throughput`, `machine_state` over a dynamic `line_machines`
   set, `fraction_productive` + `fraction_blocked`. No objectives — this
   is a measurement lab; visibility: live `current_wip` only.
3. **Validate**, fix what the compiler names, note the hash.
4. **Layout**: `LabLayout` with the two machines, a toolbox holding
   `wooden-chest: 2, fast-inserter: 4`, expected counts; `SCENARIO_DIRS`
   entry; unit tests green.
5. **Build + verify** on a Factorio machine; commit baseline + summary.
6. **Solutions**: `a-buffer-above-constraint` (the chest splice, checked
   returns, step-ok) and — the deliberately wrong one — a buffer *below*
   the constraint, which changes nothing; the comparison table teaches
   placement.
7. Run the dataset, check every prediction from step 1, then write the
   chapter around the measured numbers.

## 10. Pre-flight checklist

- [ ] Predictions written down before the first run
- [ ] `fisl validate` clean; hash noted
- [ ] Layout registered; `python3 -m pytest tests/unit -q` green
- [ ] `fisl build-baseline` verified; baseline + verification summary committed with sha256
- [ ] Warmup outlives the cold-start transient (do the buffer arithmetic)
- [ ] Every deadline-bearing metric has an observing tail phase
- [ ] Solutions check every fallible return and fail loudly
- [ ] Reference dataset regenerated after any hash change
- [ ] Course text cites only measured numbers
