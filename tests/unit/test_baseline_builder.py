"""Pure-logic tests for the lab baseline builders: layout geometry,
scenario consistency, and RCON command constraints — parametrized over
every registered lab layout. The actual construction and verification run
against real Factorio via `fisl build-baseline`."""

from pathlib import Path

import pytest
import yaml

from fisl.controller.baseline_builder import (
    LAYOUTS,
    NEUTRALIZE_FREEPLAY_LUA,
    placement_commands,
)

REPO = Path(__file__).resolve().parents[2]

SCENARIO_DIRS = {
    "fp-00-measuring-the-factory": "fp00-measuring-the-factory",
    "fp-01-flow-and-capacity": "fp01-flow-and-capacity",
    "fp-02-the-constraint": "fp02-the-constraint",
    "fp-03-littles-law": "fp03-littles-law",
    "fp-04-starvation-blocking": "fp04-starvation-blocking",
}

# The conserved transformation chain; each lab's machine list is a prefix.
RECIPE_CHAIN = ["fisl-machine-workpiece", "fisl-inspect-workpiece", "fisl-finish-workpiece"]

# Entity footprint sizes (tiles) for overlap checking.
SIZES = {
    "assembling-machine-1": 3,
    "assembling-machine-2": 3,
    "assembling-machine-3": 3,
    "substation": 2,
    "solar-panel": 3,
    "fisl-source-port": 1,
    "fisl-sink-port": 1,
    "transport-belt": 1,
    "fast-inserter": 1,
    "steel-chest": 1,
}

MACHINE_TYPES = {"assembling-machine-1", "assembling-machine-2", "assembling-machine-3"}


def scenario_raw(scenario_id):
    path = REPO / "scenarios/factory-physics" / SCENARIO_DIRS[scenario_id] / "scenario.yaml"
    return yaml.safe_load(path.read_text())


def bbox(placement):
    half = SIZES[placement.name] / 2.0
    return (placement.x - half, placement.y - half, placement.x + half, placement.y + half)


@pytest.fixture(params=sorted(LAYOUTS), ids=sorted(LAYOUTS))
def layout(request):
    return LAYOUTS[request.param]


def test_layouts_cover_all_lab_scenarios():
    assert sorted(LAYOUTS) == sorted(SCENARIO_DIRS)


def test_no_overlapping_footprints(layout):
    boxes = [(p, bbox(p)) for p in layout.placements()]
    for i, (pa, a) in enumerate(boxes):
        for pb, b in boxes[i + 1 :]:
            overlap = a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
            assert not overlap, f"{pa} overlaps {pb}"


def test_entity_counts_match_expected(layout):
    counts = {}
    for p in layout.placements():
        counts[p.name] = counts.get(p.name, 0) + 1
    assert counts == layout.expected_counts


def test_everything_inside_zone(layout):
    area = scenario_raw(layout.scenario_id)["zones"]["factory_floor"]["area"]
    (left, top), (right, bottom) = area["left_top"], area["right_bottom"]
    for p in layout.placements():
        x0, y0, x1, y1 = bbox(p)
        assert left <= x0 and x1 <= right and top <= y0 and y1 <= bottom, f"{p} outside zone"


def test_builder_matches_scenario_bindings_and_flow(layout):
    raw = scenario_raw(layout.scenario_id)
    source = raw["ports"]["workpiece_source"]
    sink = raw["ports"]["finished_goods"]
    assert tuple(source["binding"]["position"]) == layout.source_pos
    assert source["binding"]["prototype"] == "fisl-source-port"
    assert tuple(sink["binding"]["position"]) == layout.sink_pos
    assert sink["binding"]["prototype"] == "fisl-sink-port"
    # The machine chain must transform source material into sink material
    # through recipes whose materials all carry flow-basis coefficients.
    basis = set(raw["flows"]["workpiece_flow"]["basis"]["materials"])
    assert source["material"]["item"] in basis
    assert sink["material"]["item"] in basis
    recipes = [recipe for _x, _proto, recipe in layout.machines]
    assert recipes == RECIPE_CHAIN[: len(recipes)]


def test_flow_direction_is_monotonic_west_to_east(layout):
    placements = layout.placements()
    belts = [p for p in placements if p.name == "transport-belt"]
    assert all(p.direction == "east" for p in belts)
    inserters = [p for p in placements if p.name == "fast-inserter"]
    assert all(p.direction == "west" for p in inserters)
    machine_xs = [x for x, _proto, _r in layout.machines]
    assert machine_xs == sorted(machine_xs)
    assert layout.source_pos[0] < machine_xs[0] and machine_xs[-1] < layout.sink_pos[0]


def test_lab4_constraint_is_the_middle_machine():
    # Craft seconds = recipe energy / crafting speed. The Lab 4 design
    # premise: the slowest stage is M2, flanked by faster stages (blocked
    # above, starved below).
    speeds = {"assembling-machine-1": 0.5, "assembling-machine-2": 0.75, "assembling-machine-3": 1.25}
    recipe_seconds = {"fisl-machine-workpiece": 2.0, "fisl-inspect-workpiece": 1.0, "fisl-finish-workpiece": 1.0}
    craft_times = [
        recipe_seconds[recipe] / speeds[proto]
        for _x, proto, recipe in LAYOUTS["fp-04-starvation-blocking"].machines
    ]
    assert craft_times[1] == max(craft_times), craft_times
    assert craft_times[0] < craft_times[1] and craft_times[2] < craft_times[1]


def test_lab4_toolbox_supports_both_reference_solutions():
    toolbox = LAYOUTS["fp-04-starvation-blocking"].toolbox_items
    assert toolbox.get("wooden-chest", 0) >= 1        # solution A buffer
    assert toolbox.get("fast-inserter", 0) >= 2       # solution A splice
    assert toolbox.get("assembling-machine-3", 0) >= 1  # solution B upgrade


def test_commands_are_transmission_safe(layout):
    commands = placement_commands(layout)
    assert len(commands) >= 3  # preamble, >=1 batch, epilogue
    for command in commands:
        assert len(command) < 3800, f"command too long ({len(command)})"
        assert "--" not in command, "Lua comments break single-line transmission"
        assert "rcon.print" in command  # every command acknowledges


def test_freeplay_neutralization_command():
    assert "--" not in NEUTRALIZE_FREEPLAY_LUA
    assert len(NEUTRALIZE_FREEPLAY_LUA) < 3800
    for call in ("set_skip_intro", "set_disable_crashsite", "set_created_items", "set_respawn_items"):
        assert call in NEUTRALIZE_FREEPLAY_LUA
    assert "rcon.print" in NEUTRALIZE_FREEPLAY_LUA
