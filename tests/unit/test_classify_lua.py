"""Lupa tests for the pure ADR 0007 classifier (fisl/classify.lua):
the mapping table, activity detection across craft completion/reset, and
headline precedence — including the brownout (productive + energy_limited)
and unknown-status (unclassified, never silent fallback) rules."""

from pathlib import Path

import pytest

lupa = pytest.importorskip("lupa")

CORE = Path(__file__).resolve().parents[2] / "factorio" / "fisl-core"


def make(lua, **fields):
    table = lua.table()
    for key, value in fields.items():
        table[key] = value
    return table


@pytest.fixture()
def lua():
    runtime = lupa.LuaRuntime()
    runtime.execute(f'package.path = "{CORE}/?.lua;" .. package.path')
    return runtime


@pytest.fixture()
def C(lua):
    return lua.eval('(require("fisl.classify"))')


def test_activity_progress_and_completion_wrap(lua, C):
    prev = make(lua, recipe="r", products_finished=5, crafting_progress=0.8)
    # progress within one craft
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.9)
    assert C.activity(prev, cur) == "progressing"
    # craft completed: progress wrapped DOWN but counter advanced (RV-006)
    cur = make(lua, recipe="r", products_finished=6, crafting_progress=0.1)
    assert C.activity(prev, cur) == "progressing"
    # stalled
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.8)
    assert C.activity(prev, cur) == "not_progressing"


def test_activity_unknown_cases(lua, C):
    prev = make(lua, recipe="r", products_finished=5, crafting_progress=0.8)
    assert C.activity(None, prev) == "unknown"                       # first sample
    cur = make(lua, recipe="other", products_finished=5, crafting_progress=0.1)
    assert C.activity(prev, cur) == "unknown"                        # recipe changed
    cur = make(lua, recipe="r", products_finished=4, crafting_progress=0.1)
    assert C.activity(prev, cur) == "unknown"                        # counter discontinuity
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.5)
    assert C.activity(prev, cur) == "unknown"                        # reset w/o completion


def test_headline_precedence_table(lua, C):
    def headline(activity, status):
        result = C.headline(activity, status)
        return result[0] if isinstance(result, tuple) else result

    cases = {
        ("not_progressing", "item_ingredient_shortage"): "starved",
        ("not_progressing", "fluid_ingredient_shortage"): "starved",
        ("not_progressing", "full_output"): "blocked",
        ("not_progressing", "waiting_for_space_in_destination"): "blocked",
        ("not_progressing", "no_power"): "unavailable",
        ("not_progressing", "low_power"): "unavailable",
        ("not_progressing", "frozen"): "unavailable",
        ("not_progressing", "disabled_by_script"): "disabled",
        ("not_progressing", "disabled_by_control_behavior"): "disabled",
        ("not_progressing", "no_recipe"): "idle_other",
        ("not_progressing", "working"): "idle_other",  # status/evidence disagree
    }
    for (activity, status), expected in cases.items():
        assert headline(activity, status) == expected, (activity, status)


def test_brownout_is_productive_with_energy_limited_condition(lua, C):
    prev = make(lua, recipe="r", products_finished=5, crafting_progress=0.10)
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.12)
    record = C.interval(prev, cur, "low_power")
    assert record["headline"] == "productive"
    assert record["cause"] == "energy_limited"
    assert record["activity"] == "progressing"


def test_unknown_status_is_unclassified_not_silent_fallback(lua, C):
    prev = make(lua, recipe="r", products_finished=5, crafting_progress=0.5)
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.5)
    record = C.interval(prev, cur, "some_future_status_name")
    assert record["headline"] == "unclassified"
    assert record["mapped"] is False


def test_missing_evidence_is_coverage_not_a_state(lua, C):
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.5)
    record = C.interval(None, cur, "item_ingredient_shortage")
    assert record["headline"] == "coverage_missing"
    assert record["activity"] == "unknown"


def test_starved_interval(lua, C):
    prev = make(lua, recipe="r", products_finished=5, crafting_progress=0.0)
    cur = make(lua, recipe="r", products_finished=5, crafting_progress=0.0)
    record = C.interval(prev, cur, "item_ingredient_shortage")
    assert record["headline"] == "starved"
    assert record["cause"] == "input_shortage"
