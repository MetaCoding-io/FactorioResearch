# FISL User Guide

**Audience:** anyone running, building, or developing FISL — instructors,
scenario authors, developers.
**Maintenance rule:** this is a *living operational document*. Any change to
the CLI, run workflow, artifacts, or setup steps must update this guide in
the same commit. Unlike the ADRs (settled decisions), this file is expected
to change constantly.

Documentation map — which document answers what:

| Question | Document |
|---|---|
| How do I run/build/play/debug FISL? | **this guide** |
| Why does FISL measure things the way it does? | `docs/adr/` (ADRs 0001–0018) |
| What is the scenario file format? | `docs/FISL_V1_SCHEMA.md` |
| What is v1 supposed to contain eventually? | `docs/FISL_V1_PRD.md` |
| Which Factorio assumptions are empirically proven? | `docs/RUNTIME_VALIDATION.md` |
| What are the course labs? | `docs/FACTORY_PHYSICS_LABS_V1.md` |
| Where are we / what's next? | `docs/ROADMAP.md` |
| Where is the course text? | `course/` (Quarto book; see its README) |

---

## 1. What FISL is, operationally

FISL wraps a controlled experiment around an ordinary Factorio game:

```text
Python controller (fisl CLI)
    │  compiles scenario.yaml, launches/configures everything,
    │  collects results
    ▼
Factorio server (headless process, started for you per run)
    │  runs the FISL mods: experiment clock, ports, measurement
    ▼
Factorio client (the normal game — you/the learner connect to play)
```

You never run the server yourself; `fisl run` does. You *do* launch the
graphical client yourself (section 5).

A **scenario package** is a directory like
`scenarios/factory-physics/fp03-littles-law/` containing:

- `scenario.yaml` — the experiment definition (phases, ports, metrics…);
- `baseline.zip` — the pristine Factorio world every attempt starts from;
- `verification-summary.json` — recorded proof the baseline works.

A **run** is one attempt: it gets a unique run id and a directory
`runs/<run_id>/` with everything needed to audit or reproduce it (section 6).
Retrying = just run again; the baseline is never modified.

---

## 2. One-time setup

Requirements:

- Python ≥ 3.11
- Factorio **2.0.77** — the headless server is enough for building/testing
  (free from factorio.com); playing interactively needs the full game.

```sh
git clone git@github.com:MetaCoding-io/FactorioResearch.git
cd FactorioResearch
pip install -e '.[dev]'     # quotes matter in zsh: [dev] is a glob there

# tell fisl where Factorio is (add to your shell profile):
export FACTORIO_BIN=/path/to/factorio/bin/x64/factorio

python3 -m pytest tests/unit -q   # should be all green, no Factorio needed
```

The two FISL mods (`factorio/fisl-core`, `factorio/fisl-factory-physics`)
never need manual installation — every command that starts a server copies
them into that run's isolated workspace automatically.

---

## 3. Command reference

### `fisl validate <scenario-dir>`

Compiles and checks a scenario without launching Factorio: exact tick
arithmetic, all cross-references, metric compatibility (e.g. Little's-Law
inputs must share flow and window), baseline presence + hash. Run it after
any `scenario.yaml` edit. Prints the `resolved_scenario_hash` — the identity
of the experiment semantics (prose/`learning` edits don't change it;
anything semantic does).

### `fisl build-baseline <scenario-dir>`

Constructs the scenario's `baseline.zip` from nothing, against a real
Factorio server. The layout is selected by the scenario id in
`scenario.yaml` (registered labs: `fp-03-littles-law`,
`fp-04-starvation-blocking`). What it actually does, in order:

1. creates a fresh deterministic map (fixed seed, no water/trees/enemies);
2. launches a temporary headless server with the FISL mods;
3. disarms Factorio's freeplay intro (otherwise the crash-site cutscene
   fires at the first human join — found the hard way);
4. builds the lab world via scripted commands (ports, machines, belts,
   inserters, power, spawn point, toolbox chest);
5. verifies exact entity counts in-game before saving anything;
6. saves the world and copies it to `<scenario-dir>/baseline.zip`;
7. **verification** (default on): runs the full scenario headlessly at 10×
   speed against the new baseline and requires a completed lifecycle,
   nonzero throughput, complete WIP coverage, clean census, and Lua/Python
   agreement. Fails loudly otherwise.

When to re-run it:

- the builder layout changed (`python/fisl/controller/baseline_builder.py`);
- mod *prototypes placed in the world* changed (ports, workpiece items);
- the guide/commit history says the committed baseline is stale.

Editing `scenario.yaml` alone usually does **not** require a rebuild — the
world and the experiment are deliberately separate.

After a successful rebuild, commit **both** the new `baseline.zip` and the
regenerated `verification-summary.json`, and put the baseline's sha256 (from
`fisl validate`) in the commit message.

### `fisl run <scenario-dir>`

The main event. Compiles the scenario, creates `runs/<run_id>/`, launches an
isolated Factorio server from a *copy* of the baseline, uploads the resolved
configuration, waits for READY, then:

- **interactive (default):** prints the port to connect your client to
  (section 5) and waits; the learner presses **Start Experiment** in-game.
- **`--headless`:** starts immediately with no client, runs at 10× wall
  speed (simulation semantics are unchanged), used for testing/verification.

The run ends when the last phase completes (panel shows results) or aborts
(e.g. the learner disconnects mid-run — that's by design, ADR 0018). Either
way, artifacts are collected into `runs/<run_id>/` and a `summary.json` is
computed. Retry = run the command again: new run id, same experiment
identity.

`--solution <id-or-path>` applies a **scripted reference solution** after
READY, before start: ordered `*.lua` steps from
`<scenario>/solutions/<id>/`, sent over RCON exactly like a learner's
pre-start build. Same scenario, same baseline — so `fisl compare` treats
learner and solution runs as the same experiment — and fully deterministic,
so solution runs double as regression fixtures and course answer keys. The
solution id + per-step script hashes are recorded in the run's provenance
and shown by `fisl compare`. Step files must be transmission-safe: full-line
comments only, and each step ends with `rcon.print("solution-step-ok")`.

### `fisl compare runs/<id-a> runs/<id-b> [...]`

Side-by-side debrief of any number of completed runs — the heart of the
"try a different strategy" loop. It checks comparability first (same
resolved scenario hash = same experiment; same reproducibility fingerprint
= same controlled condition), surfaces each run's validity problems and any
scripted-solution identity, and shows every shared metric with in-cell
deltas relative to run A. Deliberately **no combined score**: metrics stay
a vector (ADR 0012). Incompatible runs are still displayed, loudly flagged.
`--json <path>` also writes the full comparison as machine-readable JSON —
the intended data feed for course chapters and analysis — and
`--svg <path>` renders it as a crisp SVG figure for the book (regenerated
from run data, never a hand-taken terminal screenshot).

### `fisl solutions <scenario-dir> [--run]`

Without `--run`: lists the scenario's scripted reference solutions
(`solutions/<id>/` directories with their README summaries).

With `--run`: executes the whole set headlessly — a no-intervention
baseline first (disable with `--no-include-baseline`), then every solution
— and renders the N-way comparison at the end. One command from scenario to
systematic solution data; add `--json <path>` to persist the comparison and
`--svg <path>` to render it as a figure for the course text. Because
solution runs are deterministic, this doubles as the regression check for
the expected numbers cited in the course text.

### `fisl snap <scenario-dir>` (experimental)

Scripted screenshot session for the course text. Launches the scenario's
photo runs (baseline and, where the shot list needs it, a solution-applied
world); **you only connect a graphical client when prompted** — camera
position, zoom, Alt overlay, and GUI visibility are driven automatically
via the server, and the PNGs are rendered on *your* client into its
`script-output/fisl-snap/` directory (usually `~/.factorio/script-output/`
or `<install>/script-output/`). Copy them into `course/images/<lab>/` and
uncomment the chapter's figure blocks. Shot lists live in
`python/fisl/controller/snapshot.py`, keyed by scenario id, with camera
coordinates tied to the builder layout. Photo-session runs are aborted
after their shots — they are not data runs.

### `fisl report runs/<run_id>`

Human-readable results: every metric with its method, window, exact
numerator/denominator, and validity (coverage complete? census clean?).
The same information lives in `runs/<run_id>/summary.json` as JSON.

For scenarios that declare machine-state metrics (ADR 0007 — not fp03,
whose identity is frozen; new Lab 2/4 scenarios will), the report adds a
per-machine table. Membership is dynamic (ADR 0016): a machine you build
mid-run starts counting from the moment it's recognized, a machine you
remove stops counting then — each machine's row shows its eligibility
window, and pooled denominators sum only eligible machine-time. The table
shows what fraction of its eligible time each measured machine spent
**productive / starved / blocked / unavailable / disabled / idle_other /
unclassified**, plus `coverage_missing` when an interval couldn't be
classified. Requested `state_fraction` metrics appear in the main table as
pooled machine-time fractions of the *full window* — coverage gaps are
shown next to the number, never silently folded into it, and there is
deliberately no bare "utilization" metric: you always see which states are
in the numerator and what the denominator is.

---

## 4. What the learner experiences (Labs 3 & 4)

- Spawn next to a **toolbox chest** holding belts, inserters, chests,
  assemblers, poles — the materials for redesigning the line. (These items
  are not workpieces, so they never affect any measurement.)
- The line: blue **source port** → belts → three assemblers
  (rough → machined → inspected → finished workpieces) → orange **sink
  port**. The ports are FISL bench equipment: indestructible, non-minable,
  not openable.
- The FISL panel (top-left) shows READY → **Start Experiment** → during the
  run, only the scenario's `learner_live` metrics (fp03: current WIP) plus
  phase/time → at the end, the post-run results and the run id.
- fp03 timing: 2 min warmup + 10 min measured, real time.
- Rules baked into the current profile: no pausing (the experiment clock is
  simulation ticks; there is no supported pause), and disconnecting during a
  run **aborts it** (data preserved, run marked aborted).
- Carrying workpieces in your inventory doesn't break WIP accounting (they
  still count), but leftovers at the end of the run flag the run's validity.

**Lab 4 (fp04-starvation-blocking)** uses the same architecture,
compressed, with three *different* machine models so the constraint sits in
the middle of the line (blocked above, starved below). Timing: 4 min warmup
(the inter-stage buffer needs ~3–4 min to fill and reach steady state) +
8 min measured. Post-run the learner additionally sees pooled
productive/starved/blocked fractions, and the report's per-machine table
shows each machine's state distribution over its eligibility window —
machines the learner adds or removes mid-run enter/leave the measurement at
the right boundaries. Two committed reference solutions
(`a-buffer-before-constraint`, `b-upgrade-constraint`) make the buffer-vs-
constraint comparison reproducible: `fisl solutions
scenarios/factory-physics/fp04-starvation-blocking --run` runs baseline +
both and compares.

---

## 5. Connecting the graphical client

`fisl run` prints something like `Connect a Factorio client to
localhost:42025`. Then:

```sh
$FACTORIO_BASE/bin/x64/factorio \
    --mp-connect localhost:<port> \
    --window-size 1680x950 \
    --mod-directory runs/<run_id>/server/mods
```

- `--mod-directory` must point at **that run's** mods dir — the FISL mods
  aren't on the mod portal, so the client can't auto-download them.
- `--window-size WxH` starts windowed; Alt+Enter toggles fullscreen
  in-game and Factorio remembers your window afterwards.
- If Factorio complains another instance is running (server + client on one
  machine), give the client its own config/write directory.

---

## 6. Anatomy of `runs/<run_id>/`

| File | What it is |
|---|---|
| `manifest.json` | run identity, hashes, software versions, reproducibility fingerprint, status, artifact checksums |
| `scenario.resolved.json` | the exact compiled experiment the runtime executed (tick-level) |
| `run-config.json` | per-attempt data: run id, seed, run profile, baseline hash |
| `telemetry.jsonl` | the authoritative scientific record — every boundary transaction, census, event |
| `summary.json` | final metrics recomputed by Python from telemetry, cross-checked against the in-game accumulators |
| `server/` | the isolated server workspace (server.log lives here — first place to look when something breaks) |

Two runs are the *same controlled experiment* when their manifests share a
`reproducibility_fingerprint` (same scenario semantics, seed, baseline,
software). Run ids always differ.

---

## 7. Development workflow

```sh
python3 -m pytest tests/unit -q                # fast, no Factorio (always run)
FACTORIO_BIN=... python3 -m pytest tests/integration -v   # the real-runtime suite
```

- Integration tests exercise the empirical assumptions in
  `docs/RUNTIME_VALIDATION.md` and append evidence rows to
  `tests/integration/evidence/rv-evidence.jsonl`. Commit new evidence; RV
  status updates in the docs go through James.
- Contract rule: if the real runtime contradicts an accepted ADR, preserve
  the evidence and change the *technique* or propose a superseding ADR —
  never silently weaken semantics. (`docs/POST_REVIEW_REVISIONS.md` has the
  source-of-truth order.)
- Update **this guide** in the same commit as any workflow/CLI change.

---

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Scenario invalid` with a list of problems | `scenario.yaml` error; each line names the exact path and rule violated |
| `baseline save missing` | scenario has no `baseline.zip` yet — run `fisl build-baseline` |
| Crash-site cutscene / ship wreckage on joining | baseline built before 2026-08-26 is "armed" with the freeplay intro — rebuild it |
| `RCON not reachable` / server exits early | read `runs/<run_id>/server/server.log`; usual causes: wrong `FACTORIO_BIN`, port conflict, mod load error |
| Client can't join: mod mismatch | client launched without `--mod-directory runs/<run_id>/server/mods` |
| Run aborted `learner_disconnected` | client closed/crashed mid-run — intended behavior; just run again |
| Metric reported `incomplete` / objective undetermined | the run didn't cover the metric's window (aborted early) or census flagged a discrepancy — `fisl report` shows which |
| `wip_census_discrepancy` events | tracked workpieces appeared/vanished without crossing a port (conservation violation) — the report shows the suspect interval; the ledger is never silently corrected |
| Scripted solution "applied" but metrics identical to baseline | the intervention silently did nothing — most likely a circuit wire past its 9-tile reach: `connect_to()` returns false without raising, and an unconnected inserter ignores its enable condition. Check every `connect_to` return value in the solution script (see fp03 solution A v2 → v3) |

Known runtime findings (why some code looks odd) are catalogued in
`docs/RUNTIME_VALIDATION.md` § "Spike findings".
