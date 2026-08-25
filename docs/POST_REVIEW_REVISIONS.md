# FISL v1 Post-Design-Review Revisions

**Status:** Implementation handoff addendum  
**Date:** 2026-08-25  
**Motivation:** Independent critique in [`DESIGN_REVIEW.md`](DESIGN_REVIEW.md) and subsequent review/rebuttal cycle.

## Purpose

The original v1 ADR/PRD pass established the scientific contract before any code existed. The independent review correctly identified several places where:

- design semantics were being confused with unvalidated Factorio implementation hypotheses;
- the initial physical-census implementation made conserved-flow WIP harder than necessary;
- schema identity mixed stable experiment semantics with per-run fields;
- local multiplayer pause/disconnect behavior needed an explicit POC profile;
- the document called a near-full-v1 checklist a “POC.”

The core scientific architecture remains intact. This document tells an implementation agent exactly what changed after review and what older statements are superseded.

## Current source-of-truth order

When documents conflict, use this order:

1. later Accepted/superseding ADR;
2. [`FISL_V1_SCHEMA.md`](FISL_V1_SCHEMA.md);
3. [`RUNTIME_VALIDATION.md`](RUNTIME_VALIDATION.md) for empirical status/required spikes;
4. GitHub Issue #2 for **immediate POC scope**;
5. [`FISL_V1_PRD.md`](FISL_V1_PRD.md) for full-v1 product requirements;
6. older illustrative examples/summary prose.

Do not interpret the narrower Issue #2 as deleting full-v1 requirements. It only sequences them after the vertical slice.

## Revision 1 — Accepted design vs runtime validation

`Accepted` means FISL has chosen the semantic/architectural behavior.

It does not mean every Factorio-specific implementation hypothesis has already been observed on Factorio 2.0.77.

[`RUNTIME_VALIDATION.md`](RUNTIME_VALIDATION.md) now contains the empirical gate. The first coding work should prove or falsify those assumptions against the real runtime.

A failure may require:

- a different implementation technique; or
- a new/superseding ADR when the semantic itself is infeasible.

It must never produce a silent semantic downgrade.

## Revision 2 — conserved-flow total WIP is ledger-authoritative

ADR 0017 supersedes the old implementation assumption that whole-flow total WIP is obtained by scanning every physical holder every tick.

For validated conserved work-unit flows:

```text
WIP(T)
  = initial WIP
  + cumulative admissions
  - cumulative completions
  - cumulative declared losses
```

Boundary transactions therefore produce exact tick-resolution total WIP.

Physical census is still required, but its primary roles are now:

```text
independent ledger validation
physical decomposition / “where is the WIP?”
measurement-adapter testing
```

The initial canonical cross-check cadence is 60 simulation ticks.

A complete census mismatch:

- does not overwrite the ledger;
- emits `wip_census_discrepancy`;
- conservatively flags the WIP-validity interval since the prior successful cross-check when exact failure onset is unknown.

### Consequence for player inventory

Already-admitted tracked work placed in player inventory remains WIP because it has not crossed a declared exit.

Transient carriage during redesign is diagnostic rather than automatic WIP disappearance/coverage failure.

Residual tracked player-held work at the final boundary escalates to an explicit experiment-validity condition.

### Consequence for belts/active craft

Belt deduplication and active-craft occupancy adapters remain important for physical census/decomposition and runtime tests, but they no longer sit on the every-tick authoritative total-WIP path.

## Revision 3 — hardened ports are load-bearing

Because conserved-ledger WIP depends on admission/completion transactions, canonical source/sink apparatus must enforce the one-way accounting protocol strongly rather than relying only on convention.

See ADR 0017 and RV-002/RV-003.

## Revision 4 — stable `ResolvedScenario` vs per-attempt `RunConfiguration`

The original schema blurred these concepts.

The corrected model is:

```text
AuthorScenario YAML
      ↓ compile
ResolvedScenario
      ↓ canonical hash
resolved_scenario_hash

resolved_scenario_hash + run_id + actual seed + run profile
      ↓
RunConfiguration
```

`run_id` and the actual execution seed are excluded from `resolved_scenario_hash`.

The reproducibility fingerprint includes:

```text
resolved_scenario_hash
actual seed
baseline hash
Factorio/FISL/mod identity
behavior-affecting run profile
```

and deliberately excludes `run_id`.

Every run stores both:

```text
scenario.resolved.json
run-config.json
```

## Revision 5 — service-tail validation uses the direct deadline property

No arbitrary rule such as:

```text
service_tail > max_wait
```

is required.

The compiler validates the actual property:

```text
observation_horizon_end >= latest_selected_cohort_deadline
```

Under the accepted half-open timing model, a tail exactly equal to `max_wait` can be sufficient.

## Revision 6 — deterministic local-server pause/disconnect profile

ADR 0018 defines the first interactive POC behavior:

```text
pause_policy: prohibited
server incidental/zero-player auto-pause: disabled
unexpected required learner disconnect while RUNNING: abort + preserve data
headless fixture: no learner connection required
```

General controlled pause/rejoin/resume is deferred.

## Revision 7 — immediate POC is intentionally much smaller than full v1

The old `FISL_V1_PRD.md` POC checklist described too much of the product at once.

GitHub Issue #2 is now authoritative for immediate implementation scope.

The first goal is:

```text
runtime/API validation spike
        +
one real Lab 3 / Little's Law vertical slice
```

It must prove:

- YAML validation/compilation;
- stable `ResolvedScenario` + separate `RunConfiguration`;
- real Factorio 2.0.77 server/client/RCON path;
- clean FISL tick start;
- hardened source/sink settlement;
- one conserved workpiece visibly traversing normal Factorio mechanics;
- exact conservation-ledger WIP;
- periodic physical census agreement + deliberate discrepancy handling;
- average WIP;
- throughput;
- Little's-Law-derived cycle time;
- provenance/reporting;
- baseline retry.

Only after the vertical slice works and Lab 3 has been exercised with a human should Codex expand implementation toward:

- machine-state-rich Lab 4 work;
- demand/service cohorts for Lab 5;
- visibility/objective machinery;
- upstream storage variants/capstone behavior;
- polished remaining labs.

These are deferred, not rejected.

## Revision 8 — Lua/Python metric responsibility

Do not build two complete independent metric engines.

Use the responsibility split:

```text
Lua
  authoritative simulation-time state
  authoritative primitive/boundary facts
  exact streaming accumulators needed during the live run
  minimal live values required by in-game UI/protocol

Python
  authoritative post-run derived reporting/analysis where retained data permit recomputation
  report formatting
  cross-run comparison later
  verification of exact Lua accumulators when useful
```

The contract still requires reproducibility of scientific results from retained authoritative data; it does not require every post-run statistic to have a second production Lua implementation.

## Revision 9 — telemetry may be losslessly compressed/batched

Authoritative telemetry does not mean one verbose JSON object for every unchanged entity every tick.

Prefer semantically lossless strategies such as:

```text
exact counters/accumulators
state-change records
run-length intervals
batched records
coarse census snapshots where the method itself is coarse
```

Keep exact tick/quantity semantics and enough provenance for Python to reproduce final results.

RV-009 must size/profile the chosen strategy before broader implementation.

## Revision 10 — RCON configuration remains current choice; companion mod is an explicit fallback

ADR 0015 remains in force for the POC: canonical resolved configuration is transferred through a narrow RCON protocol.

The generated companion-config-mod alternative has been considered and is recorded as RV-010 fallback.

Do not re-litigate it abstractly. First run RV-008. Switch only if real RCON configuration transfer proves materially more fragile/complex than the alternative.

## What did NOT change

Keep these foundational decisions:

- Factorio models the production system; FISL models the experiment.
- scenario before theory;
- Lua-authoritative simulation time;
- half-open tick intervals;
- explicit zone/system/port/flow separation;
- scalar WIP requires a defensible conserved work-unit basis;
- throughput comes from declared completion boundaries;
- no bare `utilization` or bare `service_level`;
- missing data is never silently zero;
- cycle-time method provenance remains explicit;
- reset means reload immutable baseline, not world undo;
- run provenance is mandatory;
- v1 remains deterministic.

## Codex instruction

Start with GitHub Issue #2, not the old broad PRD POC list.

Use the full PRD as the destination architecture/product scope, but earn the right to build the later layers by first proving the smallest end-to-end scientific laboratory against the actual Factorio runtime.
