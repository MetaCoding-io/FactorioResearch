"""Sanity tests for the photo-session shot lists (fisl snap)."""

from pathlib import Path

from fisl.controller.snapshot import SHOT_SETS, _take_screenshot_lua

REPO = Path(__file__).resolve().parents[2]


def test_lab03_shots_match_capture_list():
    shots = SHOT_SETS["fp-03-littles-law"]
    filenames = {shot.filename for shot in shots}
    capture_readme = (REPO / "course/images/lab-03/README.md").read_text()
    for filename in filenames:
        assert filename in capture_readme, f"{filename} missing from capture list"


def test_shot_positions_inside_lab_zone():
    import yaml

    raw = yaml.safe_load(
        (REPO / "scenarios/factory-physics/fp03-littles-law/scenario.yaml").read_text()
    )
    area = raw["zones"]["factory_floor"]["area"]
    (left, top), (right, bottom) = area["left_top"], area["right_bottom"]
    for shot in SHOT_SETS["fp-03-littles-law"]:
        if shot.position is not None:
            x, y = shot.position
            assert left <= x <= right and top <= y <= bottom, shot.filename


def test_screenshot_lua_is_transmission_safe():
    for shots in SHOT_SETS.values():
        for shot in shots:
            command = _take_screenshot_lua(shot)
            assert "--" not in command
            assert "\n" not in command
            assert "rcon.print" in command
            assert shot.filename in command
