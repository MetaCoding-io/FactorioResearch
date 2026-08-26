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


def machine_state_resolved() -> dict:
    import copy

    resolved = copy.deepcopy(RESOLVED)
    resolved["metrics"]["machine_state"] = {
        "type": "production_state",
        "entities": "line_machines",
        "adapter": "crafting_machine",
        "activity": {"method": "craft_progress_delta", "cadence": "1tick"},
        "classification": {"profile": "factory_physics_v1"},
        "membership_resolution": "static_at_ready",
    }
    for state in ("productive", "starved"):
        resolved["metrics"][f"fraction_{state}"] = {
            "type": "state_fraction",
            "source": "machine_state",
            "state": state,
            "entity_aggregation": "pooled_machine_time",
            "denominator": "full_window",
            "window": {"phase": "measured", "start_tick": 100, "end_tick": 200},
        }
    return resolved


def machine_state_records() -> list[dict]:
    records = base_records()
    membership = {
        "type": "machine_state_membership",
        "metric": "machine_state",
        "entity_set": "line_machines",
        "adapter": "crafting_machine",
        "classifier_version": "crafting_machine/1",
        "membership_resolution": "static_at_ready",
        "machines": [
            {"unit_number": 101, "prototype": "assembling-machine-1", "position": {"x": 0.5, "y": 0.5}},
            {"unit_number": 102, "prototype": "assembling-machine-1", "position": {"x": 8.5, "y": 0.5}},
        ],
    }
    spans = [
        # m101: productive [0,160), starved [160,200)
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 101,
         "from_tick": 0, "to_tick": 160, "headline": "productive", "cause": "none",
         "raw_status": "working", "mapped": True},
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 101,
         "from_tick": 160, "to_tick": 200, "headline": "starved", "cause": "input_shortage",
         "raw_status": "item_ingredient_shortage", "mapped": True},
        # m102: productive [0,140), missing [140,150), blocked [150,200)
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 102,
         "from_tick": 0, "to_tick": 140, "headline": "productive", "cause": "none",
         "raw_status": "working", "mapped": True},
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 102,
         "from_tick": 140, "to_tick": 150, "headline": "coverage_missing", "cause": "unknown",
         "raw_status": None, "mapped": False},
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 102,
         "from_tick": 150, "to_tick": 200, "headline": "blocked", "cause": "output_blocked",
         "raw_status": "full_output", "mapped": True},
    ]
    records[-1:-1] = [membership] + spans  # before experiment_completed
    records[-1]["summary"]["machine_state"] = {
        "machine_state": {
            "pooled_state_ticks": {"productive": 300, "starved": 40, "blocked": 50},
            "coverage_missing_ticks": 10,
        }
    }
    return records


def test_state_fractions_full_window_denominator_and_coverage(tmp_path):
    path = write_telemetry(tmp_path, machine_state_records())
    summary = compute_summary(machine_state_resolved(), RUN_CONFIG, path)

    production = summary["metrics"]["machine_state"]
    assert production["machine_count"] == 2
    assert production["pooled_state_ticks"] == {
        "productive": 300, "starved": 40, "blocked": 50, "coverage_missing": 10,
    }
    assert production["classified_machine_ticks"] == 390
    assert production["classifier_version"] == "crafting_machine/1"

    # Window [100,200): m101 productive 60 + m102 productive 40 = 100 of the
    # full 2x100 machine-tick denominator; the 10 missing ticks reduce
    # coverage, never the denominator.
    productive = summary["metrics"]["fraction_productive"]
    assert productive["denominator_machine_ticks"] == 200
    assert productive["exact"] == {"numerator": 100, "denominator": 200}
    assert productive["value"] == pytest.approx(0.5)
    assert productive["coverage_fraction"] == pytest.approx(190 / 200)
    assert productive["coverage_complete"] is False

    starved = summary["metrics"]["fraction_starved"]
    assert starved["exact"] == {"numerator": 40, "denominator": 200}

    # Lua streaming accumulators agree with the span recomputation.
    verification = summary["lua_cross_verification"]
    assert not any("machine_state" in m for m in verification["mismatches"])


def test_lua_machine_state_mismatch_is_flagged(tmp_path):
    records = machine_state_records()
    records[-1]["summary"]["machine_state"]["machine_state"]["pooled_state_ticks"]["productive"] = 299
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(machine_state_resolved(), RUN_CONFIG, path)
    assert any("machine_state" in m for m in summary["lua_cross_verification"]["mismatches"])


def test_incomplete_run_marks_coverage(tmp_path):
    records = [r for r in base_records() if r["type"] != "experiment_completed"]
    records.append({"type": "experiment_aborted", "reason": "learner_disconnected", "summary": {}})
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(RESOLVED, RUN_CONFIG, path)

    assert summary["validity"]["aborted"] is True
    assert summary["metrics"]["average_wip"]["coverage_complete"] is False
    assert summary["metrics"]["throughput"]["coverage_complete"] is False
