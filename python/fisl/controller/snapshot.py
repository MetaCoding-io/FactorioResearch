"""Scripted screenshot sessions (`fisl snap`) — experimental.

A headless server cannot render, but a connected graphical client can: the
server issues `game.take_screenshot{...}` targeting the connected player and
the PNG is rendered and saved on the *client's* machine under its
script-output directory. So a photo session = launch the run, ask the human
only to connect, then drive camera position/zoom/overlays from here.

Shot lists are defined per scenario id; camera coordinates come from the
same layout constants the baseline builder uses, so the framing stays true
to the committed world.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from fisl.controller.process import FactorioServer
from fisl.controller.protocol import FislProtocol


class SnapError(Exception):
    pass


@dataclass
class Shot:
    filename: str            # target name under script-output/fisl-snap/
    caption: str
    at_experiment_tick: int  # 0 = before start (READY world)
    solution: str | None     # scripted solution to apply first, if any
    position: tuple[float, float] | None  # None = player's own viewpoint
    zoom: float = 0.6
    show_gui: bool = False
    show_entity_info: bool = True  # the Alt overlay


# Lab 3 shot list — filenames match course/images/lab-03/README.md.
SHOT_SETS: dict[str, list[Shot]] = {
    "fp-03-littles-law": [
        Shot(
            filename="fisl-panel-ready.png",
            caption="FISL panel in READY at spawn",
            at_experiment_tick=0, solution=None,
            position=None, zoom=0.8, show_gui=True, show_entity_info=False,
        ),
        Shot(
            filename="run1-jammed-belt.png",
            caption="baseline: input belt packed solid",
            at_experiment_tick=3 * 3600, solution=None,
            position=(-38.0, 0.0), zoom=0.55,
        ),
        Shot(
            filename="run2-pull-gate.png",
            caption="pull gate at machine 1, belt nearly empty",
            at_experiment_tick=3 * 3600, solution="a-pull-signal",
            position=(-36.0, 0.0), zoom=0.55,
        ),
    ],
    # Lab 4 shot list — filenames match course/images/lab-04/README.md.
    # Steady state needs the M1->M2 buffer full: shoot at ~6 min.
    "fp-04-starvation-blocking": [
        Shot(
            filename="lab4-line-overview.png",
            caption="the whole compact line at READY: three different machines",
            at_experiment_tick=0, solution=None,
            position=(0.5, 0.5), zoom=0.45, show_gui=False,
        ),
        Shot(
            filename="lab4-blocked-starved.png",
            caption="baseline mid-run: M1 backed up solid, M3 waiting on an empty belt",
            at_experiment_tick=6 * 3600, solution=None,
            position=(0.5, 0.5), zoom=0.45,
        ),
        Shot(
            filename="lab4-buffer-chest.png",
            caption="solution A: the inline buffer chest absorbing M1's surplus",
            at_experiment_tick=6 * 3600, solution="a-buffer-before-constraint",
            position=(-4.0, 0.5), zoom=0.7,
        ),
    ],
}


def _take_screenshot_lua(shot: Shot) -> str:
    args = [
        'player = game.connected_players[1]',
        'by_player = game.connected_players[1]',
        f'path = "fisl-snap/{shot.filename}"',
        "resolution = {1920, 1080}",
        f"zoom = {shot.zoom}",
        f"show_gui = {'true' if shot.show_gui else 'false'}",
        f"show_entity_info = {'true' if shot.show_entity_info else 'false'}",
        "anti_alias = true",
    ]
    if shot.position is not None:
        args.append(f"position = {{{shot.position[0]}, {shot.position[1]}}}")
    body = (
        "if #game.connected_players == 0 then rcon.print('snap-fail: no connected player') "
        "else local ok, err = pcall(function() game.take_screenshot{"
        + ", ".join(args)
        + "} end) rcon.print(ok and 'snap-ok' or ('snap-fail: ' .. tostring(err))) end"
    )
    return "/silent-command " + body


def _wait_for_player(protocol: FislProtocol, console: Console, timeout: float = 600.0) -> None:
    console.print("[bold]Connect your Factorio client now[/bold] — waiting for a player…")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        count = protocol.rcon.command(
            "/silent-command rcon.print(#game.connected_players)"
        ).strip()
        if count.isdigit() and int(count) > 0:
            console.print("Player connected.")
            time.sleep(2.0)  # let the client finish loading/rendering
            return
        time.sleep(1.0)
    raise SnapError("no player connected within timeout")


def _wait_for_tick(protocol: FislProtocol, target_tick: int, timeout: float = 900.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = protocol.get_status()
        if status.get("experiment_tick", -1) >= target_tick:
            return
        if status.get("lifecycle") in ("COMPLETED", "ABORTED"):
            raise SnapError(f"run ended before tick {target_tick}: {status.get('lifecycle')}")
        time.sleep(1.0)
    raise SnapError(f"experiment tick {target_tick} not reached in time")


def run_photo_session(
    *,
    scenario_dir: Path,
    factorio_bin: Path,
    scenario_id: str,
    runs_dir: Path,
    console: Console,
) -> list[str]:
    """Execute the shot list. Returns the captured filenames.

    Each distinct `solution` value needs its own run (its own world state),
    and each run needs the human to (re)connect once. Photo-session runs are
    aborted after their shots — they are not data runs.
    """
    from fisl.scenario.canonical import file_sha256
    from fisl.scenario.compiler import compile_author_scenario, load_author_yaml, resolved_hash
    from fisl.scenario.runconfig import build_run_configuration, default_run_profile

    shots = SHOT_SETS.get(scenario_id)
    if not shots:
        raise SnapError(f"no shot list defined for scenario {scenario_id!r}")

    author = load_author_yaml(scenario_dir / "scenario.yaml")
    resolved = compile_author_scenario(author)
    baseline = scenario_dir / resolved["factorio"]["baseline_save"]
    captured: list[str] = []

    # Group shots by required solution, preserving order.
    groups: list[tuple[str | None, list[Shot]]] = []
    for shot in shots:
        if groups and groups[-1][0] == shot.solution:
            groups[-1][1].append(shot)
        else:
            groups.append((shot.solution, [shot]))

    for group_index, (solution_id, group_shots) in enumerate(groups):
        console.print(
            f"\n[bold]Photo run {group_index + 1}/{len(groups)}[/bold]"
            + (f" (solution: {solution_id})" if solution_id else " (baseline)")
        )
        workspace = runs_dir / f"_snap-{scenario_id}-{group_index}"
        server = FactorioServer(factorio_bin, workspace, baseline)
        server.prepare()
        server.launch()
        try:
            rcon = server.wait_for_rcon()
            protocol = FislProtocol(rcon)
            run_config = build_run_configuration(
                resolved_scenario_hash=resolved_hash(resolved),
                seed=resolved["experiment"]["default_seed"],
                baseline_path=str(baseline.name),
                baseline_sha256=file_sha256(str(baseline)),
                run_profile=default_run_profile("interactive"),
            )
            protocol.upload_configuration(
                {"run_configuration": run_config, "resolved_scenario": resolved}
            )
            if solution_id:
                from fisl.controller.solutions import (
                    apply_solution,
                    load_solution,
                    resolve_solution_path,
                )

                apply_solution(
                    load_solution(resolve_solution_path(scenario_dir, solution_id)),
                    rcon,
                )
            console.print(
                f"Connect to [bold]localhost:{server.game_port}[/bold] "
                f"(add --mod-directory {server.workspace / 'mods'})"
            )
            _wait_for_player(protocol, console)

            started = False
            for shot in group_shots:
                if shot.at_experiment_tick > 0 and not started:
                    protocol.request_start()
                    started = True
                if shot.at_experiment_tick > 0:
                    console.print(
                        f"Waiting for experiment tick {shot.at_experiment_tick} "
                        f"({shot.at_experiment_tick // 3600}m in) — feel free to watch…"
                    )
                    _wait_for_tick(protocol, shot.at_experiment_tick)
                response = rcon.command(_take_screenshot_lua(shot)).strip()
                if response != "snap-ok":
                    raise SnapError(f"{shot.filename}: {response}")
                console.print(f"  [green]captured[/green] {shot.filename} — {shot.caption}")
                captured.append(shot.filename)
            if started:
                protocol.request_abort("photo_session_complete")
        finally:
            server.stop()

    return captured
