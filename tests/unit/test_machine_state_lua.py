"""Lupa tests for the runtime production-state adapter (fisl/machine_state.lua):
run-length span encoding over a scripted machine, coverage handling when the
entity disappears, and the summary cross-check accumulators. `game`,
`defines`, and `storage` are stubbed; the pure classifier itself is covered
by test_classify_lua.py."""

import json
from pathlib import Path

import pytest

lupa = pytest.importorskip("lupa")

CORE = Path(__file__).resolve().parents[2] / "factorio" / "fisl-core"


def _lua_to_py(value):
    if not isinstance(value, lupa.lua55.LuaRuntime) and hasattr(value, "keys"):
        keys = list(value.keys())
        if keys and all(isinstance(k, int) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
            return [_lua_to_py(value[k]) for k in sorted(keys)]
        return {str(k): _lua_to_py(value[k]) for k in keys}
    return value


@pytest.fixture()
def lua():
    runtime = lupa.LuaRuntime()
    runtime.execute(f'package.path = "{CORE}/?.lua;" .. package.path')
    # Stand-in for Factorio's helpers.table_to_json (util.json_encode).
    runtime.execute("helpers = {}")
    runtime.globals()["helpers"]["table_to_json"] = lambda tbl: json.dumps(_lua_to_py(tbl))
    runtime.execute(
        """
        storage = {}
        defines = { entity_status = {
          working = 1, item_ingredient_shortage = 2, no_power = 3, full_output = 4,
        } }
        entities = {}
        game = {
          tick = 0,
          get_entity_by_unit_number = function(n) return entities[n] end,
        }
        local state = require("fisl.state")
        MS = require("fisl.machine_state")
        local s = state.get()
        s.machine_state = {
          machine_state = {
            adapter = "crafting_machine",
            classifier_version = "crafting_machine/1",
            entity_set = "line_machines",
            machines = { [7] = {
              unit_number = 7, prototype = "assembling-machine-1",
              position = { x = 0.5, y = 0.5 },
              prev = nil, span = nil, state_ticks = {}, coverage_missing_ticks = 0,
            } },
            order = { 7 },
            last_classified_tick = nil,
          },
        }
        function set_machine(status_name, progress, finished)
          entities[7] = {
            valid = true,
            status = defines.entity_status[status_name],
            get_recipe = function() return { name = "fisl-machine-workpiece" } end,
            is_crafting = function() return true end,
            crafting_progress = progress,
            products_finished = finished,
          }
        end
        function drop_machine() entities[7] = nil end
        function checkpoint(tick) MS.checkpoint(nil, tick) end
        function flush(tick) MS.flush_spans(tick) end
        function summary_json()
          return require("fisl.util").json_encode(MS.summary())
        end
        function buffered_records()
          local s = require("fisl.state").get()
          return "[" .. table.concat(s.telemetry.buffer, ",") .. "]"
        end
        """
    )
    return runtime


def emitted_spans(lua):
    records = json.loads(lua.eval("buffered_records()"))
    return [r for r in records if r["type"] == "machine_state_span"]


def test_run_length_spans_and_coverage(lua):
    # Boundaries 0..5: progressing (products_finished advances), working.
    for tick in range(0, 6):
        lua.eval(f'set_machine("working", 0.5, {tick})')
        lua.eval(f"checkpoint({tick})")
    # Boundaries 6..8: stalled with an ingredient shortage.
    for tick in range(6, 9):
        lua.eval('set_machine("item_ingredient_shortage", 0.5, 5)')
        lua.eval(f"checkpoint({tick})")
    # Boundaries 9..10: the entity is gone -> missing coverage, not idle.
    for tick in range(9, 11):
        lua.eval("drop_machine()")
        lua.eval(f"checkpoint({tick})")
    lua.eval("flush(10)")

    spans = emitted_spans(lua)
    assert [(s["from_tick"], s["to_tick"], s["headline"]) for s in spans] == [
        (0, 5, "productive"),
        (5, 8, "starved"),
        (8, 10, "coverage_missing"),
    ]
    starved = spans[1]
    assert starved["cause"] == "input_shortage"
    assert starved["raw_status"] == "item_ingredient_shortage"
    assert starved["mapped"] is True
    # Spans partition [0, 10) exactly: half-open, adjacent, no gaps.
    assert all(s["metric"] == "machine_state" and s["unit_number"] == 7 for s in spans)
    for left, right in zip(spans, spans[1:]):
        assert left["to_tick"] == right["from_tick"]


def test_summary_accumulators_match_spans(lua):
    for tick in range(0, 4):
        lua.eval(f'set_machine("working", 0.1, {tick})')
        lua.eval(f"checkpoint({tick})")
    for tick in range(4, 6):
        lua.eval('set_machine("full_output", 0.9, 3)')
        lua.eval(f"checkpoint({tick})")
    lua.eval("flush(5)")

    summary = json.loads(lua.eval("summary_json()"))["machine_state"]
    assert summary["machine_count"] == 1
    assert summary["membership_resolution"] == "static_at_ready"
    # Interval [3,4) is productive too: crafting_progress advanced 0.1 -> 0.9
    # across that boundary even though the status flipped to full_output.
    assert summary["pooled_state_ticks"] == {"productive": 4, "blocked": 1}
    assert summary["coverage_missing_ticks"] == 0
    assert summary["last_classified_tick"] == 5


def test_abort_flush_closes_at_last_classified_boundary(lua):
    for tick in range(0, 3):
        lua.eval(f'set_machine("working", 0.5, {tick})')
        lua.eval(f"checkpoint({tick})")
    # Abort: flush with nil end tick -> spans end at the last classified
    # boundary (2), not at some invented future tick.
    lua.eval("flush(nil)")
    spans = emitted_spans(lua)
    assert [(s["from_tick"], s["to_tick"], s["headline"]) for s in spans] == [
        (0, 2, "productive"),
    ]
