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
