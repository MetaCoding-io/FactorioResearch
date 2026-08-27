import copy
from pathlib import Path

import pytest
import yaml

from fisl.scenario.compiler import (
    CompilationError,
    compile_author_scenario,
    load_author_yaml,
    resolved_hash,
)

SCENARIO_YAML = (
    Path(__file__).resolve().parents[2]
    / "scenarios/factory-physics/fp03-littles-law/scenario.yaml"
)


@pytest.fixture()
def author():
    return load_author_yaml(SCENARIO_YAML)


@pytest.fixture()
def raw():
    return yaml.safe_load(SCENARIO_YAML.read_text())


def _compile_raw(raw_doc):
    from fisl.scenario.compiler import validate_author_dict

    return compile_author_scenario(validate_author_dict(raw_doc))


def test_reference_scenario_compiles(author):
    resolved = compile_author_scenario(author)
    phases = resolved["experiment"]["phases"]
    assert phases[0] == {"id": "warmup", "duration_ticks": 7200, "start_tick": 0, "end_tick": 7200}
    assert phases[1]["start_tick"] == 7200
    assert phases[1]["end_tick"] == 7200 + 36000
    assert resolved["experiment"]["total_duration_ticks"] == 43200
    window = resolved["metrics"]["average_wip"]["window"]
    assert (window["start_tick"], window["end_tick"]) == (7200, 43200)
    assert resolved["metrics"]["line_wip"]["validation"]["physical_census"]["every_ticks"] == 60
    assert resolved["observation_plan"]["ledgers"] == [{"metric": "line_wip", "flow": "workpiece_flow"}]


def test_resolved_hash_is_stable_and_run_independent(author):
    first = compile_author_scenario(author)
    second = compile_author_scenario(load_author_yaml(SCENARIO_YAML))
    assert resolved_hash(first) == resolved_hash(second)
    assert "run_id" not in str(first)
    # actual execution seed is not part of the resolved document; only the
    # authoring default travels with scenario semantics
    assert first["experiment"]["default_seed"] == 1


def test_learning_metadata_excluded_from_resolved_identity(raw):
    modified = copy.deepcopy(raw)
    modified["learning"]["concepts"].append("an extra prose concept")
    assert resolved_hash(_compile_raw(raw)) == resolved_hash(_compile_raw(modified))


def test_unknown_field_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["metrics"]["line_wip"]["typo_field"] = True
    with pytest.raises(CompilationError):
        _compile_raw(bad)


def test_unknown_phase_reference_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["metrics"]["average_wip"]["window"]["phase"] = "nonexistent"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("unknown phase" in p for p in exc.value.problems)


def test_littles_law_window_mismatch_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["metrics"]["warmup_throughput"] = {
        "type": "throughput",
        "flow": "workpiece_flow",
        "window": {"phase": "warmup"},
    }
    bad["metrics"]["loaded_cycle_time"]["throughput_metric"] = "warmup_throughput"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("different windows" in p for p in exc.value.problems)


def test_flow_port_direction_mismatch_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["flows"]["workpiece_flow"]["completion_ports"] = ["workpiece_source"]
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("direction" in p for p in exc.value.problems)


def test_flow_material_must_map_to_basis(raw):
    bad = copy.deepcopy(raw)
    del bad["flows"]["workpiece_flow"]["basis"]["materials"]["fisl-finished-workpiece"]
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("no work-unit mapping" in p for p in exc.value.problems)


def test_pause_policy_allowed_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["experiment"]["time"]["pause_policy"] = "allowed"
    with pytest.raises(CompilationError):
        _compile_raw(bad)


def test_visibility_unknown_metric_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["visibility"]["learner_live"]["metrics"].append("ghost_metric")
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("ghost_metric" in p for p in exc.value.problems)


# --- machine-state metrics (ADR 0007, issue #7) -----------------------------

# The resolved hash committed with the first verified baseline run. Machine-
# state support must not disturb the identity of scenarios that don't use it
# — existing runs stay comparable.
FP03_COMMITTED_HASH = "sha256:4fafdd4cb4607338b4888b8b6b535f4ebd1f39f0d52b0b726ccc7c71183938f4"


def test_fp03_resolved_hash_unchanged_by_machine_state_support(author):
    resolved = compile_author_scenario(author)
    assert resolved_hash(resolved) == FP03_COMMITTED_HASH
    assert "machine_state" not in resolved["observation_plan"]


def _with_machine_state(raw_doc):
    doc = copy.deepcopy(raw_doc)
    doc["metrics"]["machine_state"] = {
        "type": "production_state",
        "entities": "line_machines",
        "adapter": "crafting_machine",
    }
    doc["metrics"]["fraction_starved"] = {
        "type": "state_fraction",
        "source": "machine_state",
        "state": "starved",
        "entity_aggregation": "pooled_machine_time",
        "denominator": "full_window",
        "window": {"phase": "measured"},
    }
    return doc


def test_machine_state_metrics_compile(raw):
    resolved = _compile_raw(_with_machine_state(raw))
    production = resolved["metrics"]["machine_state"]
    assert production["adapter"] == "crafting_machine"
    assert production["activity"] == {"method": "craft_progress_delta", "cadence": "1tick"}
    assert production["classification"] == {"profile": "factory_physics_v1"}
    assert production["membership_resolution"] == "dynamic_boundary"
    fraction = resolved["metrics"]["fraction_starved"]
    assert fraction["denominator"] == "full_window"
    assert (fraction["window"]["start_tick"], fraction["window"]["end_tick"]) == (7200, 43200)
    plan = resolved["observation_plan"]["machine_state"]
    assert plan == [
        {
            "metric": "machine_state",
            "entity_set": "line_machines",
            "adapter": "crafting_machine",
            "activity_method": "craft_progress_delta",
            "cadence": "1tick",
            "classification_profile": "factory_physics_v1",
            "membership_resolution": "dynamic_boundary",
        }
    ]


def test_production_state_unknown_entity_set_rejected(raw):
    bad = _with_machine_state(raw)
    bad["metrics"]["machine_state"]["entities"] = "ghost_set"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("ghost_set" in p for p in exc.value.problems)


def test_state_fraction_source_must_be_production_state(raw):
    bad = _with_machine_state(raw)
    bad["metrics"]["fraction_starved"]["source"] = "line_wip"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("must be a production_state metric" in p for p in exc.value.problems)


def test_state_fraction_rejects_coverage_missing_as_state(raw):
    # coverage_missing is missing measurement, never a requestable state
    # (ADR 0007 §24) — the schema literal refuses it.
    bad = _with_machine_state(raw)
    bad["metrics"]["fraction_starved"]["state"] = "coverage_missing"
    with pytest.raises(CompilationError):
        _compile_raw(bad)


FP04_COMMITTED_HASH = "sha256:98f6d0b46f3b464d1c94e13922576db636fc0b1afaff6b9fd7ebd6c7bb118dc7"


def test_all_committed_scenarios_compile():
    for scenario_yaml in sorted(SCENARIO_YAML.parent.parent.glob("*/scenario.yaml")):
        resolved = compile_author_scenario(load_author_yaml(scenario_yaml))
        assert resolved["experiment"]["total_duration_ticks"] > 0, scenario_yaml


def test_fp04_resolved_hash_matches_committed_verification():
    fp04_yaml = SCENARIO_YAML.parent.parent / "fp04-starvation-blocking" / "scenario.yaml"
    resolved = compile_author_scenario(load_author_yaml(fp04_yaml))
    assert resolved_hash(resolved) == FP04_COMMITTED_HASH


def test_entry_boundary_throughput_compiles(raw):
    doc = copy.deepcopy(raw)
    doc["metrics"]["admission_rate"] = {
        "type": "throughput",
        "flow": "workpiece_flow",
        "boundary": "entry",
        "window": {"phase": "measured"},
    }
    resolved = _compile_raw(doc)
    assert resolved["metrics"]["admission_rate"]["boundary"] == "entry"
    # Default completion boundary stays keyless so existing hashes hold.
    assert "boundary" not in resolved["metrics"]["measured_throughput"]


def test_littles_law_rejects_entry_boundary_throughput(raw):
    bad = copy.deepcopy(raw)
    bad["metrics"]["measured_throughput"]["boundary"] = "entry"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("completion boundary" in p for p in exc.value.problems)


def test_fp04_scenario_compiles_with_machine_state_stack(raw):
    fp04_yaml = SCENARIO_YAML.parent.parent / "fp04-starvation-blocking" / "scenario.yaml"
    resolved = compile_author_scenario(load_author_yaml(fp04_yaml))
    assert resolved["experiment"]["total_duration_ticks"] == (4 + 8) * 3600
    assert resolved["metrics"]["machine_state"]["membership_resolution"] == "dynamic_boundary"
    for state in ("productive", "starved", "blocked"):
        fraction = resolved["metrics"][f"fraction_{state}"]
        assert fraction["denominator"] == "full_window"
        assert (fraction["window"]["start_tick"], fraction["window"]["end_tick"]) == (14400, 43200)
    plan = resolved["observation_plan"]["machine_state"]
    assert plan[0]["entity_set"] == "line_machines"


def test_state_fraction_rejects_shrunken_denominator(raw):
    # Only the explicit full-window denominator exists in the POC; anything
    # that looks like classified-time-only is rejected (ADR 0010 §12).
    bad = _with_machine_state(raw)
    bad["metrics"]["fraction_starved"]["denominator"] = "classified_time"
    with pytest.raises(CompilationError):
        _compile_raw(bad)


# --- demand / service metrics (ADR 0008, issue #9) --------------------------

def _with_demand(raw_doc, *, max_wait="30s", horizon_phase="service_tail"):
    doc = copy.deepcopy(raw_doc)
    doc["experiment"]["phases"].append({"id": "service_tail", "duration": "1m"})
    doc["ports"]["finished_goods"]["demand"] = {
        "id": "customer_demand",
        "shortage_policy": "backlog",
        "allocation": "fifo",
        "active_phases": ["measured"],
        "schedule": {"type": "constant", "rate": "12/min"},
    }
    doc["metrics"]["customer_service"] = {
        "type": "on_time_item_rate",
        "demand": "customer_demand",
        "cohort_window": {"phase": "measured"},
        "max_wait": max_wait,
        "observation_horizon": {"through_phase": horizon_phase},
    }
    return doc


def test_demand_and_service_metric_compile(raw):
    resolved = _compile_raw(_with_demand(raw))
    demand = resolved["ports"]["finished_goods"]["demand"]
    assert demand["schedule"] == {"type": "constant", "quantity": 1, "period_ticks": 300}
    service = resolved["metrics"]["customer_service"]
    assert service["max_wait_ticks"] == 1800
    assert service["observation_horizon"]["end_tick"] == 43200 + 3600
    assert resolved["observation_plan"]["demand"] == [
        {"demand": "customer_demand", "port": "finished_goods", "allocation": "fifo"}
    ]


def test_fp03_hash_unchanged_by_demand_support(author):
    # No demand declared => no demand keys anywhere in the resolved document.
    resolved = compile_author_scenario(author)
    assert resolved_hash(resolved) == FP03_COMMITTED_HASH
    assert "demand" not in resolved["observation_plan"]


def test_unobservable_deadline_rejected(raw):
    # Horizon ends with the measured phase: the last cohort's deadline can
    # never be observed -> compile error, not a silently censored metric.
    bad = _with_demand(raw, horizon_phase="measured")
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("deadline" in p for p in exc.value.problems)


def test_zero_max_wait_rejected(raw):
    bad = _with_demand(raw, max_wait="0t")
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("max_wait" in p for p in exc.value.problems)


def test_unknown_demand_reference_rejected(raw):
    bad = _with_demand(raw)
    bad["metrics"]["customer_service"]["demand"] = "ghost_demand"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("ghost_demand" in p for p in exc.value.problems)


def test_source_port_cannot_declare_demand(raw):
    bad = _with_demand(raw)
    bad["ports"]["workpiece_source"]["demand"] = bad["ports"]["finished_goods"]["demand"]
    with pytest.raises(CompilationError):
        _compile_raw(bad)


# --- objectives (ADR 0012, issue #10) ---------------------------------------

def _with_objectives(raw_doc):
    doc = _with_demand(raw_doc)
    doc["objectives"] = {
        "service_requirement": {"type": "requirement", "metric": "customer_service", "minimum": 0.95},
        "throughput_band": {"type": "requirement", "metric": "measured_throughput",
                            "range": {"minimum": "10/min", "maximum": "20/min"}},
        "minimize_wip": {"type": "preference", "metric": "average_wip", "direction": "minimize"},
    }
    doc["visibility"]["learner_live"]["objectives"] = ["service_requirement"]
    doc["visibility"]["learner_post_run"]["objectives"] = ["service_requirement", "minimize_wip"]
    return doc


def test_objectives_compile_with_units(raw):
    resolved = _compile_raw(_with_objectives(raw))
    objectives = resolved["objectives"]
    assert objectives["service_requirement"] == {
        "type": "requirement", "metric": "customer_service", "unit": "fraction", "minimum": 0.95,
    }
    band = objectives["throughput_band"]
    assert band["unit"] == "per_minute"
    assert band["minimum"] == pytest.approx(10.0) and band["maximum"] == pytest.approx(20.0)
    assert objectives["minimize_wip"]["direction"] == "minimize"


def test_objective_free_scenarios_have_no_objectives_key(author):
    resolved = compile_author_scenario(author)
    assert "objectives" not in resolved
    assert resolved_hash(resolved) == FP03_COMMITTED_HASH


def test_objective_unknown_metric_rejected(raw):
    bad = _with_objectives(raw)
    bad["objectives"]["minimize_wip"]["metric"] = "ghost_metric"
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("ghost_metric" in p for p in exc.value.problems)


def test_objective_on_non_scalar_metric_rejected(raw):
    bad = _with_objectives(raw)
    bad["objectives"]["bad"] = {"type": "requirement", "metric": "line_wip", "minimum": 1}
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("no scalar objective semantics" in p for p in exc.value.problems)


def test_fraction_threshold_out_of_range_rejected(raw):
    bad = _with_objectives(raw)
    bad["objectives"]["service_requirement"]["minimum"] = 95  # meant 0.95
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("within [0, 1]" in p for p in exc.value.problems)


def test_requirement_needs_exactly_one_rule(raw):
    bad = _with_objectives(raw)
    bad["objectives"]["service_requirement"]["maximum"] = 1.0  # plus existing minimum
    with pytest.raises(CompilationError):
        _compile_raw(bad)


def test_visibility_unknown_objective_rejected(raw):
    bad = _with_objectives(raw)
    bad["visibility"]["learner_live"]["objectives"] = ["ghost_objective"]
    with pytest.raises(CompilationError) as exc:
        _compile_raw(bad)
    assert any("ghost_objective" in p for p in exc.value.problems)


def test_supply_loss_requires_finite_scheduled_buffer(raw):
    doc = copy.deepcopy(raw)
    doc["metrics"]["supply_loss"] = {
        "type": "supply_loss", "port": "workpiece_source",
        "window": {"phase": "measured"},
    }
    # fp03's source uses replenish supply: no scheduled arrivals to lose.
    with pytest.raises(CompilationError) as exc:
        _compile_raw(doc)
    assert any("no scheduled supply" in p for p in exc.value.problems)

    doc["ports"]["workpiece_source"]["supply"] = {
        "mode": "scheduled",
        "schedule": {"type": "constant", "rate": "36/min"},
    }
    with pytest.raises(CompilationError) as exc:
        _compile_raw(doc)
    assert any("unbounded external" in p for p in exc.value.problems)

    doc["ports"]["workpiece_source"]["supply"]["external_buffer"] = {"capacity": 10}
    resolved = _compile_raw(doc)
    assert resolved["metrics"]["supply_loss"]["port"] == "workpiece_source"
