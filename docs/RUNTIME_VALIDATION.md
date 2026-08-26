# FISL v1 Runtime Validation Gate

**Status:** Required pre-POC spike plan  
**Initial target:** Factorio stable 2.0.77  
**Purpose:** Separate accepted scientific/design semantics from Factorio-specific implementation hypotheses that still require empirical confirmation.

## Principle

An ADR may be **Accepted** while a Factorio-specific implementation assumption remains **Runtime validation: Pending**.

Accepted means the project has chosen the semantic/architectural behavior it wants. It does **not** mean every Factorio API assumption has already been demonstrated in the pinned runtime.

If a runtime validation fails:

1. preserve the evidence;
2. determine whether only the implementation technique failed or the accepted semantic is infeasible;
3. prefer a different implementation when the semantic remains feasible;
4. propose a superseding ADR when the semantic itself must change;
5. never silently weaken the scientific contract.

The first implementation work should execute this validation matrix before large framework construction.

## Validation matrix

| ID | Dependent ADR(s) | Hypothesis to validate | Spike / evidence required | Pass condition | Status |
|---|---|---|---|---|---|
| RV-001 | 0004 | The single `on_tick` coordinator can implement the declared checkpoint pipeline without relying on undocumented ordering among unrelated events. | Minimal mod logs event ticks plus coordinator checkpoints while building/mining/transferring entities. | FISL can queue notifications and deterministically normalize them at the coordinator without lost required facts. | Confirmed on Factorio 2.0.77 (`test_one_workpiece_vertical_slice`, `test_retry_same_fingerprint_new_run_id`; evidence log) |
| RV-002 | 0003, 0017 | Standard source apparatus can enforce the one-way assumptions needed for net-withdrawal admission accounting strongly enough for canonical conserved-flow labs. | Exercise inserter/player interaction, filters, operability/minability/destructibility and attempted reverse insertion. | Canonical apparatus prevents normal learner reverse transfer; detectable violations are surfaced rather than masked. | Confirmed on Factorio 2.0.77 (`test_rv002_hardening_and_reverse_flow`, vertical slice; see finding 3 below) |
| RV-003 | 0003, 0017 | Sink settlement can read/remove all tracked output once per tick without ambiguous duplicate accounting. | Deliver known quantities at tick boundaries and compare physical sink state with emitted settlement facts. | Exact known `sink_delivery` sequence with clean post-settlement staging. | Confirmed on Factorio 2.0.77 (`test_one_workpiece_vertical_slice`) |
| RV-004 | 0005, 0017 | A coarse physical census can count canonical belt contents without double-counting underlying transport lines. | Construct straight belts, underground belts, and splitters; compare naïve owner sums to deduplicated `LuaTransportLine` accounting. | Census equals known injected physical work-unit quantity across supported layouts. | Confirmed on Factorio 2.0.77 for straight belts, with the technique inverted — see finding 4. Underground/splitter layouts still pending. |
| RV-005 | 0005, 0017 | Physical census can account for work committed to active crafting exactly once when used as a ledger cross-check/decomposition measurement. | Move one workpiece through machine input → active craft → output and inspect Factorio inventory/progress state each phase. | Census never creates disappearance/double-counting for the supported conserved 1:1 recipe fixture. | Confirmed on Factorio 2.0.77 (`test_one_workpiece_vertical_slice`: census stays exactly 1 through input → active craft → output) |
| RV-006 | 0007 | Adjacent checkpoint observations can determine actual crafting progress across normal progress, craft completion/reset, and high effective craft speed. | Record `crafting_progress`, `products_finished`, raw status, recipe and tick over controlled machines. | Interval classifier recognizes positive progress through completion/reset without false idle/productive intervals. | **Confirmed on Factorio 2.0.77** (2026-08-26). API evidence: `test_rv006_craft_progress_probe`. Interval classifier (`fisl/classify.lua` + `fisl/machine_state.lua`, issue #7, `products_finished`-first completion-wrap handling) passed all per-state fixtures in `tests/integration/test_machine_state.py` against the real runtime: productive→starved drain with zero unknown gaps across multiple completion wraps, blocked/output_blocked, unavailable/energy_unavailable, disabled/disabled_control, idle_other/configuration. |
| RV-007 | 0007 | Brownout/low-power operation can be distinguished as progressing + energy-limited versus stopped/unavailable at the required resolution. | Controlled power-limited crafting fixture. | Progress evidence and raw status support the ADR 0007 two-dimensional classification. | **Confirmed on Factorio 2.0.77** (2026-08-26): `test_rv007_brownout_stays_productive_with_energy_limited` — with an undersized electric-energy interface the machine kept measurable craft progress and classified `productive` + `energy_limited` on raw `low_power`, not `unavailable`. |
| RV-008 | 0015 | RCON `/silent-command` configuration transfer is reliable with a conservatively chosen chunk size and exact hash verification. | Transfer increasingly large canonical JSON payloads using the proposed begin/append/commit protocol. | POC-sized resolved config transfers reproducibly with deterministic corruption/reorder rejection. | Confirmed on Factorio 2.0.77 (`test_rv008_config_transfer_multi_chunk` at forced 200-byte chunks; corrupt payload deterministically rejected) |
| RV-009 | 0015 | `script-output` can sustain the authoritative POC telemetry strategy without materially degrading a small teaching fixture. | Run representative event/aggregate output volumes and profile UPS/file size. | POC fixture remains playable/headless-stable; authoritative records are complete. | Confirmed for POC volume on Factorio 2.0.77 (`test_steady_flow_littles_law_agreement`: complete stream at 10× speed, ~tens of KB per simulated minute; Python recomputation matches Lua accumulators) |
| RV-010 | 0015 | A generated companion configuration mod is a viable fallback if RCON configuration upload proves unnecessarily fragile. | Only if RV-008 is unsatisfactory: generate a run-specific config mod and launch server/client from the same mod directory. | Demonstrates a simpler reliable alternative without changing scientific clock/telemetry semantics. | Not needed — RV-008 confirmed |
| RV-011 | 0001, 0015 | Dedicated/local-server pause and disconnect behavior can be configured to match deterministic POC policy. | Launch server with intended auto-pause settings; test connected, disconnected, reconnect, and headless operation. | Server does not silently pause a running interactive experiment; disconnect is detectable and can trigger the declared abort policy. | Headless profile confirmed on Factorio 2.0.77 (`test_rv011_headless_no_pause_and_post_completion_rcon`: ticks advance with zero players under `auto_pause:false`; RCON responsive post-completion). Interactive connect/disconnect/reconnect still pending. |
| RV-012 | 0016 | Dynamic production-entity membership can be maintained incrementally from runtime events with canonical eligibility boundaries. | Build/remove matching machines during a run and record membership intervals. | New/removed machines enter/leave pooled denominators on the intended FISL boundaries. | Implemented (issue #8): membership adds drain from build-event notifications at checkpoint boundaries, removals are validity-driven, eligibility intervals bound spans and pooled denominators. Fixture written (`tests/integration/test_dynamic_membership.py`) — execution against the real runtime pending. |

## Spike findings (Factorio 2.0.77, 2026-08-25 onward)

Executed by `tests/integration/` against a real 2.0.77 headless server;
per-check records live in `tests/integration/evidence/rv-evidence.jsonl`.
These runtime behaviors contradicted the implementation as first written —
in each case the accepted semantic survived and only the technique changed:

1. **First Lua console command is swallowed.** Factorio 2.0 answers the
   first `/silent-command` of a save with "Using Lua console commands will
   disable achievements. Please repeat the command to proceed." and does not
   execute it. The controller now primes the console after RCON connect by
   repeating an identical no-op probe until acknowledged
   (`FactorioServer._prime_lua_console`).
2. **Runtime inserter vector writes are ignored.** Assigning
   `LuaEntity.pickup_position` / `drop_position` on standard inserters
   silently leaves the default vectors (no error). Fixtures must use the
   stock direction convention (pickup from the facing tile, drop opposite);
   custom vectors would require a prototype with `allow_custom_vectors`.
3. **READY-staged source material is withdrawn before start.** The world
   keeps ticking between READY and experiment start, so material staged at
   binding was picked up by the live inserter before the settlement pipeline
   existed — a real completion with no admission (ledger WIP −1). Initial
   staging now happens inside the experiment-start checkpoint
   (`ports.stage_initial`), so the first possible withdrawal falls in the
   settled interval [0, 1).
4. **`line_equals` deduplication undercounts; the naive sum is exact.** On
   2.0.77 each belt entity's `LuaTransportLine.get_contents()` returns only
   that entity's own segment, and `line_equals` reports true across
   *different* segments of the same merged line group. Deduplicating by
   `line_equals` therefore drops real contents (observed: 15 physical items
   counted as 8 on a 4-belt straight run), while the naive
   per-entity/per-line sum reconciles exactly with the conservation ledger.
   The census now uses the naive sum. Underground belts and splitters were
   not exercised and keep RV-004 partially pending.
5. **Per-tick `game.get_entity_by_unit_number` returned nil for live
   machines (2026-08-26).** The machine-state adapter's first execution
   classified 100% of intervals as `coverage_missing` with no raw status:
   the per-tick unit-number lookup returned nil for the very machines the
   READY membership scan had just found (unit numbers were valid;
   membership, telemetry, and the whole run pipeline worked). The adapter
   now stores the `LuaEntity` references themselves in the tracker
   (explicitly supported in `storage`; revalidated on save/load) and checks
   `entity.valid` each tick — the standard modding pattern, and immune to
   whatever the lookup's actual contract is. Missing measurement announced
   itself as `coverage_missing` rather than fake idle time, exactly as ADR
   0007 §24 intends — the failure mode was visible, not silent.

## First validation fixture: one-workpiece vertical slice

The preferred spike is deliberately small because it exercises many assumptions at once:

```text
FISL source
   ↓
inserter
   ↓
belt / underground / optional splitter
   ↓
inserter
   ↓
assembler: rough-workpiece -> finished-workpiece (1:1)
   ↓
inserter
   ↓
FISL sink
```

Run with exactly one admitted conserved workpiece first, then with a steady deterministic stream.

The fixture should demonstrate:

- clean simulation-tick start;
- source admission and sink completion;
- conservation-ledger WIP remaining exactly one between admission and completion;
- physical census agreeing with the ledger at cross-check points;
- correct belt-line deduplication;
- active-craft census continuity;
- craft-progress classification;
- telemetry durability;
- baseline reset/retry.

This fixture is both an API-validation spike and the nucleus of the first real FISL POC.

## Validation evidence

When an item passes, record at least:

```text
Factorio exact version
FISL commit SHA
fixture/scenario ID
command/test used
expected behavior
observed behavior
relevant raw API values/log excerpt
pass/fail
```

Factorio-sensitive ADRs may then update their annotation to, for example:

```text
Runtime validation: Confirmed on Factorio 2.0.77 by RV-006/RV-007
```

## Performance evidence

Do not infer performance limits from architecture alone. For the vertical-slice spike collect:

- UPS / update-time impact with FISL disabled vs enabled;
- number of measured machines/transport lines;
- telemetry bytes per simulated minute;
- number of file writes/records after compression/batching strategy;
- physical-census cost at candidate cross-check cadences.

The goal is not to establish a universal factory-size limit. It is to prove the initial small teaching laboratory has substantial performance margin and identify the first scaling bottleneck.

## Source-of-truth rule

The accepted ADRs define intended scientific semantics. This file records which Factorio-specific assumptions have been empirically demonstrated. A failed runtime assumption does not silently rewrite an ADR.