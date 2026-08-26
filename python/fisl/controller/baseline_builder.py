"""Programmatic baseline construction for Lab 3 (Issue #2 Stage B).

Builds `scenarios/factory-physics/fp03-littles-law/baseline.zip` against a
real Factorio 2.0.77 headless server:

    map create -> launch server (mods active, console primed)
      -> construct the Lab 3 world via batched /silent-command
      -> game.server_save -> copy into the scenario package
      -> optional verification: full headless `fisl run` of the actual
         fp03 scenario against the new baseline.

Layout conventions follow the spike-validated runtime behaviors: inserters
are placed west-facing (pickup west tile, drop east tile); no runtime
pickup/drop vector writes.

The Lab 3 line (y = 0.5 row, flow west -> east):

    fisl-source-port (-44.5)
      -> inserter -> belts
      -> M1 assembling-machine-1 @ -30.5  (rough -> machined, 2s)
      -> belts
      -> M2 assembling-machine-1 @ 0.5    (machined -> inspected, 1s)
      -> belts
      -> M3 assembling-machine-1 @ 30.5   (inspected -> finished, 1s)
      -> belts
      -> inserter -> fisl-sink-port (44.5)

Power is learner-comprehensible: solar field + substations, always_day.
A toolbox chest near spawn holds untracked construction materials (belts,
inserters, chests, assemblers) — untracked items never enter any metric.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from fisl.controller.process import FactorioServer, ProcessError, locate_repo_mods

# --- layout ----------------------------------------------------------------

SOURCE_POS = (-44.5, 0.5)
SINK_POS = (44.5, 0.5)

MACHINES = [
    # (center_x, recipe)
    (-30.5, "fisl-machine-workpiece"),
    (0.5, "fisl-inspect-workpiece"),
    (30.5, "fisl-finish-workpiece"),
]

MAP_GEN_SETTINGS = {
    "width": 256,
    "height": 128,
    "seed": 20260825,
    "water": 0,
    "starting_area": 3,
    "peaceful_mode": True,
    "autoplace_controls": {
        "enemy-base": {"frequency": 0, "size": 0},
        "trees": {"frequency": 0, "size": 0},
        "rocks": {"frequency": 0, "size": 0},
    },
    "cliff_settings": {"richness": 0},
}

TOOLBOX_ITEMS = {
    "transport-belt": 200,
    "fast-inserter": 20,
    "wooden-chest": 20,
    "assembling-machine-1": 6,
    "small-electric-pole": 30,
}


@dataclass
class Placement:
    name: str
    x: float
    y: float
    direction: str | None = None  # defines.direction.<value>
    recipe: str | None = None


def lab3_placements() -> list[Placement]:
    """Deterministic entity list for the Lab 3 baseline world."""
    placements: list[Placement] = []
    row_y = 0.5

    placements.append(Placement("fisl-source-port", *SOURCE_POS))
    placements.append(Placement("fisl-sink-port", *SINK_POS))

    # Machines with flanking inserters (west-facing: pickup west, drop east).
    machine_edges: list[tuple[float, float]] = []  # (input_pickup_tile, output_drop_tile)
    for center_x, recipe in MACHINES:
        placements.append(Placement("assembling-machine-1", center_x, row_y, recipe=recipe))
        input_inserter_x = center_x - 2.0
        output_inserter_x = center_x + 2.0
        placements.append(Placement("fast-inserter", input_inserter_x, row_y, direction="west"))
        placements.append(Placement("fast-inserter", output_inserter_x, row_y, direction="west"))
        machine_edges.append((input_inserter_x - 1.0, output_inserter_x + 1.0))

    # Boundary inserters at the ports.
    source_inserter_x = SOURCE_POS[0] + 1.0
    sink_inserter_x = SINK_POS[0] - 1.0
    placements.append(Placement("fast-inserter", source_inserter_x, row_y, direction="west"))
    placements.append(Placement("fast-inserter", sink_inserter_x, row_y, direction="west"))

    # Belt segments between drop and pickup tiles, all heading east.
    segments: list[tuple[float, float]] = []
    segments.append((source_inserter_x + 1.0, machine_edges[0][0]))          # source -> M1
    segments.append((machine_edges[0][1], machine_edges[1][0]))              # M1 -> M2
    segments.append((machine_edges[1][1], machine_edges[2][0]))              # M2 -> M3
    segments.append((machine_edges[2][1], sink_inserter_x - 1.0))            # M3 -> sink
    for start_x, end_x in segments:
        x = start_x
        while x <= end_x + 1e-9:
            placements.append(Placement("transport-belt", x, row_y, direction="east"))
            x += 1.0

    # Power: substations along the line + solar field near the middle.
    # 18 panels (~1.08 MW) all inside the central substation's supply area
    # (radius 9 around (0,-4)): rows y=-13.5/-10.5/-7.5, cols x=-7.5..7.5.
    # Topmost row spans y=[-9,-6], clear of the substation footprint [-5,-3].
    for pole_x in (-36.0, -18.0, 0.0, 18.0, 36.0):
        placements.append(Placement("substation", pole_x, -4.0))
    for i in range(18):
        col, row = i % 6, i // 6
        placements.append(Placement("solar-panel", -7.5 + col * 3.0, -13.5 + row * 3.0))

    # Toolbox near spawn (untracked materials; irrelevant to all metrics).
    placements.append(Placement("steel-chest", 0.5, 7.5))
    return placements


# --- Lua generation ---------------------------------------------------------

# Maps made with `factorio --create` run the freeplay scenario, whose intro
# (crash-site cutscene, ship wreckage, rocket objective, starter items) is
# deferred until the FIRST player ever joins. A headlessly built/verified
# baseline therefore joins "armed": the first human connection crash-lands a
# ship onto the lab. Neutralize it via freeplay's remote interface before
# saving; the settings persist in the save.
NEUTRALIZE_FREEPLAY_LUA = (
    "local ok = pcall(function() "
    'local freeplay = remote.interfaces["freeplay"] '
    "if freeplay then "
    'if freeplay["set_skip_intro"] then remote.call("freeplay", "set_skip_intro", true) end '
    'if freeplay["set_disable_crashsite"] then remote.call("freeplay", "set_disable_crashsite", true) end '
    'if freeplay["set_created_items"] then remote.call("freeplay", "set_created_items", {}) end '
    'if freeplay["set_respawn_items"] then remote.call("freeplay", "set_respawn_items", {}) end '
    "end end) "
    'rcon.print(ok and "freeplay-neutralized" or "freeplay-neutralize-failed")'
)

_PREAMBLE = (
    'local surface = game.surfaces["nauvis"] '
    "surface.always_day = true "
    "for _, entity in pairs(surface.find_entities_filtered{area = {{-60, -30}, {60, 30}}}) do "
    'if entity.type ~= "character" then entity.destroy() end end '
    'rcon.print("prepared")'
)

# Expected entity counts double-check the construction inside the game
# before anything is saved: every create_entity that silently failed (e.g.
# an unexpected collision) surfaces here instead of in the baseline.
EXPECTED_COUNTS = {
    "assembling-machine-1": 3,
    "fisl-source-port": 1,
    "fisl-sink-port": 1,
    "transport-belt": 71,
    "fast-inserter": 8,
    "substation": 5,
    "solar-panel": 18,
    "steel-chest": 1,
}

_EPILOGUE = (
    'local surface = game.surfaces["nauvis"] '
    + " ".join(
        f'do local n = #surface.find_entities_filtered{{name = "{name}"}} '
        f'if n ~= {count} then rcon.print("COUNT-FAIL {name} " .. n) return end end'
        for name, count in EXPECTED_COUNTS.items()
    )
    + " game.forces.player.set_spawn_position({0, 10}, surface) "
    "game.forces.player.chart(surface, {{-60, -30}, {60, 30}}) "
    'local box = surface.find_entities_filtered{name = "steel-chest", position = {0.5, 7.5}, radius = 0.5}[1] '
    'if box == nil then rcon.print("COUNT-FAIL toolbox missing") return end '
    + " ".join(
        f'box.get_inventory(defines.inventory.chest).insert{{name = "{item}", count = {count}}}'
        for item, count in TOOLBOX_ITEMS.items()
    )
    + ' rcon.print("finished")'
)


def placement_commands(placements: list[Placement], batch_size: int = 20) -> list[str]:
    """Render placements into batched /silent-command payload strings."""
    statements = []
    for placement in placements:
        args = [
            f'name = "{placement.name}"',
            f"position = {{{placement.x}, {placement.y}}}",
            'force = "player"',
            "raise_built = false",
        ]
        if placement.direction:
            args.append(f"direction = defines.direction.{placement.direction}")
        create = f"local e = surface.create_entity{{{', '.join(args)}}}"
        if placement.recipe:
            create += f' e.set_recipe("{placement.recipe}")'
        statements.append("do " + create + " end")

    commands = [_PREAMBLE]
    for index in range(0, len(statements), batch_size):
        batch = statements[index : index + batch_size]
        commands.append(
            'local surface = game.surfaces["nauvis"] '
            + " ".join(batch)
            + f' rcon.print("batch-{index // batch_size}-ok")'
        )
    commands.append(_EPILOGUE)
    return commands


# --- build ------------------------------------------------------------------

class BuildError(Exception):
    pass


def build_baseline(
    *,
    factorio_bin: Path,
    scenario_dir: Path,
    workspace: Path,
    console=None,
) -> Path:
    """Create baseline.zip for the scenario package. Returns the target path."""
    from fisl.controller.rcon import RconClient

    workspace.mkdir(parents=True, exist_ok=True)
    target = scenario_dir / "baseline.zip"

    # 1. raw map with mods active (port/workpiece prototypes must exist).
    mgs_path = workspace / "map-gen-settings.json"
    mgs_path.write_text(json.dumps(MAP_GEN_SETTINGS))
    raw_save = workspace / "raw.zip"
    mods_dir = workspace / "create-mods"
    mods_dir.mkdir(exist_ok=True)
    mod_list = [{"name": "base", "enabled": True}]
    for mod_path in locate_repo_mods():
        target_mod = mods_dir / mod_path.name
        if target_mod.exists():
            shutil.rmtree(target_mod)
        shutil.copytree(mod_path, target_mod)
        mod_list.append({"name": mod_path.name, "enabled": True})
    (mods_dir / "mod-list.json").write_text(json.dumps({"mods": mod_list}))

    import subprocess

    result = subprocess.run(
        [str(factorio_bin), "--create", str(raw_save),
         "--map-gen-settings", str(mgs_path), "--mod-directory", str(mods_dir)],
        capture_output=True, text=True, timeout=300,
    )
    if not raw_save.exists():
        raise BuildError(f"map creation failed:\n{result.stdout}\n{result.stderr}")

    # 2. launch a server on the raw map and construct the world.
    server = FactorioServer(factorio_bin, workspace / "server", raw_save)
    server.prepare()
    server.launch()
    try:
        client: RconClient = server.wait_for_rcon()
        response = client.command("/silent-command " + NEUTRALIZE_FREEPLAY_LUA)
        if "freeplay-neutralized" not in response:
            raise BuildError(f"freeplay intro could not be neutralized: {response!r}")
        for command in placement_commands(lab3_placements()):
            response = client.command("/silent-command " + command)
            if "ok" not in response and "prepared" not in response and "finished" not in response:
                raise BuildError(f"construction command failed: {response!r}")
        if console:
            console.print("World constructed; saving baseline…")

        # 3. save and collect. server_save writes into the workspace saves dir.
        client.command('/silent-command game.server_save("fp03-baseline")')
        saved = server.workspace / "saves" / "fp03-baseline.zip"
        deadline = time.monotonic() + 60
        while not saved.exists() and time.monotonic() < deadline:
            time.sleep(0.5)
        if not saved.exists():
            raise BuildError(f"server_save produced no file at {saved}")
        # Let the write finish (size stabilizes).
        last_size = -1
        while time.monotonic() < deadline:
            size = saved.stat().st_size
            if size == last_size:
                break
            last_size = size
            time.sleep(0.5)
        shutil.copyfile(saved, target)
    finally:
        server.stop()

    if console:
        console.print(f"Baseline written: {target} ({target.stat().st_size} bytes)")
    return target


def verify_baseline(
    *,
    factorio_bin: Path,
    scenario_dir: Path,
    runs_dir: Path,
    console=None,
    headless_speed: float = 10.0,
) -> dict:
    """Acceptance: full headless run of the actual scenario on the new
    baseline. Returns the run summary; raises BuildError on failure."""
    from fisl.controller.run import RunError, execute_run

    try:
        result = execute_run(
            scenario_dir=scenario_dir,
            headless=True,
            factorio_bin=factorio_bin,
            runs_dir=runs_dir,
            headless_speed=headless_speed,
            console=console,
        )
    except RunError as exc:
        raise BuildError(f"verification run failed: {exc}") from exc
    if result.lifecycle != "COMPLETED":
        raise BuildError(f"verification run ended {result.lifecycle}")
    summary_path = result.run_dir / "summary.json"
    if not summary_path.exists():
        raise BuildError("verification run produced no summary.json")
    summary = json.loads(summary_path.read_text())

    problems = []
    throughput = summary["metrics"].get("measured_throughput", {})
    if not throughput.get("completed_quantity", 0) > 0:
        problems.append("no completed workpieces in measured window")
    average = summary["metrics"].get("average_wip", {})
    if not average.get("coverage_complete"):
        problems.append("average WIP coverage incomplete")
    if average.get("census_validity", {}).get("valid") is not True:
        problems.append(f"census validity failed: {average.get('census_validity')}")
    verification = summary.get("lua_cross_verification", {})
    if verification.get("available") and not verification.get("agrees"):
        problems.append(f"Lua/Python mismatch: {verification.get('mismatches')}")
    if problems:
        raise BuildError("baseline verification failed: " + "; ".join(problems))
    return summary
