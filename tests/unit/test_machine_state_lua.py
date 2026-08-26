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
        game = { tick = 0 }
        CONFIG = { resolved = {
          zones = { factory_floor = { surface = "nauvis",
            area = { left_top = { -20, -10 }, right_bottom = { 20, 10 } } } },
          entity_sets = { line_machines = {
            zone = "factory_floor", types = { "assembling-machine" },
            prototypes = {}, exclude_roles = { "fisl_apparatus" },
          } },
        } }
        local function make_entity(unit_number)
          return {
            valid = true,
            unit_number = unit_number,
            name = "assembling-machine-1",
            type = "assembling-machine",
            position = { x = 0.5 + unit_number, y = 0.5 },
            get_recipe = function() return { name = "fisl-machine-workpiece" } end,
            is_crafting = function() return true end,
          }
        end
        entities = { [7] = make_entity(7) }
        local state = require("fisl.state")
        MS = require("fisl.machine_state")
        local s = state.get()
        s.machine_state = {
          machine_state = {
            adapter = "crafting_machine",
            classifier_version = "crafting_machine/1",
            entity_set = "line_machines",
            machines = { [7] = {
              entity = entities[7],
              unit_number = 7, prototype = "assembling-machine-1",
              position = { x = 0.5, y = 0.5 },
              joined_tick = 0, left_tick = nil,
              prev = nil, span = nil, state_ticks = {}, coverage_missing_ticks = 0,
            } },
            order = { 7 },
            last_classified_tick = nil,
          },
        }
        function set_machine(status_name, progress, finished, unit_number)
          local entity = entities[unit_number or 7]
          entity.valid = true
          entity.status = defines.entity_status[status_name]
          entity.crafting_progress = progress
          entity.products_finished = finished
        end
        function drop_machine(unit_number) entities[unit_number or 7].valid = false end
        function build_machine(unit_number, boundary_tick)
          entities[unit_number] = make_entity(unit_number)
          MS.ingest(CONFIG, { type = "entity_created", entity = entities[unit_number] }, boundary_tick)
        end
        function checkpoint(tick) MS.checkpoint(CONFIG, tick) end
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
    # Boundary 9: the entity is gone. The final PREPARED interval [8,9) is
    # missing coverage (never idle), then eligibility ends at 9 — later
    # boundaries contribute nothing (ADR 0016 §5-§6).
    for tick in range(9, 11):
        lua.eval("drop_machine()")
        lua.eval(f"checkpoint({tick})")
    lua.eval("flush(10)")

    spans = emitted_spans(lua)
    assert [(s["from_tick"], s["to_tick"], s["headline"]) for s in spans] == [
        (0, 5, "productive"),
        (5, 8, "starved"),
        (8, 9, "coverage_missing"),
    ]
    starved = spans[1]
    assert starved["cause"] == "input_shortage"
    assert starved["raw_status"] == "item_ingredient_shortage"
    assert starved["mapped"] is True
    # Spans partition the eligibility interval [0, 9): half-open, adjacent.
    assert all(s["metric"] == "machine_state" and s["unit_number"] == 7 for s in spans)
    for left, right in zip(spans, spans[1:]):
        assert left["to_tick"] == right["from_tick"]

    records = json.loads(lua.eval("buffered_records()"))
    removals = [r for r in records if r["type"] == "machine_state_membership_change"]
    assert [(r["change"], r["unit_number"], r["boundary_tick"]) for r in removals] == [
        ("removed", 7, 9),
    ]
    assert removals[0]["eligible_from_tick"] == 0


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
    assert summary["members_total"] == 1
    assert summary["membership_resolution"] == "dynamic_boundary"
    # Interval [3,4) is productive too: crafting_progress advanced 0.1 -> 0.9
    # across that boundary even though the status flipped to full_output.
    assert summary["pooled_state_ticks"] == {"productive": 4, "blocked": 1}
    assert summary["coverage_missing_ticks"] == 0
    assert summary["eligible_machine_ticks"] == 5
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


def test_mid_run_join_contributes_no_retroactive_history(lua):
    # Machine 7 runs from tick 0; machine 12 is built during [2,3) and its
    # created-event is drained at boundary 3 (ADR 0016 §4).
    for tick in range(0, 3):
        lua.eval(f'set_machine("working", 0.5, {tick})')
        lua.eval(f"checkpoint({tick})")
    lua.eval("build_machine(12, 3)")
    # Boundaries 3..7 (finalize samples the final boundary before flushing).
    for tick in range(3, 8):
        lua.eval(f'set_machine("working", 0.5, {tick})')
        lua.eval(f'set_machine("item_ingredient_shortage", 0.2, 0, 12)')
        lua.eval(f"checkpoint({tick})")
    lua.eval("flush(7)")

    records = json.loads(lua.eval("buffered_records()"))
    additions = [r for r in records if r["type"] == "machine_state_membership_change"]
    assert [(r["change"], r["unit_number"], r["boundary_tick"]) for r in additions] == [
        ("added", 12, 3),
    ]
    spans_12 = [s for s in emitted_spans(lua) if s["unit_number"] == 12]
    # Eligibility [3,7): first classified interval is [3,4) — no retroactive
    # unavailable/idle/coverage before the join (ADR 0016 §6).
    assert [(s["from_tick"], s["to_tick"], s["headline"]) for s in spans_12] == [
        (3, 7, "starved"),
    ]

    summary = json.loads(lua.eval("summary_json()"))["machine_state"]
    assert summary["machine_count"] == 2
    assert summary["members_total"] == 2
    # m7: 7 eligible intervals; m12: 4 (from boundary 3).
    assert summary["eligible_machine_ticks"] == 11
    assert summary["pooled_state_ticks"] == {"productive": 7, "starved": 4}


def test_ingest_ignores_non_matching_and_duplicate_entities(lua):
    lua.eval('set_machine("working", 0.5, 0)')
    lua.eval("checkpoint(0)")
    # Duplicate of an existing member: no new membership record.
    lua.execute('MS.ingest(CONFIG, { type = "entity_created", entity = entities[7] }, 2)')
    # Outside the zone: rejected by the selector.
    lua.execute(
        """
        local stray = { valid = true, unit_number = 99, name = "assembling-machine-1",
          type = "assembling-machine", position = { x = 50, y = 0.5 } }
        MS.ingest(CONFIG, { type = "entity_created", entity = stray }, 2)
        """
    )
    # Wrong type: rejected by the selector.
    lua.execute(
        """
        local belt = { valid = true, unit_number = 98, name = "transport-belt",
          type = "transport-belt", position = { x = 1.5, y = 0.5 } }
        MS.ingest(CONFIG, { type = "entity_created", entity = belt }, 2)
        """
    )
    records = json.loads(lua.eval("buffered_records()"))
    assert [r for r in records if r["type"] == "machine_state_membership_change"] == []
    summary = json.loads(lua.eval("summary_json()"))["machine_state"]
    assert summary["members_total"] == 1
