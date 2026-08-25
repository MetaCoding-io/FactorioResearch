"""Pure-logic tests for the Lab 3 baseline builder: layout geometry,
scenario consistency, and RCON command constraints. The actual construction
and verification run against real Factorio via `fisl build-baseline`."""

from pathlib import Path

import yaml

from fisl.controller.baseline_builder import (
    EXPECTED_COUNTS,
    MACHINES,
    SINK_POS,
    SOURCE_POS,
    lab3_placements,
    placement_commands,
)

SCENARIO_YAML = (
    Path(__file__).resolve().parents[2]
    / "scenarios/factory-physics/fp03-littles-law/scenario.yaml"
)

# Entity footprint sizes (tiles) for overlap checking.
SIZES = {
    "assembling-machine-1": 3,
    "substation": 2,
    "solar-panel": 3,
    "fisl-source-port": 1,
    "fisl-sink-port": 1,
    "transport-belt": 1,
    "fast-inserter": 1,
    "steel-chest": 1,
}


def bbox(placement):
    half = SIZES[placement.name] / 2.0
    return (placement.x - half, placement.y - half, placement.x + half, placement.y + half)


def test_no_overlapping_footprints():
    placements = lab3_placements()
    boxes = [(p, bbox(p)) for p in placements]
    for i, (pa, a) in enumerate(boxes):
        for pb, b in boxes[i + 1 :]:
            overlap = a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
            assert not overlap, f"{pa} overlaps {pb}"


def test_entity_counts_match_expected():
    placements = lab3_placements()
    counts = {}
    for p in placements:
        counts[p.name] = counts.get(p.name, 0) + 1
    assert counts == EXPECTED_COUNTS


def test_everything_inside_zone_and_line_inside_system():
    raw = yaml.safe_load(SCENARIO_YAML.read_text())
    area = raw["zones"]["factory_floor"]["area"]
    (left, top), (right, bottom) = area["left_top"], area["right_bottom"]
    for p in lab3_placements():
        x0, y0, x1, y1 = bbox(p)
        assert left <= x0 and x1 <= right and top <= y0 and y1 <= bottom, f"{p} outside zone"


def test_builder_matches_scenario_bindings_and_flow():
    raw = yaml.safe_load(SCENARIO_YAML.read_text())
    source = raw["ports"]["workpiece_source"]
    sink = raw["ports"]["finished_goods"]
    assert tuple(source["binding"]["position"]) == SOURCE_POS
    assert source["binding"]["prototype"] == "fisl-source-port"
    assert tuple(sink["binding"]["position"]) == SINK_POS
    assert sink["binding"]["prototype"] == "fisl-sink-port"
    # The machine chain must transform source material into sink material
    # through recipes whose materials all carry flow-basis coefficients.
    basis = set(raw["flows"]["workpiece_flow"]["basis"]["materials"])
    assert source["material"]["item"] in basis
    assert sink["material"]["item"] in basis
    assert [recipe for _x, recipe in MACHINES] == [
        "fisl-machine-workpiece", "fisl-inspect-workpiece", "fisl-finish-workpiece",
    ]


def test_flow_direction_is_monotonic_west_to_east():
    placements = lab3_placements()
    belts = [p for p in placements if p.name == "transport-belt"]
    assert all(p.direction == "east" for p in belts)
    inserters = [p for p in placements if p.name == "fast-inserter"]
    assert all(p.direction == "west" for p in inserters)
    machine_xs = [x for x, _r in MACHINES]
    assert machine_xs == sorted(machine_xs)
    assert SOURCE_POS[0] < machine_xs[0] and machine_xs[-1] < SINK_POS[0]


def test_commands_are_transmission_safe():
    commands = placement_commands(lab3_placements())
    assert len(commands) >= 3  # preamble, >=1 batch, epilogue
    for command in commands:
        assert len(command) < 3800, f"command too long ({len(command)})"
        assert "--" not in command, "Lua comments break single-line transmission"
        assert "rcon.print" in command  # every command acknowledges
