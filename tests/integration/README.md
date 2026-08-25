# FISL runtime-validation spike (Issue #2 Stage A)

These tests execute the `RUNTIME_VALIDATION.md` checks against a **real**
Factorio 2.0.x headless server. They are skipped automatically when no binary
is configured.

## Prerequisites

1. Factorio headless server ≥ 2.0.77 (free download):
   <https://factorio.com/get-download/2.0.77/headless/linux64>

   ```sh
   tar -xJf factorio-headless_linux_2.0.77.tar.xz -C ~/factorio-headless
   ```

2. This repo installed: `pip install -e .[dev]`

## Running

```sh
FACTORIO_BIN=~/factorio-headless/factorio/bin/x64/factorio \
    pytest tests/integration -v
```

What happens per session:

- a pristine fixture baseline save is created once (`--create`, fixed seed,
  no water/trees/enemies), with `fisl-core` + `fisl-factory-physics` active;
- each test launches an isolated loopback server (run-scoped write-data,
  random RCON password, `auto_pause: false` per ADR 0018);
- the one-workpiece line is built by a bootstrap `/silent-command`
  (inserter `pickup_position`/`drop_position` set explicitly);
- the resolved scenario is uploaded through the chunked RCON protocol and the
  run executes headlessly at 10× game speed (wall-clock only; simulation-time
  semantics are unchanged per ADR 0001 §4).

## Evidence

Passing tests append records to `tests/integration/evidence/rv-evidence.jsonl`
in the format required by `RUNTIME_VALIDATION.md` (Factorio version, FISL
commit, fixture, expected/observed, pass). Review and commit that file, then
update the RV status column in `docs/RUNTIME_VALIDATION.md` with a pointer to
the evidence.

## Test ↔ RV map

| Test | RV items |
|---|---|
| `test_rv008_config_transfer_multi_chunk` / `..._corrupt_transfer_rejected` | RV-008 |
| `test_one_workpiece_vertical_slice` | RV-001, RV-002, RV-003, RV-004, RV-005 |
| `test_steady_flow_littles_law_agreement` | RV-009 (+ Stage B metrics) |
| `test_census_discrepancy_flagged_never_reconciled` | RV-004 / ADR 0017 §8-§9 |
| `test_rv002_hardening_and_reverse_flow` | RV-002 |
| `test_rv006_craft_progress_probe` | RV-006 |
| `test_rv011_headless_no_pause_and_post_completion_rcon` | RV-011 |
| `test_retry_same_fingerprint_new_run_id` | ADR 0013/0014 identity |

Not yet covered here: RV-007 (brownout classification — needs the machine-state
adapter, deferred with Lab 4 scope) and RV-012 (dynamic entity sets, likewise
deferred by Issue #2).

## Known first-run risks

- Inserter reach: `fast-inserter` pickup/drop positions are set to exact
  tiles; if the runtime clamps them differently than expected, the workpiece
  won't flow and `test_one_workpiece_vertical_slice` will fail with zero
  admissions — adjust the coordinates in `fixture_world.py` (`BOOTSTRAP_LUA`).
- `map-gen-settings` autoplace control names (`trees`, `rocks`, `enemy-base`)
  and the `electric-energy-interface` prototype are 2.0 names; the bootstrap
  clears the build area defensively either way.
- If `helpers.decode_string` is absent/renamed on the pinned build, config
  upload fails at commit — that is exactly RV-008 evidence; the companion-mod
  fallback (RV-010) is the designed alternative.
