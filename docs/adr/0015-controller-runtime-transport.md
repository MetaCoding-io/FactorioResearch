# ADR 0015: Python Controller ↔ Factorio Runtime Transport

- **Status:** Accepted
- **Scope:** FISL v1 implementation architecture

## Context

The architectural split requires a Python controller to:

- validate/compile a scenario;
- launch a baseline world;
- provide the resolved run configuration to the FISL Lua runtime;
- request run start/abort/save operations;
- observe coarse lifecycle status;
- collect authoritative output artifacts.

The Lua runtime must remain authoritative for simulation-tick behavior. The controller cannot simply write an arbitrary JSON file and expect a Factorio runtime mod to open it: Factorio's Lua environment intentionally restricts arbitrary filesystem access. The runtime can write to `script-output`, while cross-script calls are available through registered remote interfaces inside Factorio.

FISL therefore needs a low-volume control/configuration transport that does not become the real-time experimental clock and a separate durable telemetry path.

## Decision

### 1. V1 runs the authoritative Factorio world as a locally orchestrated server

The canonical v1 execution topology is:

```text
Python FISL controller
      |
      | process lifecycle + RCON control/config
      v
local Factorio server (authoritative simulation)
      |
      | normal Factorio multiplayer protocol
      v
Factorio graphical client / learner
```

For a one-person lab the server normally runs on the same machine and binds to loopback/local interfaces.

This topology is chosen even for single-learner use because it provides a supported controller channel and extends naturally to future multiplayer organizational experiments.

### 2. The controller starts from a working copy of the declared baseline save

The controller verifies the baseline hash, creates/uses a per-run working save location, and launches Factorio in server mode using the declared baseline.

The immutable canonical baseline is never overwritten.

Server process arguments, mod directory, ports, logs, and output directories are run-scoped.

### 3. RCON is the v1 control/configuration channel

The Factorio server is launched with RCON enabled on a controller-selected port and strong per-run password.

RCON is used for low-volume operations such as:

```text
runtime readiness query
resolved configuration upload
configuration validation/commit
start request
abort request
status query
final save request
selected debug commands
```

RCON is **not** used for per-tick schedules or measurement logic.

### 4. The FISL core mod exposes a narrow versioned remote interface

The mod registers a `remote` interface with explicitly versioned operations conceptually similar to:

```text
get_protocol_version()
begin_configuration(run_id, content_hash, total_bytes)
append_configuration(chunk_index, payload)
commit_configuration()
request_start()
request_abort(reason)
get_status()
request_final_save(name)
```

Exact function names may differ, but the interface remains narrow and lifecycle-oriented.

The controller invokes it through server console/RCON scripting commands.

### 5. Resolved scenario configuration is transferred as canonical JSON text

Python owns YAML parsing/schema validation and compilation.

The Lua runtime receives a resolved canonical JSON document, not authoring YAML.

The runtime decodes the JSON into plain Lua data and validates protocol/version/hash/basic invariants before entering `READY`.

Lua does not implement a second YAML/schema compiler.

### 6. Configuration upload supports chunking

The transport MUST NOT assume the full resolved scenario safely fits inside one console/RCON command.

The protocol therefore supports chunked transfer:

```text
begin -> append chunk 0..N -> commit
```

The Lua runtime:

- accepts chunks only while not running;
- verifies count/length/hash on commit;
- rejects duplicate/out-of-order/corrupt transfer according to a deterministic protocol;
- discards incomplete configuration on reset/restart.

The exact chunk size is an implementation constant/protocol field, not scenario semantics.

### 7. RCON start is a request; Lua chooses the authoritative clean tick boundary

When Python calls `request_start()`, Lua records a pending start request.

ADR 0001/0004 remain authoritative: the experiment begins at the next eligible clean simulation-tick boundary selected by the Lua coordinator.

RCON/network arrival time never becomes `experiment_tick` zero directly.

The same principle applies to phase changes: they are never externally scheduled by wall-clock/RCON timing.

### 8. Authoritative telemetry remains file-backed, not RCON-backed

The Lua runtime writes append-oriented authoritative telemetry/events through Factorio's supported `script-output` facility.

Python may tail/collect those files for live tooling, but a dropped RCON connection does not erase scientific observations.

RCON status responses are operational convenience, not the scientific record.

### 9. The learner client consumes normal multiplayer state plus FISL in-game UI

The learner uses an ordinary graphical Factorio client connected to the local server.

FISL does not proxy gameplay actions through Python.

The controller MAY automatically launch/connect the graphical client using Factorio command-line multiplayer-connect options. Manual connect is an acceptable fallback.

### 10. Default networking is loopback/private and ephemeral

For v1 local use:

- RCON binds to loopback only;
- the RCON password is randomly generated per run/session;
- game server ports may bind locally/private as needed;
- no public internet exposure is required.

RCON credentials are operational secrets and SHOULD NOT be emitted into learner-facing telemetry/reports.

Future shared/multiplayer deployment can define stronger authentication/network policy without changing the scientific protocol.

### 11. Controller failure does not silently transfer clock authority

Once a configured experiment is running, Lua continues simulation-synchronous behavior from the resolved configuration even if the Python controller temporarily disappears.

The scenario MAY define an operational policy to abort when controller supervision is lost, but the controller does not have to send recurring timing messages for the experiment to remain correct.

### 12. Runtime configuration is immutable after start except through explicitly modeled controls

After `RUNNING` begins, the resolved scenario configuration is frozen for the run.

Ad-hoc RCON commands MUST NOT mutate demand rates, metric definitions, visibility, objectives, or other experiment semantics unless the scenario explicitly defines that change as a runtime control/input and records it as an authoritative event.

Debug mutation of a running world flags protocol validity.

### 13. Protocol compatibility is negotiated before configuration

Python queries the Lua remote-interface protocol version before upload.

Incompatible controller/mod protocol versions fail before `READY`.

The run manifest records the protocol version along with controller/core-mod versions.

### 14. The topology supports headless automated execution without a graphical client

For regression tests and batch fixtures, the controller may run the Factorio server without launching a learner client.

The same resolved configuration, remote protocol, Lua coordinator, and telemetry contract are used.

This avoids maintaining separate scientific runtimes for classroom and automated testing.

### 15. Alternative transports are future-compatible but not authoritative in v1

Future implementations may add:

- UDP live telemetry;
- WebSocket/dashboard bridges;
- stdin/server-console control;
- an external message bus;
- a dedicated multiplayer orchestration service.

They must preserve the core separation:

```text
control/config transport != simulation clock
live transport != authoritative telemetry record
```

## Consequences

### Positive

- Python can inject arbitrary validated run configuration without unsafe file-reading assumptions in Lua.
- The authoritative simulation naturally supports future multiplayer.
- RCON is used only where network latency is scientifically irrelevant.
- The same server runtime supports interactive labs and headless regression tests.
- File-backed telemetry remains durable if control connections fail.
- Configuration immutability and protocol versioning make runs auditable.

### Negative / trade-offs

- A local interactive lab normally runs both a server process and graphical client rather than pure single-player.
- Controller implementation must manage ports, process lifecycle, RCON credentials, and client connection.
- JSON configuration needs a chunked/escaped transport protocol.
- Scenario authors/developers need server-compatible mod/save handling from the beginning.

## Acceptance criteria

This architecture is ready for implementation when:

1. the authoritative world runs in a controller-launched Factorio server;
2. the learner connects with a normal Factorio client;
3. Python uses RCON only for low-volume configuration/lifecycle control;
4. the FISL mod exposes a narrow versioned remote interface;
5. Python sends resolved canonical JSON, not YAML;
6. config transfer handles chunking and verifies content identity;
7. Lua schedules actual start on a clean simulation-tick boundary;
8. authoritative telemetry is file-backed via `script-output` rather than dependent on RCON;
9. runtime semantic config is frozen after start except for explicitly modeled inputs;
10. default RCON exposure is loopback/private with ephemeral credentials;
11. the same topology can run headlessly for automated tests.

## References

- Factorio command-line parameters support dedicated server startup, multiplayer client connection, and RCON port/password configuration.
- Factorio Runtime API `LuaRemote` supports mod-registered remote interfaces/calls.
- Factorio console/RCON supports server-side `/silent-command` Lua execution.
- Factorio Runtime API `LuaHelpers.write_file()` supports output to `script-output`.
