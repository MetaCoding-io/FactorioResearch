# ADR 0014: Reset, Repeat, and Replay Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

FISL scenarios are intended to be repeated experiments. A learner should be able to modify a factory, observe results, reset, try a different design, and compare runs. Regression tests should be able to load the same world repeatedly under the same controlled condition.

The word "reset" can hide several very different operations:

- undoing every learner action in-place;
- restoring entities from a script-maintained snapshot;
- reloading a pristine baseline save;
- restarting only FISL counters while leaving the world modified.

Only one of these gives a simple, trustworthy v1 scientific contract.

Likewise, "replay" can mean either:

- repeating the same controlled environment from the same starting state;
- reproducing the exact same player actions;
- using Factorio's own replay facilities;
- re-running a deterministic automated fixture.

FISL must distinguish these concepts explicitly.

## Decision

### 1. Canonical v1 reset means reload the immutable baseline save

A FISL reset does **not** attempt to undo learner changes entity-by-entity.

Canonical reset is:

```text
end/discard current attempt
        |
        v
load pristine baseline save bytes
        |
        v
initialize a fresh FISL run from resolved scenario
```

This is the authoritative mechanism for returning the physical simulation to baseline.

### 2. The baseline save is immutable during ordinary runs

The baseline artifact identified by ADR 0013 is read-only input from the experiment's perspective.

A run MUST NOT overwrite the canonical baseline.

If a final/modified save is deliberately promoted to become a new baseline, that is an authoring/versioning action producing a new baseline artifact/hash and normally a scenario version change.

### 3. Reset creates a new run ID

Every attempt after reset is a new run under ADR 0013.

Even when the baseline, resolved experiment, software environment, and seed are identical:

```text
run A != run B
```

but they may share the same reproducibility fingerprint.

This permits clean comparative history rather than overwriting prior attempts.

### 4. FISL distinguishes `reset`, `repeat`, and `replay`

V1 terminology:

- **reset** — return to the pristine baseline and prepare a new run;
- **repeat** — execute another run under the same controlled experimental condition, with new player actions allowed;
- **replay** — attempt to reproduce an execution including its time-varying external/input actions closely enough to claim execution equivalence.

A normal classroom retry is a reset + repeat, not necessarily a replay.

### 5. Same controlled condition does not imply same human behavior

The reproducibility fingerprint fixes controlled experiment inputs such as baseline, scenario, software, and FISL seed.

It does not capture a human learner's mouse/keyboard/build decisions.

Therefore FISL MUST NOT promise that two human-played runs sharing a fingerprint will have identical world histories or outputs.

They are comparable runs under the same controlled condition.

### 6. FISL-controlled schedules are reproducible from seed/configuration

For any FISL-controlled process—deterministic or future stochastic—the same resolved scenario and experiment seed MUST generate the same FISL-controlled schedule/action sequence, provided the same relevant causal preconditions apply.

Future stochastic features use the dedicated FISL RNG described in prior ADRs.

Where a policy depends on observed world state, identical RNG draws do not by themselves guarantee identical actions if player behavior changes the state; that dependency is part of the policy semantics.

### 7. Automated deterministic fixtures can make stronger repeatability claims

For tests with no uncontrolled human input and a pinned Factorio/mod/runtime environment, FISL SHOULD support deterministic repeated execution from the same baseline/configuration.

Such tests may use tick-controlled execution and assert exact FISL observations/results at known ticks.

Current Factorio command-line/runtime facilities include running a save to a specified tick and controlled tick advancement patterns useful for regression testing; implementation specifics are left to the test harness.

### 8. Mid-run save/load is not part of the canonical v1 measured-run protocol

A canonical v1 scientific measured run SHOULD execute continuously from experiment start through completion without a mid-run save/load cycle.

If a save/load occurs during an active measured experiment, FISL records it as a protocol/continuity condition and the run is not considered canonical for strict comparison unless the scenario explicitly permits it.

This avoids having to make strong v1 claims about every mod/runtime reload edge case or human wall-time break.

### 9. Save/load does not create simulation time

If a future scenario explicitly permits mid-run save/load, elapsed wall time during the break does not advance FISL experiment time.

The next executed simulation tick continues from the persisted simulation tick state.

This preserves ADR 0001.

### 10. Persistent FISL state must survive ordinary Factorio save/load safely

Although canonical measured runs avoid mid-run reload, FISL implementation still needs correct save compatibility.

Persistent state follows the architecture rule:

> FISL persistent state should be boring data.

Store IDs, counters, strings, booleans, tables, seeds, phase state, and entity identifiers suitable for reconstruction. Do not depend on persisted closures or fragile runtime object graphs.

Transient indexes/references are reconstructed according to Factorio's supported mod data lifecycle.

### 11. Run initialization validates that the baseline is suitable

Before entering `READY`, the controller/runtime validates at least:

- expected baseline/save identity;
- FISL core mod compatibility;
- required port/entity bindings;
- declared zone/surface existence;
- required prototypes/items/recipes;
- absence of an already-active stale FISL run state;
- scenario/compiler/runtime compatibility.

Failure to validate prevents the experiment from entering `RUNNING` rather than producing a misleading run.

### 12. FISL run state is newly initialized for every attempt

A new run receives fresh:

```text
run_id
experiment seed/RNG state
phase/lifecycle counters
port ledgers
demand cohorts
metric accumulators
objective state
telemetry sequence state
protocol/coverage state
```

The physical baseline may contain static FISL apparatus and authoring tags, but it MUST NOT carry forward prior run results as active experimental state.

### 13. Final saves are outputs and never become reset sources implicitly

A completed/aborted run may capture a final save for debrief.

Reset never chooses "most recent save" or a final save automatically.

It always returns to the explicitly declared baseline artifact for that scenario unless the instructor changes the scenario/baseline configuration.

This prevents accidental drift between learners/attempts.

### 14. Abort preserves the run dataset

An aborted run remains a run with a unique ID and provenance.

FISL should flush/preserve as much authoritative telemetry and summary/abort metadata as possible.

Abort does not trigger silent deletion or reuse of the run ID.

A subsequent retry is a new run.

### 15. Reset is controller-orchestrated rather than a giant Lua world-reconstruction feature

The external Python controller owns the high-level reset/relaunch workflow.

The Lua runtime owns simulation-synchronous state but SHOULD NOT implement a general-purpose undo engine for arbitrary Factorio player actions.

This follows the architecture responsibility boundary:

- Lua: what is happening in Factorio now;
- Python: what experiment/run is being orchestrated;
- baseline save: what world should a reset restore.

### 16. V1 does not require recording/replaying every player input

Exact human-input replay is deferred.

Possible future approaches include Factorio replay support, command/action recording, constrained interfaces, or server-side experimental protocols.

V1's reproducibility promise is therefore:

> The controlled starting condition and FISL-controlled environment can be reproduced; arbitrary human choices are observations/causes of run divergence, not hidden deterministic inputs.

### 17. Comparisons should default to runs from compatible reproducibility conditions

The debrief/comparison layer SHOULD warn when learners attempt to compare runs whose baseline/resolved experiment/software/seed conditions differ in a way that invalidates the intended comparison.

Some scenarios intentionally compare different demand schedules or experimental variants; those comparisons should be declared as compatible variants rather than silently treating every run as equivalent.

### 18. A deterministic replay/test may validate result equivalence, not byte-identical artifacts

Even when a fixture is deterministic, operational metadata such as:

```text
run_id
wall-clock timestamps
file paths
```

will differ.

Regression tests should compare the scientific outputs/observation stream after excluding declared non-semantic run metadata rather than requiring identical run-directory bytes.

### 19. Reset/repeat behavior is exposed through the CLI

The intended user workflow is conceptually:

```text
fisl run fp-05-pull-production
fisl reset/retry <run-or-scenario>
fisl compare <run-a> <run-b>
```

The exact command names are implementation details, but the controller must make fresh-baseline retry easy enough to support iterative learning.

## Consequences

### Positive

- Reset has a simple, auditable meaning: reload known baseline bytes.
- Arbitrary Factorio building/destruction does not require an impossible undo engine.
- Every attempt remains preserved for comparison.
- Controlled experimental conditions are reproducible without pretending human actions are deterministic.
- Automated fixtures can make stronger exact-repeatability claims than human labs.
- Mid-run save/load complexity is excluded from canonical v1 experiments while remaining forward-compatible.
- Final saves cannot accidentally drift into baseline status.

### Negative / trade-offs

- Reset generally requires reloading/restarting the Factorio world rather than an instantaneous in-place undo.
- Exact human-action replay is not a v1 feature.
- Mid-run save/resume is discouraged for strict measured runs.
- Baseline authoring/version management becomes important because the baseline is the authoritative reset source.

## Acceptance criteria

The reset/replay portion of Issue #1 is complete when:

1. canonical reset reloads the immutable baseline rather than undoing world mutations;
2. every reset/retry creates a new run ID;
3. reset, repeat, and replay have distinct meanings;
4. same experiment fingerprint does not imply identical human actions;
5. FISL-controlled seeded schedules are reproducible under the same controlled causal conditions;
6. automated no-human fixtures can make stronger deterministic assertions;
7. canonical v1 measured runs avoid mid-run save/load by default;
8. save/load wall time never becomes experiment simulation time;
9. persistent Lua state follows safe, reconstructable boring-data rules;
10. run initialization validates baseline/bindings before `RUNNING`;
11. each attempt initializes fresh run ledgers/counters/RNG/objective state;
12. final saves remain outputs and are never implicit reset baselines;
13. aborted runs preserve data/provenance;
14. the Python controller orchestrates reset instead of Lua implementing arbitrary undo;
15. exact human-input replay is explicitly deferred rather than implied.

## References

- Factorio command-line parameters include loading a specified single-player game (`--load-game`) and deterministic test/benchmark-related controls.
- Factorio runtime data lifecycle documentation defines supported save/load behavior for mod state and reconstruction hooks.
