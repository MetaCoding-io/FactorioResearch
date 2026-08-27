"""Programmatic baseline construction for lab scenario packages.

Builds `scenarios/.../<lab>/baseline.zip` against a real Factorio 2.0.77
headless server:

    map create -> launch server (mods active, console primed)
      -> construct the lab world via batched /silent-command
      -> game.server_save -> copy into the scenario package
      -> optional verification: full headless `fisl run` of the actual
         scenario against the new baseline.

Layout conventions follow the spike-validated runtime behaviors: inserters
are placed west-facing (pickup west tile, drop east tile); no runtime
pickup/drop vector writes. Every lab is a single west -> east line on the
y = 0.5 row (`LabLayout`); the scenario id in scenario.yaml selects the
layout.

Lab 3 (fp-03-littles-law): three identical assembling-machine-1 stages,
bottleneck at M1 (2s machine recipe / 0.5 speed) — the Little's Law queue
forms at admission.

Lab 4 (fp-04-starvation-blocking): a compact line whose CONSTRAINT IS IN
THE MIDDLE via machine speeds — M1 asm-3 (2s/1.25 = 1.6s), M2 asm-1
(1s/0.5 = 2.0s, the constraint), M3 asm-2 (1s/0.75 = 1.33s). Upstream of
the constraint blocks, downstream starves: the diagnosis signature Lab 4
teaches.

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


@dataclass
class Placement:
    name: str
    x: float
    y: float
    direction: str | None = None  # defines.direction.<value>
    recipe: str | None = None


@dataclass(frozen=True)
class LabLayout:
    scenario_id: str
    source_pos: tuple[float, float]
    sink_pos: tuple[float, float]
    machines: list[tuple[float, str, str]]  # (center_x, prototype, recipe)
    substation_xs: tuple[float, ...]
    toolbox_items: dict[str, int]
    expected_counts: dict[str, int]  # independent in-game construction check
    save_name: str = ""

    def placements(self) -> list[Placement]:
        return line_placements(self)


def line_placements(layout: LabLayout) -> list[Placement]:
    """Deterministic entity list for a single-line lab world."""
    placements: list[Placement] = []
    row_y = 0.5

    placements.append(Placement("fisl-source-port", *layout.source_pos))
    placements.append(Placement("fisl-sink-port", *layout.sink_pos))

    # Machines with flanking inserters (west-facing: pickup west, drop east).
    machine_edges: list[tuple[float, float]] = []  # (input_pickup_tile, output_drop_tile)
    for center_x, prototype, recipe in layout.machines:
        placements.append(Placement(prototype, center_x, row_y, recipe=recipe))
        input_inserter_x = center_x - 2.0
        output_inserter_x = center_x + 2.0
        placements.append(Placement("fast-inserter", input_inserter_x, row_y, direction="west"))
        placements.append(Placement("fast-inserter", output_inserter_x, row_y, direction="west"))
        machine_edges.append((input_inserter_x - 1.0, output_inserter_x + 1.0))

    # Boundary inserters at the ports.
    source_inserter_x = layout.source_pos[0] + 1.0
    sink_inserter_x = layout.sink_pos[0] - 1.0
    placements.append(Placement("fast-inserter", source_inserter_x, row_y, direction="west"))
    placements.append(Placement("fast-inserter", sink_inserter_x, row_y, direction="west"))

    # Belt segments between drop and pickup tiles, all heading east.
    segments: list[tuple[float, float]] = []
    segments.append((source_inserter_x + 1.0, machine_edges[0][0]))          # source -> M1
    for index in range(len(machine_edges) - 1):
        segments.append((machine_edges[index][1], machine_edges[index + 1][0]))
    segments.append((machine_edges[-1][1], sink_inserter_x - 1.0))           # last machine -> sink
    for start_x, end_x in segments:
        x = start_x
        while x <= end_x + 1e-9:
            placements.append(Placement("transport-belt", x, row_y, direction="east"))
            x += 1.0

    # Power: substations along the line + solar field near the middle.
    # 18 panels (~1.08 MW) all inside the central substation's supply area
    # (radius 9 around (0,-4)): rows y=-13.5/-10.5/-7.5, cols x=-7.5..7.5.
    # Topmost row spans y=[-9,-6], clear of the substation footprint [-5,-3].
    for pole_x in layout.substation_xs:
        placements.append(Placement("substation", pole_x, -4.0))
    for i in range(18):
        col, row = i % 6, i // 6
        placements.append(Placement("solar-panel", -7.5 + col * 3.0, -13.5 + row * 3.0))

    # Toolbox near spawn (untracked materials; irrelevant to all metrics).
    placements.append(Placement("steel-chest", 0.5, 7.5))
    return placements


LAB3 = LabLayout(
    scenario_id="fp-03-littles-law",
    source_pos=(-44.5, 0.5),
    sink_pos=(44.5, 0.5),
    machines=[
        (-30.5, "assembling-machine-1", "fisl-machine-workpiece"),
        (0.5, "assembling-machine-1", "fisl-inspect-workpiece"),
        (30.5, "assembling-machine-1", "fisl-finish-workpiece"),
    ],
    substation_xs=(-36.0, -18.0, 0.0, 18.0, 36.0),
    toolbox_items={
        "transport-belt": 200,
        "fast-inserter": 20,
        "wooden-chest": 20,
        "assembling-machine-1": 6,
        "small-electric-pole": 30,
    },
    expected_counts={
        "assembling-machine-1": 3,
        "fisl-source-port": 1,
        "fisl-sink-port": 1,
        "transport-belt": 71,
        "fast-inserter": 8,
        "substation": 5,
        "solar-panel": 18,
        "steel-chest": 1,
    },
    save_name="fp03-baseline",
)

LAB4 = LabLayout(
    scenario_id="fp-04-starvation-blocking",
    source_pos=(-20.5, 0.5),
    sink_pos=(21.5, 0.5),
    machines=[
        # Constraint deliberately in the MIDDLE: 1.6s / 2.0s / 1.33s per craft.
        (-10.5, "assembling-machine-3", "fisl-machine-workpiece"),
        (0.5, "assembling-machine-1", "fisl-inspect-workpiece"),
        (11.5, "assembling-machine-2", "fisl-finish-workpiece"),
    ],
    substation_xs=(-18.0, 0.0, 18.0),
    toolbox_items={
        "transport-belt": 100,
        "fast-inserter": 20,
        "wooden-chest": 10,
        "steel-chest": 4,
        "assembling-machine-1": 2,
        "assembling-machine-2": 2,
        "assembling-machine-3": 2,
        "small-electric-pole": 20,
    },
    expected_counts={
        "assembling-machine-1": 1,
        "assembling-machine-2": 1,
        "assembling-machine-3": 1,
        "fisl-source-port": 1,
        "fisl-sink-port": 1,
        "transport-belt": 24,
        "fast-inserter": 8,
        "substation": 3,
        "solar-panel": 18,
        "steel-chest": 1,
    },
    save_name="fp04-baseline",
)

LAB0 = LabLayout(
    scenario_id="fp-00-measuring-the-factory",
    source_pos=(-12.5, 0.5),
    sink_pos=(13.5, 0.5),
    machines=[
        (0.5, "assembling-machine-1", "fisl-machine-workpiece"),  # 4s per craft
    ],
    substation_xs=(-9.0, 9.0),
    toolbox_items={
        "transport-belt": 50,
        "fast-inserter": 6,
        "wooden-chest": 4,
        "small-electric-pole": 10,
    },
    expected_counts={
        "assembling-machine-1": 1,
        "fisl-source-port": 1,
        "fisl-sink-port": 1,
        "transport-belt": 18,
        "fast-inserter": 4,
        "substation": 2,
        "solar-panel": 18,
        "steel-chest": 1,
    },
    save_name="fp00-baseline",
)

LAB1 = LabLayout(
    scenario_id="fp-01-flow-and-capacity",
    source_pos=(-16.5, 0.5),
    sink_pos=(17.5, 0.5),
    machines=[
        # Installed capacities deliberately differ: 1.6s vs 2.0s per craft.
        (-5.5, "assembling-machine-3", "fisl-machine-workpiece"),
        (5.5, "assembling-machine-1", "fisl-inspect-workpiece"),
    ],
    substation_xs=(-9.0, 9.0),
    toolbox_items={
        "transport-belt": 100,
        "fast-inserter": 12,
        "wooden-chest": 6,
        "assembling-machine-1": 2,
        "assembling-machine-3": 1,
        "small-electric-pole": 15,
    },
    expected_counts={
        "assembling-machine-1": 1,
        "assembling-machine-3": 1,
        "fisl-source-port": 1,
        "fisl-sink-port": 1,
        "transport-belt": 21,
        "fast-inserter": 6,
        "substation": 2,
        "solar-panel": 18,
        "steel-chest": 1,
    },
    save_name="fp01-baseline",
)

# Lab 2 shares Lab 4's physical world (A fast -> B slow -> C fast is exactly
# the ToC line the Lab 2 contract requires); the scenarios differ in
# metrics, visibility, and reference solutions. Toolbox carries the upgrade
# machines the constraint lesson needs.
LAB2 = LabLayout(
    scenario_id="fp-02-the-constraint",
    source_pos=LAB4.source_pos,
    sink_pos=LAB4.sink_pos,
    machines=list(LAB4.machines),
    substation_xs=LAB4.substation_xs,
    toolbox_items={
        "transport-belt": 100,
        "fast-inserter": 20,
        "wooden-chest": 10,
        "assembling-machine-1": 2,
        "assembling-machine-2": 2,
        "assembling-machine-3": 2,
        "small-electric-pole": 20,
    },
    expected_counts=dict(LAB4.expected_counts),
    save_name="fp02-baseline",
)

# Lab 5 shares Lab 3's physical world — customer demand is external
# accounting attached to the sink, not a physical change. The toolbox adds
# circuit components for learner-built pull/throttle logic.
LAB5 = LabLayout(
    scenario_id="fp-05-push-and-pull",
    source_pos=LAB3.source_pos,
    sink_pos=LAB3.sink_pos,
    machines=list(LAB3.machines),
    substation_xs=LAB3.substation_xs,
    toolbox_items={
        "transport-belt": 200,
        "fast-inserter": 20,
        "wooden-chest": 20,
        "assembling-machine-1": 6,
        "small-electric-pole": 30,
        "decider-combinator": 4,
        "constant-combinator": 4,
        "arithmetic-combinator": 4,
    },
    expected_counts=dict(LAB3.expected_counts),
    save_name="fp05-baseline",
)

# Lab 6 shares the fast->slow->fast physical world (constraint mid-line);
# the capstone's complexity is upstream (scheduled finite supply) and
# downstream (customer demand), both external accounting. The toolbox
# carries every remedy the course taught: upgrade machines, buffer chests,
# circuit components.
LAB6 = LabLayout(
    scenario_id="fp-06-system-optimization",
    source_pos=LAB4.source_pos,
    sink_pos=LAB4.sink_pos,
    machines=list(LAB4.machines),
    substation_xs=LAB4.substation_xs,
    toolbox_items={
        "transport-belt": 100,
        "fast-inserter": 20,
        "wooden-chest": 10,
        "steel-chest": 4,
        "assembling-machine-1": 2,
        "assembling-machine-2": 2,
        "assembling-machine-3": 2,
        "small-electric-pole": 20,
        "decider-combinator": 4,
        "constant-combinator": 4,
        "arithmetic-combinator": 4,
    },
    expected_counts=dict(LAB4.expected_counts),
    save_name="fp06-baseline",
)

LABSANDBOX = LabLayout(
    # Operator training (on-ramp phase 2): Lab 0's one-machine world with a
    # toolbox stocked for every drill — belts, chests, an upgrade machine,
    # and combinators. The drills themselves are graded post-run by
    # scenarios/factory-physics/fp-sandbox/drills/check.lua, whose baseline
    # belt count must match this layout (unit-tested).
    scenario_id="fp-sandbox",
    source_pos=LAB0.source_pos,
    sink_pos=LAB0.sink_pos,
    machines=list(LAB0.machines),
    substation_xs=LAB0.substation_xs,
    toolbox_items={
        "transport-belt": 50,
        "fast-inserter": 8,
        "wooden-chest": 4,
        "assembling-machine-2": 2,
        "constant-combinator": 2,
        "decider-combinator": 2,
        "small-lamp": 2,
        "small-electric-pole": 10,
    },
    expected_counts=dict(LAB0.expected_counts),
    save_name="fp-sandbox-baseline",
)

LAYOUTS: dict[str, LabLayout] = {
    layout.scenario_id: layout
    for layout in (LAB0, LAB1, LAB2, LAB3, LAB4, LAB5, LAB6, LABSANDBOX)
}


def layout_for_scenario(scenario_dir: Path) -> LabLayout:
    import yaml

    raw = yaml.safe_load((scenario_dir / "scenario.yaml").read_text(encoding="utf-8"))
    scenario_id = raw["scenario"]["id"]
    layout = LAYOUTS.get(scenario_id)
    if layout is None:
        raise BuildError(
            f"no baseline layout registered for scenario {scenario_id!r} "
            f"(known: {sorted(LAYOUTS)})"
        )
    return layout


def lab3_placements() -> list[Placement]:
    return LAB3.placements()


def lab4_placements() -> list[Placement]:
    return LAB4.placements()


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

def _epilogue(layout: LabLayout) -> str:
    """Expected entity counts double-check the construction inside the game
    before anything is saved: every create_entity that silently failed (e.g.
    an unexpected collision) surfaces here instead of in the baseline."""
    return (
        'local surface = game.surfaces["nauvis"] '
        + " ".join(
            f'do local n = #surface.find_entities_filtered{{name = "{name}"}} '
            f'if n ~= {count} then rcon.print("COUNT-FAIL {name} " .. n) return end end'
            for name, count in layout.expected_counts.items()
        )
        + " game.forces.player.set_spawn_position({0, 10}, surface) "
        "game.forces.player.chart(surface, {{-60, -30}, {60, 30}}) "
        'local box = surface.find_entities_filtered{name = "steel-chest", position = {0.5, 7.5}, radius = 0.5}[1] '
        'if box == nil then rcon.print("COUNT-FAIL toolbox missing") return end '
        + " ".join(
            f'box.get_inventory(defines.inventory.chest).insert{{name = "{item}", count = {count}}}'
            for item, count in layout.toolbox_items.items()
        )
        + ' rcon.print("finished")'
    )


def placement_commands(layout: LabLayout, batch_size: int = 20) -> list[str]:
    """Render the layout into batched /silent-command payload strings."""
    statements = []
    for placement in layout.placements():
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
    commands.append(_epilogue(layout))
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
    layout = layout_for_scenario(scenario_dir)
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
        for command in placement_commands(layout):
            response = client.command("/silent-command " + command)
            if "ok" not in response and "prepared" not in response and "finished" not in response:
                raise BuildError(f"construction command failed: {response!r}")
        if console:
            console.print("World constructed; saving baseline…")

        # 3. save and collect. server_save writes into the workspace saves dir.
        client.command(f'/silent-command game.server_save("{layout.save_name}")')
        saved = server.workspace / "saves" / f"{layout.save_name}.zip"
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
    for metric_id, metric in summary["metrics"].items():
        if metric.get("type") == "state_fraction" and not metric.get("coverage_complete"):
            problems.append(f"{metric_id}: state-fraction classification coverage incomplete")
    if problems:
        raise BuildError("baseline verification failed: " + "; ".join(problems))
    return summary
