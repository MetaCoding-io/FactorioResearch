"""Sanity tests for the photo-session shot lists (fisl snap)."""

from pathlib import Path

import pytest
import yaml

from fisl.controller.snapshot import SHOT_SETS, _take_screenshot_lua

REPO = Path(__file__).resolve().parents[2]

LAB_DIRS = {
    "fp-03-littles-law": ("fp03-littles-law", "lab-03"),
    "fp-04-starvation-blocking": ("fp04-starvation-blocking", "lab-04"),
}


@pytest.mark.parametrize("scenario_id", sorted(SHOT_SETS))
def test_shots_match_capture_list(scenario_id):
    _, images_dir = LAB_DIRS[scenario_id]
    capture_readme = (REPO / f"course/images/{images_dir}/README.md").read_text()
    for shot in SHOT_SETS[scenario_id]:
        assert shot.filename in capture_readme, f"{shot.filename} missing from capture list"


@pytest.mark.parametrize("scenario_id", sorted(SHOT_SETS))
def test_shot_positions_inside_lab_zone(scenario_id):
    scenario_dir, _ = LAB_DIRS[scenario_id]
    raw = yaml.safe_load(
        (REPO / f"scenarios/factory-physics/{scenario_dir}/scenario.yaml").read_text()
    )
    area = raw["zones"]["factory_floor"]["area"]
    (left, top), (right, bottom) = area["left_top"], area["right_bottom"]
    for shot in SHOT_SETS[scenario_id]:
        if shot.position is not None:
            x, y = shot.position
            assert left <= x <= right and top <= y <= bottom, shot.filename


@pytest.mark.parametrize("scenario_id", sorted(SHOT_SETS))
def test_shot_solutions_exist(scenario_id):
    scenario_dir, _ = LAB_DIRS[scenario_id]
    for shot in SHOT_SETS[scenario_id]:
        if shot.solution is not None:
            path = REPO / f"scenarios/factory-physics/{scenario_dir}/solutions/{shot.solution}"
            assert path.is_dir(), f"{shot.filename} references unknown solution {shot.solution}"


def test_screenshot_lua_is_transmission_safe():
    for shots in SHOT_SETS.values():
        for shot in shots:
            command = _take_screenshot_lua(shot)
            assert "--" not in command
            assert "\n" not in command
            assert "rcon.print" in command
            assert shot.filename in command
