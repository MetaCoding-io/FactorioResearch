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
        "membership_resolution": "dynamic_boundary",
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
        "membership_resolution": "dynamic_boundary",
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


def test_dynamic_membership_eligibility_denominators(tmp_path):
    """ADR 0016 §5-§6: a mid-run joiner contributes no retroactive history,
    a removed machine leaves the denominator at its removal boundary, and the
    pooled denominator is summed eligible machine-ticks — while classification
    coverage still never shrinks it."""
    records = base_records()
    membership = {
        "type": "machine_state_membership",
        "metric": "machine_state",
        "entity_set": "line_machines",
        "adapter": "crafting_machine",
        "classifier_version": "crafting_machine/1",
        "membership_resolution": "dynamic_boundary",
        "machines": [
            {"unit_number": 101, "prototype": "assembling-machine-1", "position": {"x": 0.5, "y": 0.5}},
        ],
    }
    changes_and_spans = [
        membership,
        # m201 built mid-run: eligible [140, 200), productive throughout.
        {"type": "machine_state_membership_change", "metric": "machine_state",
         "change": "added", "unit_number": 201, "prototype": "assembling-machine-1",
         "position": {"x": 8.5, "y": 0.5}, "boundary_tick": 140},
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 201,
         "from_tick": 140, "to_tick": 200, "headline": "productive", "cause": "none",
         "raw_status": "working", "mapped": True},
        # m101 removed at 180: final prepared interval [179,180) is coverage.
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 101,
         "from_tick": 0, "to_tick": 170, "headline": "productive", "cause": "none",
         "raw_status": "working", "mapped": True},
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 101,
         "from_tick": 170, "to_tick": 179, "headline": "starved", "cause": "input_shortage",
         "raw_status": "item_ingredient_shortage", "mapped": True},
        {"type": "machine_state_span", "metric": "machine_state", "unit_number": 101,
         "from_tick": 179, "to_tick": 180, "headline": "coverage_missing", "cause": "unknown",
         "mapped": False},
        {"type": "machine_state_membership_change", "metric": "machine_state",
         "change": "removed", "unit_number": 101, "prototype": "assembling-machine-1",
         "position": {"x": 0.5, "y": 0.5}, "boundary_tick": 180, "eligible_from_tick": 0},
    ]
    records[-1:-1] = changes_and_spans  # before experiment_completed
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(machine_state_resolved(), RUN_CONFIG, path)

    production = summary["metrics"]["machine_state"]
    assert production["machine_count"] == 2
    assert production["eligibility"] == {
        "101": {"from_tick": 0, "to_tick": 180},
        "201": {"from_tick": 140, "to_tick": 200},
    }
    assert production["eligible_machine_ticks"] == 180 + 60
    assert production["per_machine_eligible_ticks"] == {"101": 180, "201": 60}

    # Window [100,200): m101 contributes 80 eligible ticks (removed at 180),
    # m201 contributes 60 (joined at 140) => denominator 140, not 200.
    starved = summary["metrics"]["fraction_starved"]
    assert starved["denominator_machine_ticks"] == 140
    assert starved["per_machine_denominator_ticks"] == {"101": 80, "201": 60}
    assert starved["exact"] == {"numerator": 9, "denominator": 140}
    productive = summary["metrics"]["fraction_productive"]
    # m101 productive in window [100,170) = 70; m201 all 60.
    assert productive["exact"] == {"numerator": 130, "denominator": 140}
    # The one coverage_missing tick shrinks coverage, never the denominator.
    assert productive["classified_machine_ticks"] == 139
    assert productive["coverage_fraction"] == pytest.approx(139 / 140)
    assert productive["coverage_complete"] is False


def test_entry_boundary_throughput_counts_admissions(tmp_path):
    import copy

    resolved = copy.deepcopy(RESOLVED)
    resolved["metrics"]["admission_rate"] = {
        "type": "throughput", "flow": "flow", "boundary": "entry",
        "window": {"phase": "measured", "start_tick": 100, "end_tick": 200},
    }
    records = base_records()
    records[2:2] = [
        {"type": "source_withdrawal", "port": "src", "quantity": 1,
         "interval_start_tick": 49, "interval_end_tick": 50},
        {"type": "source_withdrawal", "port": "src", "quantity": 1,
         "interval_start_tick": 119, "interval_end_tick": 120},
    ]
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(resolved, RUN_CONFIG, path)

    admission = summary["metrics"]["admission_rate"]
    assert admission["method"] == "entry_source_withdrawal"
    # Only the second withdrawal falls inside [100, 200).
    assert admission["completed_quantity"] == 1
    assert admission["value_per_minute"] == pytest.approx(1 * 3600 / 100)
    completion = summary["metrics"]["throughput"]
    assert completion["method"] == "completion_sink_delivery"
    assert completion["completed_quantity"] == 2  # inflow != outflow; ΔWIP explains it


def test_incomplete_run_marks_coverage(tmp_path):
    records = [r for r in base_records() if r["type"] != "experiment_completed"]
    records.append({"type": "experiment_aborted", "reason": "learner_disconnected", "summary": {}})
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(RESOLVED, RUN_CONFIG, path)

    assert summary["validity"]["aborted"] is True
    assert summary["metrics"]["average_wip"]["coverage_complete"] is False
    assert summary["metrics"]["throughput"]["coverage_complete"] is False


def service_resolved() -> dict:
    import copy

    resolved = copy.deepcopy(RESOLVED)
    resolved["metrics"]["customer_service"] = {
        "type": "on_time_item_rate", "demand": "customer_demand", "port": "snk",
        "cohort_window": {"phase": "measured", "start_tick": 100, "end_tick": 200},
        "max_wait_ticks": 30,
        "observation_horizon": {"through_phase": "tail", "end_tick": 230},
    }
    resolved["metrics"]["p90_wait"] = {
        "type": "demand_wait_percentile", "demand": "customer_demand",
        "cohort_window": {"phase": "measured", "start_tick": 100, "end_tick": 200},
        "observation_horizon": {"through_phase": "tail", "end_tick": 230},
        "p": 0.9, "weighting": "demanded_quantity",
        "quantile_method": "weighted_nearest_rank",
    }
    return resolved


def demand_records(final_tick: int) -> list[dict]:
    records = [r for r in base_records() if r["type"] != "experiment_completed"]
    records += [
        # Opening backlog: created BEFORE the cohort window; its fulfillment
        # during the window must not inflate the ratio (ADR 0008 SS8).
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 5, "experiment_tick": 50},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 50, "fulfillment_tick": 120, "quantity": 5},
        # In-window cohorts.
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 10, "experiment_tick": 100},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 100, "fulfillment_tick": 110, "quantity": 8},   # on time (wait 10)
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 100, "fulfillment_tick": 140, "quantity": 2},   # late (wait 40)
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 10, "experiment_tick": 150},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 150, "fulfillment_tick": 170, "quantity": 10},  # on time (wait 20)
        # End-of-window cohort: deadline 220 observed; partial fulfillment.
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 10, "experiment_tick": 190},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 190, "fulfillment_tick": 215, "quantity": 4},   # on time (wait 25)
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 5, "experiment_tick": 199},                          # never fulfilled
        # After the window: excluded from this cohort population entirely.
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 7, "experiment_tick": 205},
    ]
    records.append({"type": "experiment_completed", "experiment_tick": final_tick, "summary": {
        "metrics": {"average_wip": {"area": 120}, "throughput": {"completed_quantity": 2}},
        "demand": {"customer_demand": {"created": 47, "fulfilled": 29, "surplus": 0}},
    }})
    return records


def test_on_time_item_rate_cohort_accounting(tmp_path):
    path = write_telemetry(tmp_path, demand_records(final_tick=230))
    summary = compute_summary(service_resolved(), RUN_CONFIG, path)

    service = summary["metrics"]["customer_service"]
    # Population: cohorts created in [100, 200) only => 10+10+10+5 = 35.
    assert service["total_demand_quantity"] == 35
    assert service["on_time_quantity"] == 22          # 8 + 10 + 4
    assert service["late_fulfilled_quantity"] == 2
    # Deadlines observed passing unfulfilled: outcomes fixed, not censored.
    assert service["outstanding_past_deadline_quantity"] == 11  # 6 + 5
    assert service["unresolved_quantity"] == 0
    assert service["exact"] == {"numerator": 22, "denominator": 35}
    assert service["value"] == pytest.approx(22 / 35)
    assert service["coverage_complete"] is True
    # Lua ledger totals cross-check counts created 47 (incl. out-of-window)
    # and fulfilled 29 (incl. the opening-backlog allocation).
    assert summary["lua_cross_verification"]["agrees"] is True


def test_on_time_rate_censors_unobserved_deadlines(tmp_path):
    # Run ends at 210: cohorts created at 190/199 have deadlines 220/229 —
    # their unfulfilled remainder is CENSORED, never late (ADR 0008 SS10).
    path = write_telemetry(tmp_path, demand_records(final_tick=210))
    summary = compute_summary(service_resolved(), RUN_CONFIG, path)

    service = summary["metrics"]["customer_service"]
    assert service["observed_through_tick"] == 210
    # t=190 allocation at 215 is beyond observation: 10 unresolved there.
    assert service["unresolved_quantity"] == 15  # 10 + 5
    assert service["outstanding_past_deadline_quantity"] == 0
    assert service["on_time_quantity"] == 18     # 8 + 10
    assert service["coverage_complete"] is False


def test_demand_wait_percentile_strict_censoring_and_value(tmp_path):
    path = write_telemetry(tmp_path, demand_records(final_tick=230))
    summary = compute_summary(service_resolved(), RUN_CONFIG, path)
    p90 = summary["metrics"]["p90_wait"]
    # 24 of 35 selected units resolved: percentile is censored, not guessed.
    assert p90["value_seconds"] is None
    assert p90["status"] == "censored"
    assert p90["resolved_quantity"] == 24

    # Fully-resolved population: waits (10 x10), (15 x5), (30 x5);
    # p90 rank = ceil(0.9 * 20) = 18 -> wait 30 ticks = 0.5 s.
    records = [r for r in base_records() if r["type"] != "experiment_completed"]
    records += [
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 10, "experiment_tick": 100},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 100, "fulfillment_tick": 110, "quantity": 10},
        {"type": "demand_created", "demand": "customer_demand", "port": "snk",
         "quantity": 10, "experiment_tick": 150},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 150, "fulfillment_tick": 165, "quantity": 5},
        {"type": "demand_allocation", "demand": "customer_demand", "port": "snk",
         "created_tick": 150, "fulfillment_tick": 180, "quantity": 5},
        {"type": "experiment_completed", "experiment_tick": 230, "summary": {}},
    ]
    path = write_telemetry(tmp_path, records)
    summary = compute_summary(service_resolved(), RUN_CONFIG, path)
    p90 = summary["metrics"]["p90_wait"]
    assert p90["value_ticks"] == 30
    assert p90["value_seconds"] == pytest.approx(0.5)
    assert p90["coverage_complete"] is True
