"""Golden tests for the authoritative Python recomputation (PRD §29.4):
exact ledger trajectory, tick-weighted WIP integration, completion
throughput, Little's-Law-derived cycle time, and census validity flagging.
"""

import json
from pathlib import Path

import pytest

from fisl.metrics.aggregation import compute_summary

RESOLVED = {
    "scenario": {"id": "fixture", "version": "0.0.1", "title": "fixture"},
    "flows": {
        "flow": {
            "system": "factory",
            "unit": "workpiece",
            "basis": {"type": "conserved_work_unit", "materials": {"rough": 1, "finished": 1}},
            "entry_ports": ["src"],
            "completion_ports": ["snk"],
            "loss_ports": [],
        }
    },
    "ports": {
        "src": {"direction": "source", "material": {"item": "rough"}},
        "snk": {"direction": "sink", "material": {"item": "finished"}},
    },
    "metrics": {
        "line_wip": {"type": "wip", "flow": "flow"},
        "average_wip": {
            "type": "aggregate", "source": "line_wip", "aggregation": "time_mean",
            "window": {"phase": "measured", "start_tick": 100, "end_tick": 200},
        },
        "throughput": {
            "type": "throughput", "flow": "flow",
            "window": {"phase": "measured", "start_tick": 100, "end_tick": 200},
        },
        "cycle_time": {
            "type": "cycle_time", "flow": "flow", "method": "little_law_derived",
            "wip_metric": "average_wip", "throughput_metric": "throughput",
        },
    },
}

RUN_CONFIG = {"run_id": "TESTRUN", "resolved_scenario_hash": "sha256:x"}


def write_telemetry(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "telemetry.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return path


def base_records() -> list[dict]:
    records = [
        {"type": "stream_header", "run_id": "TESTRUN"},
        {"type": "initial_census", "flow": "flow", "wip": 0},
    ]
    # Admissions: 1 unit at boundaries 50 and 120; completions at 150 and 190.
    records += [
        {"type": "ledger_transaction", "flow": "flow", "admitted": 1, "completed": 0,
         "interval_start_tick": 49, "interval_end_tick": 50},
        {"type": "ledger_transaction", "flow": "flow", "admitted": 1, "completed": 0,
         "interval_start_tick": 119, "interval_end_tick": 120},
        {"type": "sink_delivery", "port": "snk", "quantity": 1,
         "interval_start_tick": 149, "interval_end_tick": 150},
        {"type": "ledger_transaction", "flow": "flow", "admitted": 0, "completed": 1,
         "interval_start_tick": 149, "interval_end_tick": 150},
        {"type": "sink_delivery", "port": "snk", "quantity": 1,
         "interval_start_tick": 189, "interval_end_tick": 190},
        {"type": "ledger_transaction", "flow": "flow", "admitted": 0, "completed": 1,
         "interval_start_tick": 189, "interval_end_tick": 190},
        {"type": "experiment_completed", "experiment_tick": 200, "summary": {
            "metrics": {
                "average_wip": {"area": 130},
                "throughput": {"completed_quantity": 2},
            }
        }},
    ]
    return records


def test_exact_wip_integration_and_littles_law(tmp_path):
    path = write_telemetry(tmp_path, base_records())
    summary = compute_summary(RESOLVED, RUN_CONFIG, path)

    # WIP trajectory: 1 from tick 50, 2 from 120, 1 from 150, 0 from 190.
    # Window [100,200): WIP=1 on [100,120) => 20; 2 on [120,150) => 60;
    # 1 on [150,190) => 40; 0 on [190,200) => 0. Area = 120... check: 20+60+40 = 120.
    average = summary["metrics"]["average_wip"]
    assert average["exact"] == {"numerator": 120, "denominator": 100}
    assert average["value"] == pytest.approx(1.2)
    assert average["coverage_complete"] is True

    throughput = summary["metrics"]["throughput"]
    assert throughput["completed_quantity"] == 2
    assert throughput["value_per_minute"] == pytest.approx(2 * 3600 / 100)

    cycle = summary["metrics"]["cycle_time"]
    assert cycle["method"] == "little_law_derived"
    assert cycle["measurement_class"] == "derived"
    # CT = area / completed = 120/2 = 60 ticks = 1 s.
    assert cycle["exact_ticks"] == {"numerator": 60, "denominator": 1}
    assert cycle["value_seconds"] == pytest.approx(1.0)

    # Lua cross-verification disagrees on purpose (lua reported area=130).
    verification = summary["lua_cross_verification"]
    assert verification["available"] is True
    assert verification["agrees"] is False


def test_census_discrepancy_flags_overlapping_window(tmp_path):
    records = base_records()
    records[-1]["summary"]["metrics"]["average_wip"]["area"] = 120  # agree now
    records.insert(-1, {
        "type": "wip_census", "metric": "line_wip", "flow": "flow",
        "experiment_tick": 120, "ledger_wip": 2, "census_wip": 2, "discrepancy": 0,
    })
    records.insert(-1, {
        "type": "wip_census_discrepancy", "metric": "line_wip", "flow": "flow",
        "experiment_tick": 180, "discrepancy": -1,
        "suspect_from_tick": 120, "suspect_to_tick": 180,
    })
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(RESOLVED, RUN_CONFIG, path)

    validity = summary["metrics"]["average_wip"]["census_validity"]
    assert validity["valid"] is False
    assert validity["discrepancy_intervals"] == [
        {"from_tick": 120, "to_tick": 180, "discrepancy": -1}
    ]
    assert summary["lua_cross_verification"]["agrees"] is True


def test_incomplete_run_marks_coverage(tmp_path):
    records = [r for r in base_records() if r["type"] != "experiment_completed"]
    records.append({"type": "experiment_aborted", "reason": "learner_disconnected", "summary": {}})
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(RESOLVED, RUN_CONFIG, path)

    assert summary["validity"]["aborted"] is True
    assert summary["metrics"]["average_wip"]["coverage_complete"] is False
    assert summary["metrics"]["throughput"]["coverage_complete"] is False
