# ADR 0001: Experiment Time and Phase Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

FISL needs a temporal model that is scientifically unambiguous, reproducible, compatible with Factorio's simulation model, and extensible to later variability/control experiments.

Factorio exposes several notions that can be confused with one another:

- the current map tick (`game.tick`);
- `ticks_played`;
- wall-clock time;
- game speed (`game.speed`);
- paused/unpaused state.

These are not interchangeable. In particular, `ticks_played` continues advancing while entity updates are tick-paused, so it is unsuitable as an experiment clock.

The temporal contract must also define what a phase means, how phase boundaries behave, whether warm-up has special semantics, and how human-friendly durations map to the simulation.

## Decision

### 1. Simulation ticks are the authoritative time base

The canonical unit of FISL experiment time is the **executed Factorio map tick**.

FISL distinguishes at least four temporal coordinates:

1. `map_tick` — the absolute Factorio `game.tick` value.
2. `experiment_tick` — zero-based elapsed simulation ticks since the experiment began.
3. `phase_tick` — zero-based elapsed simulation ticks since the current phase began.
4. `wall_time` — optional external timestamp/elapsed real time used only for provenance and operational diagnostics.

Only the first three may define experiment behavior or simulation-time measurements. Wall time MUST NOT determine source schedules, demand schedules, phase transitions, metrics, or objectives.

A run beginning at map tick `S` records an `experiment_start_map_tick`. For ticks during the run:

```text
experiment_tick = map_tick - experiment_start_map_tick
phase_tick      = experiment_tick - phase_start_experiment_tick
```

The implementation MAY maintain explicit counters rather than recomputing subtraction, but the semantics must be equivalent.

### 2. `ticks_played` is not experiment time

FISL MUST NOT use Factorio `ticks_played` for experiment time, phase time, measurement windows, or schedule progression.

It may be recorded as provenance if useful, but it has no scientific meaning inside the FISL contract.

### 3. A simulation second is exactly 60 ticks

Author-facing scenario files may express durations using human-friendly simulation units such as:

```yaml
duration: 5m
```

These are authoring conveniences only. The compiled/resolved scenario MUST contain integer tick durations.

Definitions:

```text
1 simulation second = 60 ticks
1 simulation minute = 3,600 ticks
```

Conversion MUST be deterministic. A duration that cannot be represented as an integral number of ticks MUST either be rejected by validation or require an explicit rounding policy; silent floating-point rounding is forbidden.

The recommended v1 behavior is to reject non-integral tick durations.

### 4. Game speed changes wall-clock execution rate, not experiment time

`game.speed` affects how quickly Factorio attempts to execute simulation ticks in real time. It does not change the meaning of a FISL tick.

Therefore a 600-tick phase is the same simulation interval whether the game executes it slowly because of poor UPS, at normal speed, or at an intentionally accelerated game speed.

However, game speed can affect a human learner's available real-world reaction/thinking time. FISL therefore treats game-speed policy as part of the **experimental protocol**, even though it is not part of simulation-time mathematics.

V1 scenarios SHOULD default to a fixed game speed of `1.0` for human experiments.

A run MUST record:

- configured speed policy;
- configured speed value when fixed;
- any detected speed-policy violations.

A future headless/testing run may intentionally use a different fixed speed without changing simulation-time metric semantics.

### 5. Pausing stops simulation time

When Factorio's map tick is paused, FISL experiment time does not advance.

A pause therefore does not add simulation time to a phase and does not change the duration denominator of simulation-time metrics.

Pausing can nevertheless change a human experiment by giving the learner additional thinking time. Pause handling is therefore also an experimental-protocol concern.

V1 supports an explicit pause policy, initially:

```text
allowed
prohibited
```

All pause/unpause activity that FISL can observe MUST be recorded as protocol events. If a scenario declares pauses prohibited, a detected pause is a protocol violation and the run may be flagged invalid for comparison while still preserving its data.

FISL SHOULD avoid destroying data merely because a protocol violation occurred.

### 6. Run lifecycle and experiment phases are separate concepts

A FISL run has a lifecycle outside the experiment timeline. Recommended states are:

```text
INITIALIZING
    -> READY
    -> RUNNING
    -> COMPLETED

with ABORTED and INVALID/PROTOCOL_VIOLATION as possible outcomes/flags.
```

`READY` time is not experiment time.

During `READY`, FISL validates the scenario/world bindings and may hold the simulation paused. An explicit start request transitions the run into `RUNNING` on a clean simulation-tick boundary.

A run can complete successfully while also carrying protocol-violation flags. `INVALID` should therefore preferably be represented as validity metadata rather than as a destructive lifecycle terminal that discards results.

### 7. Experiment phases are ordered, contiguous tick intervals

A v1 experiment contains one or more named phases.

Example:

```yaml
experiment:
  phases:
    - id: warmup
      duration: 5m
    - id: measured
      duration: 20m
```

Phase IDs are labels. Names such as `warmup`, `baseline`, `measured`, or `intervention` have **no built-in runtime semantics**.

V1 phase rules:

- phase IDs MUST be unique within an experiment;
- each phase MUST have a positive fixed duration;
- phases execute in declared order;
- phases are contiguous;
- phases do not overlap;
- phases do not contain gaps;
- the first phase starts at `experiment_tick = 0`;
- total experiment duration is the sum of all phase durations.

V1 intentionally supports fixed-duration phase endings only. The schema SHOULD leave room for future end conditions such as manual transitions or predicates, but those are not required for v1.

### 8. Phase intervals are half-open

A phase occupying ticks from `A` through `B` is represented as:

```text
[A, B)
```

The phase includes `A` and excludes `B`.

If phase `warmup` has duration 18,000 ticks:

```text
warmup:  experiment ticks [0, 18000)
measured: begins at experiment tick 18000
```

Thus:

- the last tick belonging to `warmup` is `17999`;
- the first tick belonging to `measured` is `18000`;
- a transition consumes zero experiment ticks;
- no event or observation belongs to two phases because of a boundary convention.

This half-open convention MUST also be used later for observation windows unless a metric contract explicitly defines otherwise.

### 9. Start and transition boundaries must be clean tick boundaries

An experiment start request received during a Factorio tick MUST NOT create a partially observed experiment tick.

The recommended implementation is:

1. receive/record the start request;
2. establish a pending start;
3. begin the experiment at the next eligible simulation-tick boundary;
4. record that map tick as `experiment_start_map_tick`;
5. assign that tick `experiment_tick = 0`.

Similarly, phase changes occur only at exact experiment-tick boundaries derived from accumulated phase durations.

All FISL subsystems MUST agree on the active phase for a given `experiment_tick`.

### 10. Warm-up is not a special clock mode

FISL v1 does not define a magical `warmup_seconds` field whose data are automatically discarded.

A warm-up period is an ordinary phase, for example:

```yaml
- id: warmup
  duration: 5m
```

Metrics explicitly choose observation windows. A metric that should ignore warm-up references only the later measured phase/window. A metric that needs warm-up data may include it.

This keeps time semantics simple and prevents hidden measurement policy from being encoded in the experiment clock.

### 11. Metrics and objectives must reference explicit temporal windows

The time model establishes named phases as stable selectors for later measurement definitions.

The exact metric-window schema will be finalized under the aggregation/observation-window portion of Issue #1, but the time contract requires that:

- every scored/derived metric has an explicit observation interval;
- no metric silently assumes that `RUNNING` means `measured`;
- phase names may be used to identify windows;
- future sub-phase offsets may refine windows without changing the experiment clock.

Illustrative only:

```yaml
metrics:
  - id: output_throughput
    type: throughput
    window:
      phase: measured
```

### 12. Completion occurs at the boundary after the final phase

When the final phase reaches its exclusive end tick, the experiment is complete.

FISL SHOULD prevent unmeasured post-experiment simulation drift from contaminating the final state. The recommended v1 completion behavior is to pause the simulation immediately at the completion boundary after final observations required by the measurement contract have been captured.

The precise ordering of final observation capture versus pause will be defined with primitive-observation semantics.

### 13. Factorio event ordering must not become an accidental scientific dependency

Factorio events are timestamped with map ticks, but the global ordering among unrelated events within a tick is not generally a stable scientific contract that FISL should rely upon.

Therefore:

- FISL records the map tick on primitive events;
- all FISL-owned per-tick operations use one documented internal ordering;
- metrics that need to combine multiple same-tick events must define deterministic reduction semantics;
- the scientific contract MUST NOT assume undocumented ordering among unrelated Factorio events.

This is particularly important at phase boundaries.

### 14. Save/load does not create experiment time

If an active run is saved and later loaded, no simulation time passes merely because wall-clock time passed outside Factorio.

Any support or prohibition for mid-run save/load is a later reset/replay protocol decision, but the temporal rule is fixed: only executed map ticks advance experiment time.

### 15. Multiplayer shares one authoritative experiment clock

In multiplayer, the server simulation tick is authoritative. All players participate in the same experiment/phase clock.

Future organizational experiments may give roles different information, but they do not receive different physical simulation clocks.

## Proposed v1 schema shape

Illustrative shape:

```yaml
spec: fisl/v1

experiment:
  time:
    game_speed:
      policy: fixed
      value: 1.0
    pause_policy: allowed

  phases:
    - id: warmup
      duration: 5m

    - id: measured
      duration: 20m
```

The resolved/compiled representation should contain exact integer ticks, for example:

```yaml
experiment:
  time:
    game_speed:
      policy: fixed
      value: 1.0
    pause_policy: allowed

  phases:
    - id: warmup
      duration_ticks: 18000
      start_tick: 0
      end_tick: 18000

    - id: measured
      duration_ticks: 72000
      start_tick: 18000
      end_tick: 90000
```

The author-facing and resolved forms SHOULD be treated as distinct representations. Provenance should retain the resolved form or a hash of it.

## Consequences

### Positive

- Experiment semantics are independent of rendering, UI latency, controller latency, UPS, and wall-clock execution speed.
- Pauses cannot silently inflate or shrink simulation-time metrics.
- The same clock works for deterministic Factory Physics labs and later stochastic experiments.
- Warm-up behavior remains explicit in metric definitions.
- Phases provide a general extension point for later disturbances, economics, information policies, or control-policy changes.
- Headless regression tests can execute scenarios faster without changing simulation semantics.
- A future test harness can potentially exploit Factorio's paused-tick stepping support to advance an exact number of ticks.

### Negative / trade-offs

- Scenario compilation is required to convert friendly durations into exact ticks.
- Human reaction-time experiments require additional wall-time/protocol semantics; simulation ticks alone are insufficient.
- Same-tick event reduction must be designed carefully instead of relying on accidental Factorio event order.
- Fixed-duration-only phases constrain some future interactive scenarios, intentionally, in exchange for a simpler reproducible v1.

## Open items deferred to later Issue #1 sections

This ADR deliberately does not settle:

- exact observation sampling point within a tick;
- WIP integration/sampling frequency;
- same-tick port transaction ordering;
- exact final-observation ordering at completion;
- metric window syntax beyond phase selection;
- reset/replay validity policy;
- whether a mid-run load is merely logged or invalidates a classroom comparison;
- how wall-clock learner-response metrics would be defined if ever needed.

Those require the primitive-observation, aggregation, port, and reset/replay contracts.

## Acceptance criteria for this decision

The time/phase portion of Issue #1 is complete when we agree that:

1. relative Factorio map ticks are the authoritative experiment clock;
2. simulation seconds are exact 60-tick authoring units;
3. wall time and game speed do not define simulation-time measurements;
4. pause behavior is protocol-controlled and does not advance experiment time;
5. phases are ordered, contiguous, fixed-duration half-open tick intervals in v1;
6. warm-up is represented by an ordinary phase, not hidden clock semantics;
7. metric windows explicitly choose the phases/time intervals they measure;
8. start/end/phase transitions occur only on clean tick boundaries;
9. same-tick event ordering is never left implicit.
