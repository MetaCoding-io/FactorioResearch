"""Scripted reference solutions ("Lab 3: solution A").

A solution is a directory inside a scenario package:

    scenarios/.../solutions/<solution-id>/
        README.md        # what the intervention is and why (course material)
        *.lua            # ordered steps applied via RCON after READY,
                         # before the experiment starts

Each .lua step is sent as one /silent-command (single line), so steps must
be transmission-safe: full-line comments are stripped, inline `--` is
rejected, and each step must end by printing exactly `solution-step-ok`
(any other output fails the run loudly).

Why scripts instead of solution baselines: the solution runs against the
SAME scenario and SAME baseline, so `fisl compare` certifies identical
experiment semantics and the measured delta is attributable to the
intervention alone. Because the script is deterministic, solution runs are
fully reproducible — usable as regression fixtures and as the instructor's
answer key. The solution's identity (id + per-step sha256) is recorded in
the run's provenance; it is deliberately NOT part of the reproducibility
fingerprint, which captures controlled inputs, not (scripted) player-side
actions (ADR 0014 §5).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

STEP_OK = "solution-step-ok"
MAX_COMMAND_CHARS = 3500


class SolutionError(Exception):
    pass


@dataclass
class SolutionStep:
    name: str
    command: str  # single-line Lua, ready for /silent-command
    sha256: str   # of the original file bytes


@dataclass
class Solution:
    solution_id: str
    directory: Path
    steps: list[SolutionStep]

    def provenance(self) -> dict:
        return {
            "id": self.solution_id,
            "applied_at": "pre_start",
            "steps": [{"name": step.name, "sha256": step.sha256} for step in self.steps],
        }


def _to_single_line(name: str, source: str) -> str:
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue  # full-line comment: safe to drop
        if "--" in stripped:
            raise SolutionError(
                f"{name}: inline '--' is not allowed — the step is transmitted as one "
                "line, so anything after an inline comment would swallow the rest"
            )
        if stripped:
            lines.append(stripped)
    command = " ".join(lines)
    if not command:
        raise SolutionError(f"{name}: step is empty after comment stripping")
    if STEP_OK not in command:
        raise SolutionError(f"{name}: step must end by printing '{STEP_OK}' via rcon.print")
    if len(command) > MAX_COMMAND_CHARS:
        raise SolutionError(
            f"{name}: step is {len(command)} chars (> {MAX_COMMAND_CHARS}); split it "
            "into multiple numbered .lua files"
        )
    return command


def load_solution(directory: Path) -> Solution:
    directory = Path(directory)
    if not directory.is_dir():
        raise SolutionError(f"solution directory not found: {directory}")
    lua_files = sorted(directory.glob("*.lua"))
    if not lua_files:
        raise SolutionError(f"{directory}: no .lua step files")
    steps = []
    for lua_file in lua_files:
        raw = lua_file.read_bytes()
        steps.append(
            SolutionStep(
                name=lua_file.name,
                command=_to_single_line(lua_file.name, raw.decode("utf-8")),
                sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
            )
        )
    return Solution(solution_id=directory.name, directory=directory, steps=steps)


def list_solutions(scenario_dir: Path) -> list[dict]:
    """Enumerate a scenario's solutions: id + first prose line of README."""
    solutions_dir = Path(scenario_dir) / "solutions"
    entries = []
    if not solutions_dir.is_dir():
        return entries
    for directory in sorted(p for p in solutions_dir.iterdir() if p.is_dir()):
        summary = ""
        readme = directory / "README.md"
        if readme.exists():
            for line in readme.read_text(encoding="utf-8").splitlines():
                stripped = line.strip().lstrip("#").strip()
                if stripped:
                    summary = stripped
                    break
        entries.append({"id": directory.name, "summary": summary})
    return entries


def resolve_solution_path(scenario_dir: Path, spec: str) -> Path:
    """Accept either a path or a bare id under <scenario>/solutions/."""
    as_path = Path(spec)
    if as_path.is_dir():
        return as_path
    candidate = scenario_dir / "solutions" / spec
    if candidate.is_dir():
        return candidate
    raise SolutionError(f"solution {spec!r} not found (looked at {as_path} and {candidate})")


def apply_solution(solution: Solution, rcon) -> None:
    """Send each step; any response other than a clean step-ok fails loudly."""
    for step in solution.steps:
        response = rcon.command("/silent-command " + step.command).strip()
        if response != STEP_OK:
            raise SolutionError(
                f"solution {solution.solution_id} step {step.name} failed: {response!r}"
            )
