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
| RV-001 | 0004 | The single `on_tick` coordinator can implement the declared checkpoint pipeline without relying on undocumented ordering among unrelated events. | Minimal mod logs event ticks plus coordinator checkpoints while building/mining/transferring entities. | FISL can queue notifications and deterministically normalize them at the coordinator without lost required facts. | Pending |
| RV-002 | 0003, 0017 | Standard source apparatus can enforce the one-way assumptions needed for net-withdrawal admission accounting strongly enough for canonical conserved-flow labs. | Exercise inserter/player interaction, filters, operability/minability/destructibility and attempted reverse insertion. | Canonical apparatus prevents normal learner reverse transfer; detectable violations are surfaced rather than masked. | Pending |
| RV-003 | 0003, 0017 | Sink settlement can read/remove all tracked output once per tick without ambiguous duplicate accounting. | Deliver known quantities at tick boundaries and compare physical sink state with emitted settlement facts. | Exact known `sink_delivery` sequence with clean post-settlement staging. | Pending |
| RV-004 | 0005, 0017 | A coarse physical census can count canonical belt contents without double-counting underlying transport lines. | Construct straight belts, underground belts, and splitters; compare naïve owner sums to deduplicated `LuaTransportLine` accounting. | Census equals known injected physical work-unit quantity across supported layouts. | Pending |
| RV-005 | 0005, 0017 | Physical census can account for work committed to active crafting exactly once when used as a ledger cross-check/decomposition measurement. | Move one workpiece through machine input → active craft → output and inspect Factorio inventory/progress state each phase. | Census never creates disappearance/double-counting for the supported conserved 1:1 recipe fixture. | Pending |
| RV-006 | 0007 | Adjacent checkpoint observations can determine actual crafting progress across normal progress, craft completion/reset, and high effective craft speed. | Record `crafting_progress`, `products_finished`, raw status, recipe and tick over controlled machines. | Interval classifier recognizes positive progress through completion/reset without false idle/productive intervals. | Pending |
| RV-007 | 0007 | Brownout/low-power operation can be distinguished as progressing + energy-limited versus stopped/unavailable at the required resolution. | Controlled power-limited crafting fixture. | Progress evidence and raw status support the ADR 0007 two-dimensional classification. | Pending |
| RV-008 | 0015 | RCON `/silent-command` configuration transfer is reliable with a conservatively chosen chunk size and exact hash verification. | Transfer increasingly large canonical JSON payloads using the proposed begin/append/commit protocol. | POC-sized resolved config transfers reproducibly with deterministic corruption/reorder rejection. | Pending |
| RV-009 | 0015 | `script-output` can sustain the authoritative POC telemetry strategy without materially degrading a small teaching fixture. | Run representative event/aggregate output volumes and profile UPS/file size. | POC fixture remains playable/headless-stable; authoritative records are complete. | Pending |
| RV-010 | 0015 | A generated companion configuration mod is a viable fallback if RCON configuration upload proves unnecessarily fragile. | Only if RV-008 is unsatisfactory: generate a run-specific config mod and launch server/client from the same mod directory. | Demonstrates a simpler reliable alternative without changing scientific clock/telemetry semantics. | Deferred fallback |
| RV-011 | 0001, 0015 | Dedicated/local-server pause and disconnect behavior can be configured to match deterministic POC policy. | Launch server with intended auto-pause settings; test connected, disconnected, reconnect, and headless operation. | Server does not silently pause a running interactive experiment; disconnect is detectable and can trigger the declared abort policy. | Pending |
| RV-012 | 0016 | Dynamic production-entity membership can be maintained incrementally from runtime events with canonical eligibility boundaries. | Build/remove matching machines during a run and record membership intervals. | New/removed machines enter/leave pooled denominators on the intended FISL boundaries. | Pending |

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