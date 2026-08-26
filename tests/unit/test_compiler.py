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
