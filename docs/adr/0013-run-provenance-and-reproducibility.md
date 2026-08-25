# ADR 0013: Run Provenance and Reproducibility Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

FISL exists to turn Factorio scenarios into reproducible experiments. A metric result is not scientifically useful if the system cannot establish which world, experiment definition, software stack, measurement methods, and seed produced it.

Several different concepts are easy to conflate:

- the human-readable scenario version;
- the exact authoring files used;
- the resolved/compiled experiment semantics;
- the baseline Factorio save;
- the software/mod environment;
- a unique execution attempt;
- whether two runs are intended to be reproducible under the same experimental condition.

FISL needs a provenance model that distinguishes those concepts and produces a self-contained run dataset suitable for audit, debrief, regression testing, and later research use.

## Decision

### 1. Every execution attempt has a globally unique `run_id`

Each FISL run receives a new opaque unique identifier before execution.

A ULID, UUIDv7, or equivalent sortable/random unique identifier is acceptable; the final implementation choice is not scientific semantics.

A retry of the same scenario with the same seed still receives a different `run_id`.

The run ID identifies an attempt, not an experimental condition.

### 2. Scenario ID/version is human coordination metadata, not sufficient provenance

A scenario declares at least:

```text
scenario.id
scenario.version
```

V1 scenario versions SHOULD use SemVer-compatible strings.

However, FISL MUST NOT rely on `scenario.version` alone to prove that two runs used identical experiment semantics. Authors can make mistakes, working-tree changes can occur, and version numbers do not identify baseline-save bytes.

Hashes/fingerprints provide the authoritative machine-checkable identity.

### 3. FISL preserves both source/package identity and resolved experiment identity

Two different hashes are useful:

1. **scenario package/source hash** — identifies the supplied scenario package/artifacts as executed;
2. **resolved experiment hash** — identifies the canonical compiled semantics used by the runtime.

The resolved experiment representation contains explicit ticks, resolved port policies, metric windows, objective rules, visibility, bindings/configuration, and other experiment-relevant semantics rather than authoring shorthand.

This allows FISL to distinguish:

- a prose-only/source packaging change;
- a semantically meaningful experiment change.

The canonicalization rules must be versioned with the schema/compiler.

### 4. The resolved experiment is stored as a run artifact

Every run dataset MUST contain the exact resolved scenario/experiment representation used for that execution, or a lossless canonical equivalent.

A hash without the corresponding resolved configuration is insufficient for audit.

Conceptually:

```text
scenario.source.yaml
       |
       v
Python validation/compiler
       |
       v
scenario.resolved.json  <-- stored with run
       |
       v
Factorio runtime
```

The resolved document is the authoritative contract handed to execution, subject to the final controller/runtime transport design.

### 5. Baseline save bytes are identified by a cryptographic hash

The baseline Factorio save is an input artifact and MUST have a recorded cryptographic digest, using SHA-256 or a comparably standard digest.

Run provenance records at least:

```text
baseline_save_name/path logical reference
baseline_save_sha256
```

Two saves with the same filename but different contents are different baseline inputs.

The baseline is treated as immutable for an experiment version.

### 6. Software/runtime provenance is mandatory

The run manifest records enough software information to reproduce the runtime environment, including at least:

```text
Factorio version
FISL core mod version/build identity
FISL Python/controller version/build identity
scenario schema/compiler version
installed mod names and versions
relevant mod/settings identity
classifier/adapter versions where separately versioned
```

Where practical, local development builds SHOULD also record a Git commit SHA and dirty-working-tree indicator for FISL components.

The scientific contract should not depend on only a package display version when exact source identity is available.

### 7. Mod/environment identity participates in reproducibility

A Factorio save can behave differently with a different mod set or settings.

The reproducibility input therefore includes the effective mod manifest and relevant startup/runtime configuration required by the scenario.

At minimum, the manifest records mod name/version. The implementation SHOULD record hashes for FISL-owned mod artifacts/builds and enough configuration to detect meaningful changes.

### 8. Every run records an explicit experiment seed

Even deterministic v1 experiments record an `experiment_seed`.

All FISL-controlled pseudo-random behavior, now or in future Course II features, MUST derive from the dedicated FISL experiment RNG/seed policy rather than ad-hoc randomness.

For v1 deterministic schedules the seed may not affect behavior, but including it from the beginning makes the run contract stable.

### 9. A reproducibility fingerprint identifies the experimental input condition

FISL computes a canonical fingerprint from the inputs that can affect experiment behavior/measurement, including at least:

```text
resolved experiment hash
baseline save hash
Factorio version/build identity as available
FISL runtime/controller identity
mod/configuration identity
experiment seed
```

The exact serialization/hash composition is versioned.

Runs with different `run_id`s may share the same reproducibility fingerprint.

This fingerprint does **not** imply identical human player actions; it means the controlled experimental starting condition/configuration is the same.

### 10. Learner/team identifiers do not define experiment identity

A scenario/run may optionally record a learner/team identifier for classroom organization.

That identifier:

- belongs to run metadata;
- does not enter the reproducibility fingerprint unless a future scenario explicitly uses identity as an experimental input;
- should avoid unnecessary personal data.

FISL does not require real names for scientific operation.

### 11. Wall-clock timestamps are provenance, never simulation timing

The manifest may record:

```text
created_at/start_wall_time/end_wall_time
```

for operational traceability.

These timestamps do not define experiment phase duration, rates, service deadlines, or other simulation-time measurements. ADR 0001 remains authoritative.

### 12. Simulation timing and lifecycle are recorded explicitly

A completed run manifest/summary records as applicable:

```text
experiment_start_map_tick
experiment_end_map_tick
experiment_duration_ticks
phase resolved tick ranges
completion/abort reason
pause/protocol events summary
```

This permits verification that the execution matched the resolved time contract.

### 13. Result artifacts are versioned and checksummed

The run dataset should be organized around stable machine-readable artifacts such as:

```text
runs/<run_id>/
  manifest.json
  scenario.resolved.json
  telemetry.jsonl
  events.jsonl
  summary.json
  final-save.zip        # optional/recommended when captured
```

Additional files may include logs, screenshots, or instructor reports.

The manifest/summary SHOULD contain checksums or an artifact inventory sufficient to detect missing/modified authoritative artifacts.

Telemetry/result schema versions are explicit.

### 14. `telemetry.jsonl` is the authoritative append-oriented scientific stream for v1

ADR 0004 established ordered primitive observations. V1 SHOULD persist authoritative observations in append-oriented JSON Lines or an equivalently transparent lossless format.

Factorio's runtime API supports writing files to the `script-output` directory; implementation may use that mechanism for the Lua-owned stream and have the controller collect it after/during execution.

Live UDP/RCON/other transports may be added for dashboards/control, but they MUST NOT be the only authoritative record.

### 15. Event/telemetry records carry run and schema identity

The stream must be interpretable outside the live process.

Records or stream headers therefore provide enough identity to associate observations with:

```text
run_id
telemetry schema version
experiment tick / map tick as applicable
monotonic FISL sequence number
observation/event type
measurement method/provenance fields
```

A consumer must not need undocumented process state to order or interpret observations.

### 16. `summary.json` is derived and reproducible from authoritative inputs when feasible

The summary contains named final metrics/objectives/validity diagnostics for convenient consumption.

It is a derived artifact. Where the retained primitive/aggregate data are sufficient, the Python analysis layer SHOULD be able to recompute and validate the summary from the resolved scenario and telemetry.

The summary preserves exact numerators/denominators and provenance references where defined by preceding ADRs.

### 17. Final save capture is useful but is not the primary scientific record

FISL SHOULD support capturing a final Factorio save for debrief/debugging. Current Factorio runtime APIs provide save operations for single-player/multiplayer contexts, and the controller can also orchestrate save handling.

However:

- the final save does not replace telemetry/provenance;
- a missing final save does not automatically invalidate otherwise complete scientific measurements;
- a final save is an output artifact, not a new baseline unless deliberately promoted/versioned.

### 18. Provenance includes protocol and coverage validity summaries without erasing underlying data

The run summary/manifest records whether:

- required metric coverage was complete;
- protocol violations occurred;
- boundary/WIP balance diagnostics failed;
- unsupported states/carriers appeared;
- the run completed normally or aborted.

A flagged run remains stored. FISL does not delete inconvenient data because a validity rule failed.

### 19. Metric and objective provenance is dependency-linked

A final metric result identifies its source observation types/metric dependencies and resolved window/method metadata as required by prior ADRs.

An objective result identifies its source metric.

This creates an auditable chain:

```text
Factorio/runtime fact
      -> primitive observation
      -> metric/aggregation
      -> objective evaluation
```

### 20. Scenario metadata distinguishes semantic from explanatory content

The final schema SHOULD distinguish experiment-semantic fields from explanatory/course metadata such as:

```text
title
description
learning objectives
instructor notes
representational-limit notes
```

The complete package/source hash may change when explanatory content changes.

The resolved experiment hash SHOULD include only fields that affect execution, measurement, evaluation, or learner disclosure. Because learner disclosure can affect behavior, visibility is semantic and is included.

The canonicalization/compiler version determines this distinction and is itself provenance.

## Minimum manifest concept

```json
{
  "run_id": "...",
  "spec": "fisl/v1",
  "scenario": {
    "id": "fp-05-pull-production",
    "version": "1.0.0",
    "source_hash": "sha256:...",
    "resolved_hash": "sha256:..."
  },
  "baseline": {
    "save": "fp-05.zip",
    "sha256": "..."
  },
  "software": {
    "factorio_version": "...",
    "fisl_version": "...",
    "controller_version": "...",
    "compiler_version": "..."
  },
  "experiment_seed": 12345,
  "reproducibility_fingerprint": "sha256:...",
  "ticks": {
    "experiment_start_map_tick": 100,
    "experiment_end_map_tick": 90100,
    "duration": 90000
  },
  "status": "completed"
}
```

Exact fields/serialization are settled in the schema implementation.

## Consequences

### Positive

- Every result is traceable to exact experiment/world/software inputs.
- Retries remain distinct runs while still being recognizable as the same controlled condition.
- Human-readable scenario versions do not substitute for cryptographic identity.
- Resolved experiment semantics remain inspectable after authoring files change.
- The run dataset supports classroom debrief, regression testing, and later empirical research.
- Future stochastic experiments already have seed/replay provenance.
- Derived summaries can be independently verified against retained observations.

### Negative / trade-offs

- Run directories contain more metadata/artifacts than a minimal game mod would require.
- Development builds need disciplined version/commit recording.
- Exact cross-platform reproducibility may still depend on Factorio/mod behavior beyond FISL control; the manifest identifies the environment rather than promising impossible equivalence.
- Artifact hashing/canonicalization must be implemented consistently.

## Acceptance criteria

The run-provenance portion of Issue #1 is complete when:

1. every attempt has a unique run ID independent of scenario/seed;
2. scenario version is human metadata, with hashes providing authoritative identity;
3. source/package and resolved-experiment identities are distinguished;
4. the exact resolved experiment is stored with every run;
5. baseline saves are immutable inputs identified by cryptographic hash;
6. Factorio/FISL/mod/compiler identities are recorded;
7. every run records an experiment seed;
8. a reproducibility fingerprint identifies the controlled input condition without implying identical human actions;
9. simulation ticks and wall timestamps remain semantically distinct;
10. authoritative telemetry is append-oriented/lossless and not dependent on a live-only transport;
11. summary results remain dependency/provenance linked to measurements;
12. protocol/coverage problems flag rather than erase runs;
13. final saves are useful output artifacts but not substitutes for telemetry;
14. semantic experiment identity distinguishes execution/measurement/evaluation/disclosure fields from prose-only course metadata.

## References

- Factorio Runtime API: `LuaHelpers.write_file()` writes to the game's `script-output` directory.
- Factorio Runtime API: `LuaGameScript.auto_save()` / `server_save()` support save capture in their respective runtime contexts.
