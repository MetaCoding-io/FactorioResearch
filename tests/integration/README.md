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

## First-run findings (resolved on Factorio 2.0.77)

The first execution against the real runtime surfaced four behaviors that
contradicted the harness as originally written; all are fixed and documented
as spike findings in `docs/RUNTIME_VALIDATION.md`:

- the first `/silent-command` of a save is swallowed by the achievement
  confirmation prompt (controller now primes the console after connect);
- runtime writes to inserter `pickup_position`/`drop_position` are silently
  ignored (the bootstrap places west-facing inserters instead);
- source material staged at READY was withdrawn before experiment start
  (staging moved into the start checkpoint);
- `line_equals`-based belt census deduplication undercounts — the naive
  per-entity segment sum is the exact method on 2.0.77.

Still true: if `helpers.decode_string` is absent/renamed on a future pinned
build, config upload fails at commit — that is RV-008 evidence; the
companion-mod fallback (RV-010) is the designed alternative.
