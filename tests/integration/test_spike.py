"""Runtime-validation spike (Issue #2 Stage A) + vertical-slice assertions.

Each passing test appends evidence rows for the RV items it exercises.
Run with a real binary:

    FACTORIO_BIN=~/factorio/bin/x64/factorio pytest tests/integration -v
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import fisl.controller.protocol as protocol_module
from tests.integration.fixture_world import SpikeSession, create_baseline, fixture_scenario


@pytest.fixture(scope="session")
def baseline(factorio, tmp_path_factory) -> Path:
    workspace = tmp_path_factory.mktemp("baseline")
    return create_baseline(factorio, workspace)


def _session(factorio, tmp_path, baseline, scenario):
    return SpikeSession(factorio, tmp_path / "server", baseline, scenario)


# ---------------------------------------------------------------------------
# RV-008: chunked RCON configuration transfer
# ---------------------------------------------------------------------------

def test_rv008_config_transfer_multi_chunk(factorio, tmp_path, baseline, evidence, monkeypatch):
    monkeypatch.setattr(protocol_module, "CHUNK_SIZE", 200)  # force many chunks
    scenario = fixture_scenario(measured="10s")
    with _session(factorio, tmp_path, baseline, scenario) as session:
        response = session.configure()
        status = session.protocol.get_status()
    assert status["lifecycle"] == "READY", status
    evidence.record(
        "RV-008",
        fixture="rv-spike-fixture multi-chunk upload (chunk=200B)",
        expected="config transfers in verified chunks; runtime reaches READY",
        observed=f"commit={response}, lifecycle={status['lifecycle']}",
        passed=True,
    )


def test_rv008_corrupt_transfer_rejected(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(measured="10s")
    with _session(factorio, tmp_path, baseline, scenario) as session:
        proto = session.protocol
        proto._call("begin_configuration", "BADRUN", 12345, 1)
        proto._call("append_configuration", 1, "bm90IHZhbGlkIGRlZmxhdGU=")
        response = proto._call("commit_configuration")
    assert isinstance(response, dict) and response.get("ok") is False
    evidence.record(
        "RV-008",
        fixture="corrupt payload commit",
        expected="deterministic rejection, no READY",
        observed=str(response),
        passed=True,
    )


# ---------------------------------------------------------------------------
# The one-workpiece vertical slice: RV-001/002/003/004/005 together
# ---------------------------------------------------------------------------

def test_one_workpiece_vertical_slice(factorio, tmp_path, baseline, evidence):
    # Exactly one admission: initial staging of 1, schedule never active.
    scenario = fixture_scenario(
        warmup="5s",
        measured="60s",
        supply={
            "mode": "scheduled",
            "initial_quantity": 1,
            "active_phases": [],
            "schedule": {"type": "constant", "rate": "1/min"},
        },
        census_every="60t",
    )
    with _session(factorio, tmp_path, baseline, scenario) as session:
        session.configure()
        session.start(speed=10.0)
        status = session.wait_done()
        records = session.telemetry_records()

    assert status["lifecycle"] == "COMPLETED", status
    ledgers = status["ledgers"]["workpiece_flow"]
    assert ledgers["admissions"] == 1, ledgers
    assert ledgers["completions"] == 1, ledgers
    assert ledgers["wip"] == 0, ledgers

    withdrawals = [r for r in records if r["type"] == "source_withdrawal"]
    deliveries = [r for r in records if r["type"] == "sink_delivery"]
    assert sum(r["quantity"] for r in withdrawals) == 1
    assert sum(r["quantity"] for r in deliveries) == 1
    admission_tick = withdrawals[0]["interval_end_tick"]
    completion_tick = deliveries[0]["interval_end_tick"]
    assert completion_tick > admission_tick

    # RV-001: single-writer ordering — strictly increasing sequence numbers,
    # phase transitions at the compiled boundaries.
    seqs = [r["seq"] for r in records]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    phase_ticks = {r["phase"]: r["experiment_tick"] for r in records if r["type"] == "phase_transition"}
    assert phase_ticks == {"warmup": 0, "measured": 300}
    evidence.record(
        "RV-001",
        fixture="one-workpiece slice",
        expected="coordinator emits ordered facts; phase boundaries exact",
        observed=f"seq monotonic over {len(seqs)} records; phase ticks {phase_ticks}",
        passed=True,
    )

    # RV-003: sink settlement — exact known delivery, staging emptied.
    evidence.record(
        "RV-003",
        fixture="one-workpiece slice",
        expected="exactly one sink_delivery of quantity 1",
        observed=f"deliveries={[(r['quantity'], r['interval_end_tick']) for r in deliveries]}",
        passed=True,
    )

    # RV-004/RV-005: every complete census between admission and completion
    # must equal ledger WIP=1 while the workpiece traverses belts, inserter
    # hands, and the active craft; no discrepancies anywhere.
    censuses = [r for r in records if r["type"] == "wip_census"]
    in_flight = [r for r in censuses if admission_tick <= r["experiment_tick"] < completion_tick]
    discrepancies = [r for r in records if r["type"] == "wip_census_discrepancy"]
    assert discrepancies == [], discrepancies
    assert in_flight, "no census fell inside the traversal window; lengthen traversal or census cadence"
    for record in in_flight:
        assert record["census_wip"] == record["ledger_wip"] == 1, record
    holders_seen = set()
    for record in in_flight:
        for holder, quantity in record["decomposition"].items():
            if quantity > 0:
                holders_seen.add(holder)
    evidence.record(
        "RV-004",
        fixture="one-workpiece slice",
        expected="belt census counts the workpiece exactly once (no line double count)",
        observed=f"{len(in_flight)} in-flight censuses all agree; holders observed: {sorted(holders_seen)}",
        passed=True,
    )
    evidence.record(
        "RV-005",
        fixture="one-workpiece slice",
        expected="census continuity through active craft (WIP stays 1, never 0 or 2)",
        observed=f"census values in flight: {[r['census_wip'] for r in in_flight]}",
        passed=True,
    )
    evidence.record(
        "RV-002",
        fixture="one-workpiece slice",
        expected="net-withdrawal admission accounting yields exactly one admission",
        observed=f"withdrawals={[(r['quantity'], r['interval_end_tick']) for r in withdrawals]}",
        passed=True,
    )


# ---------------------------------------------------------------------------
# Steady flow: throughput + Little's Law + Lua/Python agreement
# ---------------------------------------------------------------------------

def test_steady_flow_littles_law_agreement(factorio, tmp_path, baseline, evidence):
    from fisl.metrics.aggregation import compute_summary

    scenario = fixture_scenario(warmup="10s", measured="60s", supply={"mode": "replenish", "target": 20})
    with _session(factorio, tmp_path, baseline, scenario) as session:
        session.configure()
        session.start(speed=10.0)
        status = session.wait_done()
        telemetry = session.telemetry_path()
        summary = compute_summary(session.resolved, session.run_config, telemetry)

    assert status["lifecycle"] == "COMPLETED"
    throughput = summary["metrics"]["measured_throughput"]
    assert throughput["completed_quantity"] > 0, "no completions in measured window"
    average = summary["metrics"]["average_wip"]
    assert average["coverage_complete"] is True
    assert average["census_validity"]["valid"] is True
    cycle = summary["metrics"]["loaded_cycle_time"]
    assert cycle["method"] == "little_law_derived"
    assert cycle["value_seconds"] and cycle["value_seconds"] > 0
    verification = summary["lua_cross_verification"]
    assert verification["available"] and verification["agrees"], verification
    evidence.record(
        "RV-009",
        fixture="steady flow 60s measured window",
        expected="telemetry stream complete and Python recomputation matches Lua accumulators",
        observed=(
            f"completed={throughput['completed_quantity']}, "
            f"avg_wip={average['value']:.2f}, ct={cycle['value_seconds']:.2f}s, "
            f"telemetry_bytes={telemetry.stat().st_size}"
        ),
        passed=True,
    )


# ---------------------------------------------------------------------------
# Deliberate discrepancy: ledger never silently reconciled
# ---------------------------------------------------------------------------

def test_census_discrepancy_flagged_never_reconciled(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="30s", supply={"mode": "replenish", "target": 20})
    with _session(factorio, tmp_path, baseline, scenario) as session:
        session.configure()
        session.start(speed=10.0)
        time.sleep(1.5)  # let the run get going
        # Undeclared material appears inside the system: conservation violated.
        session.sc(
            'game.surfaces["nauvis"].create_entity{name="item-on-ground", '
            'position={-1.5, 3.5}, stack={name="fisl-rough-workpiece", count=3}} '
            'rcon.print("injected")'
        )
        status = session.wait_done()
        records = session.telemetry_records()

    discrepancies = [r for r in records if r["type"] == "wip_census_discrepancy"]
    assert discrepancies, "injected ground workpieces were never flagged"
    first = discrepancies[0]
    assert first["discrepancy"] == 3
    assert first["suspect_from_tick"] < first["suspect_to_tick"]
    # The ledger was not rewritten: admissions/completions remain port-driven.
    ledgers = status["ledgers"]["workpiece_flow"]
    assert ledgers["wip"] == ledgers["initial_wip"] + ledgers["admissions"] - ledgers["completions"]
    evidence.record(
        "RV-004",
        fixture="deliberate 3-unit ground injection",
        expected="census discrepancy flagged with conservative interval; ledger untouched",
        observed=f"first discrepancy: {first}",
        passed=True,
    )


# ---------------------------------------------------------------------------
# RV-002: apparatus hardening + reverse flow detection
# ---------------------------------------------------------------------------

def test_rv002_hardening_and_reverse_flow(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="30s", supply={"mode": "replenish", "target": 20})
    with _session(factorio, tmp_path, baseline, scenario) as session:
        session.configure()
        hardened = session.sc(
            'local e = game.surfaces["nauvis"].find_entities_filtered{name="fisl-source-port"}[1] '
            'rcon.print(tostring(e.destructible) .. "," .. tostring(e.minable) .. "," .. tostring(e.operable))'
        ).strip()
        session.start(speed=10.0)
        time.sleep(1.0)
        # Simulate reverse flow: extra tracked material appears in the source.
        session.sc(
            'local e = game.surfaces["nauvis"].find_entities_filtered{name="fisl-source-port"}[1] '
            'e.get_inventory(defines.inventory.chest).insert{name="fisl-rough-workpiece", count=5} '
            'rcon.print("inserted")'
        )
        session.wait_done()
        records = session.telemetry_records()

    assert hardened == "false,false,false", f"apparatus not hardened: {hardened}"
    reverse = [r for r in records if r["type"] == "source_reverse_flow"]
    assert reverse, "reverse insertion was not detected"
    evidence.record(
        "RV-002",
        fixture="hardening probe + scripted reverse insertion",
        expected="port non-destructible/minable/operable; reverse flow detected as protocol event",
        observed=f"flags={hardened}; reverse events={[(r['quantity'], r['interval_end_tick']) for r in reverse]}",
        passed=True,
    )


# ---------------------------------------------------------------------------
# RV-006: craft-progress evidence probe
# ---------------------------------------------------------------------------

def test_rv006_craft_progress_probe(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="60s", supply={"mode": "replenish", "target": 20})
    samples = []
    with _session(factorio, tmp_path, baseline, scenario) as session:
        session.configure()
        session.start(speed=1.0)  # real time so RCON sampling lands on distinct ticks
        for _ in range(40):
            raw = session.sc(
                'local a = game.surfaces["nauvis"].find_entities_filtered{type="assembling-machine"}[1] '
                'rcon.print(game.tick .. "," .. tostring(a.is_crafting()) .. "," '
                '.. tostring(a.crafting_progress) .. "," .. tostring(a.products_finished))'
            ).strip()
            samples.append(raw.split(","))
            time.sleep(0.1)
        session.protocol.request_abort("probe_done")

    finished_counts = [int(s[3]) for s in samples if len(s) == 4]
    progress_values = [float(s[2]) for s in samples if len(s) == 4]
    assert finished_counts[-1] > finished_counts[0], "no crafts completed during probe"
    assert all(0.0 <= p <= 1.0 for p in progress_values)
    assert finished_counts == sorted(finished_counts), "products_finished not monotonic"
    evidence.record(
        "RV-006",
        fixture="40-sample crafting probe at speed 1.0",
        expected="products_finished monotonic; crafting_progress in [0,1]; completions observable",
        observed=(
            f"products_finished {finished_counts[0]} -> {finished_counts[-1]}; "
            f"progress range [{min(progress_values):.3f}, {max(progress_values):.3f}]"
        ),
        passed=True,
        detail={"samples": samples[:40]},
    )


# ---------------------------------------------------------------------------
# RV-011: no silent pause without players; RCON keeps working post-completion
# ---------------------------------------------------------------------------

def test_rv011_headless_no_pause_and_post_completion_rcon(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="10s", supply={"mode": "replenish", "target": 20})
    with _session(factorio, tmp_path, baseline, scenario) as session:
        session.configure()
        session.start(speed=10.0)
        first = session.protocol.get_status()
        time.sleep(1.0)
        second = session.protocol.get_status()
        assert second["map_tick"] > first["map_tick"], "server paused with zero players despite auto_pause=false"
        status = session.wait_done()
        # RCON must remain responsive after COMPLETED (no terminal tick pause).
        after = session.protocol.get_status()
    assert status["lifecycle"] == "COMPLETED"
    assert after["lifecycle"] == "COMPLETED"
    evidence.record(
        "RV-011",
        fixture="headless run with zero connected players",
        expected="ticks advance with no players; RCON responsive after completion",
        observed=f"tick {first['map_tick']} -> {second['map_tick']}; post-completion status ok",
        passed=True,
    )


# ---------------------------------------------------------------------------
# Retry: new run identity, same reproducibility condition
# ---------------------------------------------------------------------------

def test_retry_same_fingerprint_new_run_id(factorio, tmp_path, baseline, evidence, factorio_version):
    from fisl.scenario.canonical import file_sha256
    from fisl.scenario.compiler import resolved_hash
    from fisl.scenario.runconfig import default_run_profile, reproducibility_fingerprint

    scenario = fixture_scenario(warmup="5s", measured="10s", supply={"mode": "replenish", "target": 20})
    run_ids, hashes = [], []
    for attempt in ("a", "b"):
        with _session(factorio, tmp_path / attempt, baseline, scenario) as session:
            session.configure()
            session.start(speed=10.0)
            status = session.wait_done()
            assert status["lifecycle"] == "COMPLETED"
            run_ids.append(session.run_config["run_id"])
            hashes.append(session.run_config["resolved_scenario_hash"])

    assert run_ids[0] != run_ids[1]
    assert hashes[0] == hashes[1]
    profile = default_run_profile("headless")
    fingerprints = [
        reproducibility_fingerprint(
            resolved_scenario_hash=h,
            seed=1,
            baseline_sha256=file_sha256(str(baseline)),
            factorio_version=factorio_version,
            fisl_versions={"compiler": "0.1.0", "fisl-core": "0.1.0"},
            mod_manifest={"fisl-core": "0.1.0", "fisl-factory-physics": "0.1.0"},
            run_profile=profile,
        )
        for h in hashes
    ]
    assert fingerprints[0] == fingerprints[1]
    evidence.record(
        "RV-001",
        fixture="two retries from pristine baseline",
        expected="distinct run ids, identical resolved hash and reproducibility fingerprint",
        observed=f"runs={run_ids}, fingerprint match={fingerprints[0] == fingerprints[1]}",
        passed=True,
    )
