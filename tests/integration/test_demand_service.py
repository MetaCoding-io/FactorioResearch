"""ADR 0008 demand-cohort fixtures (issue #9): FIFO backlog demand against
a real Factorio runtime, verifying the cohort accounting end-to-end —
demand_created / demand_allocation / surplus_delivery records, on-time item
rate, censoring of the wait percentile, and Lua/Python ledger agreement.

The fixture line's capacity is 15/min (one 4 s machine). Two variants:
demand under capacity (served, with surplus) and demand over capacity
(backlog grows; deadlines observed passing fix the on-time outcome).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fisl.metrics.aggregation import compute_summary
from tests.integration.fixture_world import SpikeSession, create_baseline, fixture_scenario


@pytest.fixture(scope="session")
def baseline(factorio, tmp_path_factory) -> Path:
    workspace = tmp_path_factory.mktemp("ds-baseline")
    return create_baseline(factorio, workspace)


def _run(factorio, tmp_path, baseline, scenario):
    with SpikeSession(factorio, tmp_path / "server", baseline, scenario) as session:
        session.configure()
        session.start(speed=10.0)
        status = session.wait_done()
        assert status["lifecycle"] == "COMPLETED", status
        records = session.telemetry_records()
        summary = compute_summary(session.resolved, session.run_config, session.telemetry_path())
    return session, status, records, summary


def test_demand_under_capacity_serves_on_time(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(
        warmup="5s", measured="60s",
        demand={"rate": "10/min"}, max_wait="10s", service_tail="15s",
    )
    session, status, records, summary = _run(factorio, tmp_path, baseline, scenario)

    created = [r for r in records if r["type"] == "demand_created"]
    allocations = [r for r in records if r["type"] == "demand_allocation"]
    # 10/min over exactly 60 s of measured phase = 10 cohorts of 1.
    assert sum(r["quantity"] for r in created) == 10
    assert all(300 <= r["experiment_tick"] < 3900 for r in created)

    service = summary["metrics"]["customer_service"]
    assert service["total_demand_quantity"] == 10
    assert service["value"] == pytest.approx(1.0), service
    assert service["unresolved_quantity"] == 0
    assert service["coverage_complete"] is True

    # Capacity (15/min) exceeds demand: the excess is surplus, which never
    # credits future cohorts (ADR 0008 §17).
    surplus = sum(r["quantity"] for r in records if r["type"] == "surplus_delivery")
    assert surplus > 0

    p90 = summary["metrics"]["p90_wait"]
    assert p90["coverage_complete"] is True
    assert p90["value_ticks"] is not None and p90["value_ticks"] >= 1

    # FIFO: allocations are non-decreasing in created_tick.
    created_order = [r["created_tick"] for r in allocations]
    assert created_order == sorted(created_order)
    assert summary["lua_cross_verification"]["agrees"], summary["lua_cross_verification"]

    evidence.record(
        "RV-003",
        fixture="demand under capacity (10/min vs 15/min)",
        expected="all cohorts served on time; surplus recorded, never credited forward; FIFO allocation order",
        observed=(
            f"on_time={service['on_time_quantity']}/{service['total_demand_quantity']}, "
            f"surplus={surplus}, p90_wait={p90['value_ticks']} ticks"
        ),
        passed=True,
    )


def test_demand_over_capacity_fixes_missed_deadlines(factorio, tmp_path, baseline, evidence):
    scenario = fixture_scenario(
        warmup="5s", measured="60s",
        demand={"rate": "40/min"}, max_wait="10s", service_tail="15s",
    )
    session, status, records, summary = _run(factorio, tmp_path, baseline, scenario)

    service = summary["metrics"]["customer_service"]
    # 40/min demanded for 60 s = 40; capacity delivers ~15/min.
    assert service["total_demand_quantity"] == 40
    assert service["value"] is not None and service["value"] < 1.0
    # Every selected deadline was observable (compiler property), so nothing
    # is censored: unserved quantity is outstanding-past-deadline, not
    # unresolved (ADR 0008 §10-§11).
    assert service["unresolved_quantity"] == 0
    assert service["outstanding_past_deadline_quantity"] > 0
    assert service["coverage_complete"] is True

    # The wait percentile IS censored: unfulfilled demand has no wait.
    p90 = summary["metrics"]["p90_wait"]
    assert p90["value_seconds"] is None
    assert p90["status"] == "censored"

    lua_demand = summary and [r for r in records if r["type"] == "experiment_completed"][0][
        "summary"
    ]["demand"]["customer_demand"]
    assert lua_demand["backlog"] > 0
    assert summary["lua_cross_verification"]["agrees"], summary["lua_cross_verification"]

    evidence.record(
        "RV-003",
        fixture="demand over capacity (40/min vs 15/min)",
        expected="backlog grows; missed deadlines fixed as not-on-time (never censored); wait percentile censored honestly",
        observed=(
            f"on_time={service['on_time_quantity']}/{service['total_demand_quantity']}, "
            f"outstanding={service['outstanding_past_deadline_quantity']}, backlog={lua_demand['backlog']}"
        ),
        passed=True,
    )
