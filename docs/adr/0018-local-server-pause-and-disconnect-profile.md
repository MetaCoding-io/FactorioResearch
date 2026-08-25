# ADR 0018: Local-Server Pause and Disconnect Profile

- **Status:** Accepted
- **Runtime validation:** Pending; see `../RUNTIME_VALIDATION.md` RV-011
- **Scope:** FISL v1 interactive POC / canonical local-server topology
- **Clarifies:** ADR 0001 pause protocol semantics and ADR 0015 local server execution

## Context

ADR 0001 correctly established that only executed Factorio simulation ticks advance experiment time and that pausing is a protocol concern because it can give a human learner additional thinking time.

ADR 0015 later selected a locally orchestrated Factorio server plus ordinary graphical client as the canonical interactive topology.

That topology changes the practical meaning of pause controls:

- a multiplayer client opening its menu does not provide the same pause semantics as local single-player;
- a dedicated/local server may have operational auto-pause behavior when no players are connected;
- a client disconnect during a measured run must not silently freeze the server and later resume as though nothing happened;
- headless automated runs intentionally have no learner connected.

The initial POC needs one deterministic operational profile rather than a broad `allowed/prohibited` switch whose exact behavior varies with topology.

## Decision

### 1. The interactive v1 POC uses a fixed `prohibited` learner-pause policy

For the first local-server interactive implementation:

```text
pause_policy = prohibited
```

means the learner is not provided a FISL-supported way to suspend a RUNNING experiment for additional thinking time.

The POC does not need to implement a general learner-controlled pause/resume workflow.

The authoring/schema value `allowed` may remain reserved for future experiments, but the initial implementation SHOULD reject it for the canonical interactive profile until explicit controlled pause/resume semantics are implemented and tested.

### 2. Server operational auto-pause is disabled for RUNNING experiments

The controller MUST launch/configure the local Factorio server so loss of an attached graphical client does not silently pause the authoritative simulation as an incidental server default.

Exact Factorio configuration/flags are an implementation detail validated by RV-011.

The scientific requirement is:

> A RUNNING interactive experiment must never become paused merely because the server has zero connected learners without FISL detecting and applying the declared disconnect policy.

### 3. Interactive learner disconnect during `RUNNING` aborts the POC run

For a run declared interactive/learner-attended, loss of the required learner connection during `RUNNING` produces an authoritative event such as:

```text
learner_disconnected
```

and transitions the run to `ABORTED` at the next safe FISL lifecycle boundary.

Collected data are preserved.

The run is not silently paused and later resumed.

This simple policy is appropriate to the loopback/local POC where an unexpected disconnect is operationally closer to a client crash/experiment interruption than an intentional scientific treatment.

### 4. `READY` is not experiment time and may use lifecycle holding behavior

Before the learner presses Start, FISL may hold the world in whatever safe lifecycle state is required to validate bindings and wait for the client.

Such lifecycle holding is not a learner `pause_policy` event because the experiment has not entered `RUNNING` and `experiment_tick` has not begun.

The distinction is:

```text
READY lifecycle hold != pause during experiment time
```

### 5. FISL-controlled terminal pause is allowed after the final scientific observation

ADR 0001 recommends preventing post-run simulation drift after the final boundary.

The runtime may therefore pause/hold the world **after** final observations have been captured and the experiment has transitioned out of `RUNNING`.

This is not a prohibited learner pause and does not create experiment time.

### 6. Headless runs explicitly do not require a learner connection

Regression/batch fixtures use the same server/Lua scientific runtime but declare headless execution.

For those runs:

```text
required_learner_connection = false
```

The absence of a graphical client is expected and does not trigger the interactive disconnect-abort rule.

### 7. Connection mode is run protocol metadata

The run configuration/provenance distinguishes at least:

```text
interactive
headless
```

For interactive runs, provenance should record relevant connection/disconnect events without storing unnecessary personal/network data.

### 8. Future controlled pause/resume remains possible but is outside the POC

A later scenario/profile may explicitly define:

```text
disconnect -> controlled FISL pause
reconnect -> explicit resume
```

or learner-requested pause windows.

Such a feature must specify:

- who may request pause;
- when the pause becomes effective;
- whether wall-time duration matters;
- how connection loss is distinguished from intentional pause;
- what telemetry/provenance is emitted;
- which comparisons consider pause admissible.

It should receive a new/superseding ADR rather than being inferred from the old `allowed` label.

## POC resolved profile

Conceptually:

```yaml
experiment:
  time:
    game_speed:
      policy: fixed
      value: 1.0
    pause_policy: prohibited

run_profile:
  mode: interactive
  server_auto_pause: false
  disconnect_policy: abort
```

`run_profile` fields may live in `RunConfiguration` rather than stable scenario semantics when they are purely execution-topology choices. If a field can change learner experimental conditions, it must participate in the appropriate resolved/fingerprint identity according to ADR 0013.

## Consequences

### Positive

- Local multiplayer topology no longer has ambiguous pause semantics.
- Client crashes/disconnects cannot silently create extra thinking time or hidden simulation freezes.
- Headless fixtures continue to use the same scientific runtime without pretending a learner exists.
- General pause/resume complexity is deferred until a scenario genuinely needs it.

### Negative / trade-offs

- The first interactive POC does not support deliberate learner pausing.
- A transient client disconnect aborts the attempt rather than trying to recover it.
- Controller/server launch configuration becomes part of runtime validation.

## Acceptance criteria

1. canonical interactive POC scenarios use `pause_policy: prohibited`;
2. the local server is configured so zero connected clients do not silently auto-pause a running experiment;
3. unexpected required-learner disconnect during RUNNING emits an event and aborts while preserving data;
4. READY lifecycle holding is not counted as experiment pause/time;
5. final post-observation hold/pause is permitted after RUNNING ends;
6. headless runs explicitly bypass the learner-connection requirement;
7. RV-011 confirms the actual Factorio 2.0.77 server behavior/configuration used to implement these rules.
