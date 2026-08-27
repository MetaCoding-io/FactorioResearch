"""Drill-check plumbing (operator training): transmission safety of the real
check script, response validation, and the run-dir artifact."""

import json
from pathlib import Path

import pytest

from fisl.controller.drills import (
    DrillError,
    load_drill_check,
    parse_drill_response,
    run_drill_check,
)
from fisl.controller.solutions import MAX_COMMAND_CHARS

REPO = Path(__file__).resolve().parents[2]
SANDBOX = REPO / "scenarios/factory-physics/fp-sandbox"


def test_sandbox_check_is_transmission_safe():
    command = load_drill_check(SANDBOX)
    assert command is not None
    assert "\n" not in command
    assert "--" not in command
    assert len(command) <= MAX_COMMAND_CHARS
    assert "rcon.print" in command
    assert "helpers.table_to_json" in command


def test_scenario_without_drills_is_a_noop(tmp_path):
    assert load_drill_check(tmp_path) is None
    assert run_drill_check(tmp_path, rcon=None, run_dir=tmp_path) == {}


def test_parse_valid_response():
    payload = {"drills": [
        {"id": "d1", "passed": True, "detail": "ok"},
        {"id": "d2", "passed": False},
    ]}
    result = parse_drill_response(json.dumps(payload))
    assert [d["id"] for d in result["drills"]] == ["d1", "d2"]
    assert result["drills"][1]["passed"] is False
    assert result["drills"][1]["detail"] == ""


@pytest.mark.parametrize(
    "response",
    [
        "not json at all",
        json.dumps({"nope": []}),
        json.dumps({"drills": []}),
        json.dumps({"drills": ["bare string"]}),
        json.dumps({"drills": [{"id": "d1"}]}),  # missing 'passed'
    ],
)
def test_parse_rejects_malformed_responses(response):
    with pytest.raises(DrillError):
        parse_drill_response(response)


class _FakeRcon:
    def __init__(self, response):
        self.response = response
        self.sent = None

    def command(self, command):
        self.sent = command
        return self.response


def test_run_drill_check_writes_artifact(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    response = json.dumps({"drills": [
        {"id": "d1", "passed": True, "detail": "ok"},
        {"id": "d2", "passed": False, "detail": "not yet"},
    ]})
    rcon = _FakeRcon(response)
    summary = run_drill_check(SANDBOX, rcon, run_dir)
    assert summary == {"passed": 1, "total": 2}
    assert rcon.sent.startswith("/silent-command ")
    stored = json.loads((run_dir / "drills.json").read_text())
    assert [d["id"] for d in stored["drills"]] == ["d1", "d2"]


def test_sandbox_scenario_compiles_with_drill_ids_stable():
    # The scenario itself must compile; drill ids are course-facing (the
    # chapter references them), so pin them.
    from fisl.scenario.compiler import compile_author_scenario, load_author_yaml

    resolved = compile_author_scenario(load_author_yaml(SANDBOX / "scenario.yaml"))
    assert resolved["scenario"]["id"] == "fp-sandbox"
    check = (SANDBOX / "drills/check.lua").read_text()
    for drill_id in (
        "d1_place_belts",
        "d2_rotate_belt",
        "d3_chest_splice",
        "d4_machine_swap",
        "d5_enable_condition",
        "d6_combinator_pair",
    ):
        assert drill_id in check
