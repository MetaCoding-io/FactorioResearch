"""ADR 0007 §25 classifier fixtures (issue #7): force the fixture line's
assembler into each supported state against a real Factorio runtime and
verify raw + classified output end-to-end (spans in telemetry, pooled state
fractions in the Python summary, Lua/Python cross-check).

Each world mutation happens BEFORE session.configure(): production-state
membership resolves statically at READY (interim until issue #8), and READY
validation runs inside configure's commit.

Evidence: RV-006 (interval activity across craft completion) and RV-007
(brownout keeps productive + energy_limited when progress is observed).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fisl.metrics.aggregation import compute_summary
from tests.integration.fixture_world import SpikeSession, create_baseline, fixture_scenario


@pytest.fixture(scope="session")
def baseline(factorio, tmp_path_factory) -> Path:
    workspace = tmp_path_factory.mktemp("ms-baseline")
    return create_baseline(factorio, workspace)


def _session(factorio, tmp_path, baseline, scenario) -> SpikeSession:
    return SpikeSession(factorio, tmp_path / "server", baseline, scenario)


def _run(session: SpikeSession, pre_configure_lua: str | None = None) -> tuple[dict, list[dict], dict]:
    if pre_configure_lua:
        response = session.sc(pre_configure_lua.replace("\n", " "))
        assert "fixture-ok" in response, f"fixture mutation failed: {response!r}"
    session.configure()
    session.start(speed=10.0)
    status = session.wait_done()
    assert status["lifecycle"] == "COMPLETED", status
    records = session.telemetry_records()
    summary = compute_summary(session.resolved, session.run_config, session.telemetry_path())
    return status, records, summary


def _spans(records: list[dict]) -> list[dict]:
    return [r for r in records if r["type"] == "machine_state_span"]


def _membership(records: list[dict]) -> dict:
    matches = [r for r in records if r["type"] == "machine_state_membership"]
    assert len(matches) == 1
    return matches[0]


def _assert_span_partition(records: list[dict], total_ticks: int) -> None:
    """Per machine: spans are half-open, adjacent, and cover [0, total)."""
    by_machine: dict[int, list[dict]] = {}
    for span in _spans(records):
        by_machine.setdefault(span["unit_number"], []).append(span)
    assert by_machine, "no machine_state_span records emitted"
    for spans in by_machine.values():
        spans.sort(key=lambda s: s["from_tick"])
        assert spans[0]["from_tick"] == 0
        assert spans[-1]["to_tick"] == total_ticks
        for left, right in zip(spans, spans[1:]):
            assert left["to_tick"] == right["from_tick"], (left, right)


def _pooled(summary: dict) -> dict:
    return summary["metrics"]["machine_state"]["pooled_state_ticks"]


def test_productive_then_starved_and_completion_wrap(factorio, tmp_path, baseline, evidence):
    # Supply replenishes only during warmup; the measured phase drains the
    # source and the machine ends up input-starved.
    scenario = fixture_scenario(
        warmup="10s",
        measured="60s",
        supply={"mode": "replenish", "target": 8, "active_phases": ["warmup"]},
        machine_state=True,
    )
    with _session(factorio, tmp_path, baseline, scenario) as session:
        status, records, summary = _run(session)

    total = session.resolved["experiment"]["total_duration_ticks"]
    membership = _membership(records)
    assert membership["membership_resolution"] == "static_at_ready"
    assert len(membership["machines"]) == 1  # the port apparatus is excluded
    _assert_span_partition(records, total)

    pooled = _pooled(summary)
    # The machine crafts several 4-second workpieces (multiple completion
    # wraps) with zero unknown gaps, then starves when the line drains.
    assert pooled.get("productive", 0) > 0
    assert pooled.get("starved", 0) > 0
    assert "unclassified" not in pooled
    assert "coverage_missing" not in pooled
    starved_spans = [s for s in _spans(records) if s["headline"] == "starved"]
    assert all(s["cause"] == "input_shortage" for s in starved_spans)

    fraction = summary["metrics"]["fraction_starved"]
    assert fraction["denominator_machine_ticks"] == 36000  # 1 machine x 60 s
    assert fraction["coverage_fraction"] == pytest.approx(1.0)
    assert summary["lua_cross_verification"]["agrees"], summary["lua_cross_verification"]

    evidence.record(
        "RV-006",
        fixture="machine-state productive->starved run",
        expected="progress-based activity spans multiple craft completions without unknown gaps; drain ends in starved/input_shortage",
        observed=f"pooled={pooled}, spans={len(_spans(records))}",
        passed=True,
    )


def test_blocked_when_output_cannot_discharge(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="30s", machine_state=True)
    remove_output_inserter = """
    local surface = game.surfaces["nauvis"]
    local found = surface.find_entities_filtered{name = "fast-inserter", position = {2.5, 0.5}, radius = 0.2}
    for _, entity in pairs(found) do entity.destroy() end
    rcon.print("fixture-ok")
    """
    with _session(factorio, tmp_path, baseline, scenario) as session:
        status, records, summary = _run(session, remove_output_inserter)

    pooled = _pooled(summary)
    assert pooled.get("blocked", 0) > 0, pooled
    blocked_spans = [s for s in _spans(records) if s["headline"] == "blocked"]
    assert all(s["cause"] == "output_blocked" for s in blocked_spans)
    evidence.record(
        "RV-006",
        fixture="machine-state blocked fixture (output inserter removed)",
        expected="full output buffer classifies as blocked/output_blocked",
        observed=f"pooled={pooled}, raw={sorted({s.get('raw_status') for s in blocked_spans})}",
        passed=True,
    )


def test_unavailable_without_power(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="30s", machine_state=True)
    kill_power = """
    local surface = game.surfaces["nauvis"]
    for _, eei in pairs(surface.find_entities_filtered{name = "electric-energy-interface"}) do
      eei.power_production = 0
      eei.electric_buffer_size = 0
    end
    rcon.print("fixture-ok")
    """
    with _session(factorio, tmp_path, baseline, scenario) as session:
        status, records, summary = _run(session, kill_power)

    pooled = _pooled(summary)
    assert pooled.get("unavailable", 0) > 0, pooled
    assert pooled.get("productive", 0) == 0
    unavailable_spans = [s for s in _spans(records) if s["headline"] == "unavailable"]
    assert all(s["cause"] in ("energy_unavailable", "energy_limited") for s in unavailable_spans)
    evidence.record(
        "RV-006",
        fixture="machine-state no-power fixture",
        expected="zero progress with no_power classifies unavailable/energy_unavailable",
        observed=f"pooled={pooled}, raw={sorted({s.get('raw_status') for s in unavailable_spans})}",
        passed=True,
    )


def test_disabled_by_script_is_disabled_not_unavailable(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="30s", machine_state=True)
    disable_machine = """
    local surface = game.surfaces["nauvis"]
    for _, asm in pairs(surface.find_entities_filtered{type = "assembling-machine"}) do
      asm.active = false
    end
    rcon.print("fixture-ok")
    """
    with _session(factorio, tmp_path, baseline, scenario) as session:
        status, records, summary = _run(session, disable_machine)

    pooled = _pooled(summary)
    assert pooled.get("disabled", 0) > 0, pooled
    disabled_spans = [s for s in _spans(records) if s["headline"] == "disabled"]
    assert all(s["cause"] == "disabled_control" for s in disabled_spans)
    evidence.record(
        "RV-006",
        fixture="machine-state disabled fixture (active=false)",
        expected="script disablement classifies disabled/disabled_control, distinct from unavailable",
        observed=f"pooled={pooled}, raw={sorted({s.get('raw_status') for s in disabled_spans})}",
        passed=True,
    )


def test_no_recipe_machine_is_idle_other(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="30s", machine_state=True)
    add_bare_machine = """
    local surface = game.surfaces["nauvis"]
    surface.create_entity{name = "assembling-machine-1", position = {0.5, 5.5}, force = "player", raise_built = false}
    rcon.print("fixture-ok")
    """
    with _session(factorio, tmp_path, baseline, scenario) as session:
        status, records, summary = _run(session, add_bare_machine)

    membership = _membership(records)
    assert len(membership["machines"]) == 2
    per_machine = summary["metrics"]["machine_state"]["per_machine_state_ticks"]
    idle_machines = [u for u, states in per_machine.items() if states.get("idle_other", 0) > 0]
    assert idle_machines, per_machine
    idle_spans = [s for s in _spans(records) if s["headline"] == "idle_other"]
    assert all(s["cause"] == "configuration" for s in idle_spans)
    evidence.record(
        "RV-006",
        fixture="machine-state no-recipe fixture (second bare assembler)",
        expected="recipe-less machine classifies idle_other/configuration; per-machine identity retained",
        observed=f"idle machines={idle_machines}, raw={sorted({s.get('raw_status') for s in idle_spans})}",
        passed=True,
    )


def test_rv007_brownout_stays_productive_with_energy_limited(factorio, tmp_path, baseline, evidence):
    """RV-007: undersized generation slows the machine instead of stopping
    it; observed craft progress must keep the headline productive while the
    energy_limited condition is preserved. The power level below may need
    tuning against the real runtime — the evidence record captures the
    observed state distribution either way."""
    scenario = fixture_scenario(warmup="10s", measured="60s", machine_state=True)
    brownout = """
    local surface = game.surfaces["nauvis"]
    for _, eei in pairs(surface.find_entities_filtered{name = "electric-energy-interface"}) do
      eei.power_production = 700
      eei.electric_buffer_size = 700
    end
    rcon.print("fixture-ok")
    """
    with _session(factorio, tmp_path, baseline, scenario) as session:
        status, records, summary = _run(session, brownout)

    spans = _spans(records)
    productive_limited = [
        s for s in spans if s["headline"] == "productive" and s["cause"] == "energy_limited"
    ]
    pooled = _pooled(summary)
    observed = {
        "pooled": pooled,
        "productive_energy_limited_spans": len(productive_limited),
        "raw_statuses": sorted({s.get("raw_status") for s in spans if s.get("raw_status")}),
    }
    assert productive_limited, observed
    assert all(s.get("raw_status") == "low_power" for s in productive_limited)
    evidence.record(
        "RV-007",
        fixture="machine-state brownout fixture (EEI at ~700 J/tick)",
        expected="reduced-power crafting classifies productive + energy_limited (low_power), not unavailable",
        observed=str(observed),
        passed=True,
    )
