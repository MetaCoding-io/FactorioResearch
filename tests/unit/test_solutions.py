"""Unit tests for scripted reference solutions."""

from pathlib import Path

import pytest

from fisl.controller.solutions import (
    STEP_OK,
    SolutionError,
    apply_solution,
    load_solution,
    resolve_solution_path,
)

REPO = Path(__file__).resolve().parents[2]
FP03 = REPO / "scenarios/factory-physics/fp03-littles-law"


def write_solution(tmp_path: Path, name: str, sources: dict[str, str]) -> Path:
    directory = tmp_path / name
    directory.mkdir()
    for filename, source in sources.items():
        (directory / filename).write_text(source)
    return directory


def test_fp03_pull_signal_solution_loads():
    solution = load_solution(FP03 / "solutions" / "a-pull-signal")
    assert solution.solution_id == "a-pull-signal"
    assert len(solution.steps) == 1
    step = solution.steps[0]
    assert "--" not in step.command  # comments stripped for single-line transmit
    assert STEP_OK in step.command
    assert len(step.command) < 3500
    assert step.sha256.startswith("sha256:")
    provenance = solution.provenance()
    assert provenance["id"] == "a-pull-signal"
    assert provenance["applied_at"] == "pre_start"


def test_inline_comment_rejected(tmp_path):
    directory = write_solution(
        tmp_path, "bad", {"solution.lua": 'local x = 1 -- boom\nrcon.print("solution-step-ok")\n'}
    )
    with pytest.raises(SolutionError, match="inline '--'"):
        load_solution(directory)


def test_missing_step_ok_rejected(tmp_path):
    directory = write_solution(tmp_path, "bad", {"solution.lua": 'rcon.print("done")\n'})
    with pytest.raises(SolutionError, match="solution-step-ok"):
        load_solution(directory)


def test_steps_apply_in_sorted_order(tmp_path):
    directory = write_solution(
        tmp_path,
        "multi",
        {
            "02-second.lua": 'rcon.print("solution-step-ok")\n',
            "01-first.lua": 'rcon.print("solution-step-ok")\n',
        },
    )
    solution = load_solution(directory)
    assert [step.name for step in solution.steps] == ["01-first.lua", "02-second.lua"]

    sent = []

    class FakeRcon:
        def command(self, text):
            sent.append(text)
            return STEP_OK + "\n"

    apply_solution(solution, FakeRcon())
    assert len(sent) == 2 and all(text.startswith("/silent-command ") for text in sent)


def test_failing_step_raises(tmp_path):
    directory = write_solution(tmp_path, "solo", {"s.lua": 'rcon.print("solution-step-ok")\n'})
    solution = load_solution(directory)

    class FakeRcon:
        def command(self, _text):
            return "solution-step-fail: inserter not found"

    with pytest.raises(SolutionError, match="inserter not found"):
        apply_solution(solution, FakeRcon())


def test_resolve_by_id_and_path(tmp_path):
    assert resolve_solution_path(FP03, "a-pull-signal") == FP03 / "solutions" / "a-pull-signal"
    direct = write_solution(tmp_path, "direct", {"s.lua": 'rcon.print("solution-step-ok")\n'})
    assert resolve_solution_path(FP03, str(direct)) == direct
    with pytest.raises(SolutionError):
        resolve_solution_path(FP03, "nonexistent")
