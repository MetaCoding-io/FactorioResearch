"""RV-012 (ADR 0016): dynamic entity-set membership against a real runtime.

One machine runs the fixture line for the whole experiment; a second
matching machine is BUILT mid-run (script_raised_built -> membership add at
the next checkpoint boundary) and later DESTROYED (validity-driven removal).
Asserts the eligibility intervals: no retroactive history before the join,
no denominator contribution after the removal, and eligibility-aware pooled
state-fraction denominators.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from fisl.metrics.aggregation import compute_summary
from tests.integration.fixture_world import SpikeSession, create_baseline, fixture_scenario


@pytest.fixture(scope="session")
def baseline(factorio, tmp_path_factory) -> Path:
    workspace = tmp_path_factory.mktemp("dm-baseline")
    return create_baseline(factorio, workspace)


def _wait_for_tick(session: SpikeSession, experiment_tick: int, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = session.protocol.get_status()
        if status.get("lifecycle") != "RUNNING":
            raise AssertionError(f"run ended early: {status}")
        if (status.get("experiment_tick") or 0) >= experiment_tick:
            return
        time.sleep(0.2)
    raise TimeoutError(f"experiment_tick {experiment_tick} not reached")


BUILD_MACHINE = (
    'local surface = game.surfaces["nauvis"] '
    'local asm = surface.create_entity{name = "assembling-machine-1", position = {0.5, 5.5}, '
    'force = "player", raise_built = true} '
    'asm.set_recipe("fisl-machine-workpiece") '
    'rcon.print("built:" .. asm.unit_number)'
)

DESTROY_MACHINE = (
    'local surface = game.surfaces["nauvis"] '
    'for _, e in pairs(surface.find_entities_filtered{type = "assembling-machine", '
    'area = {{-2, 4}, {2, 7}}}) do e.destroy() end '
    'rcon.print("destroyed-ok")'
)


def test_rv012_membership_add_and_remove_mid_run(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(warmup="5s", measured="60s", machine_state=True)
    with SpikeSession(factorio, tmp_path / "server", baseline, scenario) as session:
        session.configure()
        session.start(speed=10.0)

        _wait_for_tick(session, 900)
        response = session.sc(BUILD_MACHINE)
        assert "built:" in response, response
        built_unit = int(response.split("built:")[1].split()[0])

        _wait_for_tick(session, 2400)
        response = session.sc(DESTROY_MACHINE)
        assert "destroyed-ok" in response, response

        status = session.wait_done()
        assert status["lifecycle"] == "COMPLETED", status
        records = session.telemetry_records()
        summary = compute_summary(session.resolved, session.run_config, session.telemetry_path())

    total = session.resolved["experiment"]["total_duration_ticks"]
    changes = [r for r in records if r["type"] == "machine_state_membership_change"]
    added = [r for r in changes if r["change"] == "added"]
    removed = [r for r in changes if r["change"] == "removed"]
    assert [r["unit_number"] for r in added] == [built_unit], changes
    assert [r["unit_number"] for r in removed] == [built_unit], changes
    join_tick = added[0]["boundary_tick"]
    leave_tick = removed[0]["boundary_tick"]
    assert 900 <= join_tick < leave_tick <= total
    assert removed[0]["eligible_from_tick"] == join_tick

    # No retroactive history; spans exactly partition eligibility [join, leave).
    spans = [r for r in records if r["type"] == "machine_state_span" and r["unit_number"] == built_unit]
    spans.sort(key=lambda s: s["from_tick"])
    assert spans[0]["from_tick"] == join_tick
    assert spans[-1]["to_tick"] == leave_tick
    for left, right in zip(spans, spans[1:]):
        assert left["to_tick"] == right["from_tick"], (left, right)
    # Fed nothing, the machine should be starved nearly all of its life; only
    # its final prepared interval (entity destroyed) is missing coverage.
    joined_states = {s["headline"] for s in spans}
    assert "starved" in joined_states, spans
    coverage_ticks = sum(
        s["to_tick"] - s["from_tick"] for s in spans if s["headline"] == "coverage_missing"
    )
    assert coverage_ticks <= 2, spans

    production = summary["metrics"]["machine_state"]
    assert production["membership_resolution"] == "dynamic_boundary"
    assert production["machine_count"] == 2
    eligibility = production["eligibility"][str(built_unit)]
    assert eligibility == {"from_tick": join_tick, "to_tick": leave_tick}

    # Eligibility-aware pooled denominator (ADR 0016 §5): the joiner
    # contributes exactly leave-join machine-ticks to the measured window,
    # the resident machine the full window.
    window = summary["metrics"]["fraction_starved"]["window"]
    starved = summary["metrics"]["fraction_starved"]
    resident_ticks = window["end_tick"] - window["start_tick"]
    assert starved["per_machine_denominator_ticks"][str(built_unit)] == leave_tick - join_tick
    assert starved["denominator_machine_ticks"] == resident_ticks + (leave_tick - join_tick)
    assert summary["lua_cross_verification"]["agrees"], summary["lua_cross_verification"]

    evidence.record(
        "RV-012",
        fixture="dynamic membership: build + destroy a matching assembler mid-run",
        expected="membership add at the drain boundary, validity-driven removal; eligibility intervals bound spans and pooled denominators (no retroactive history, no stale denominator)",
        observed=(
            f"joined={join_tick}, left={leave_tick}, spans={[(s['from_tick'], s['to_tick'], s['headline']) for s in spans]}, "
            f"denominator={starved['denominator_machine_ticks']}"
        ),
        passed=True,
    )
