"""Pure-logic tests for fisl-core Lua modules, run via lupa (PRD §29.2).

These do not substitute for Factorio integration fixtures; they cover the
Factorio-independent arithmetic (CRC32 transfer verification, rational
schedule accumulation) and syntax-check every shipped Lua file.
"""

import zlib
from pathlib import Path

import pytest

lupa = pytest.importorskip("lupa")

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "factorio" / "fisl-core"

BIT32_SHIM = """
bit32 = {
  band = function(a, b) return a & b end,
  bxor = function(a, b) return a ~ b end,
  rshift = function(a, n) return a >> n end,
}
"""


def make_runtime():
    lua = lupa.LuaRuntime()
    lua.execute(BIT32_SHIM)
    lua.execute(f'package.path = "{CORE}/?.lua;" .. package.path')
    return lua


def test_all_lua_files_compile():
    lua = lupa.LuaRuntime()
    failures = []
    for path in sorted(REPO.glob("factorio/**/*.lua")):
        check = lua.eval(f'(function() local f, err = loadfile("{path}") return err end)()')
        if check is not None:
            failures.append(f"{path.relative_to(REPO)}: {check}")
    assert not failures, "\n".join(failures)


def test_crc32_matches_zlib():
    lua = make_runtime()
    crc32 = lua.eval('(require("fisl.util")).crc32')
    for sample in [b"", b"hello", b'{"resolved_scenario":{"spec":"fisl/v1"}}', bytes(range(256))]:
        assert crc32(sample) == zlib.crc32(sample), sample


def test_constant_schedule_exact_accumulation():
    lua = make_runtime()
    schedules = lua.eval('(require("fisl.schedules"))')
    # 75/min == 1 per 48 ticks: over exactly one simulated minute the release
    # total must be exactly 75 with zero drift.
    sched = schedules.new_constant(1, 48)
    total = 0
    for _ in range(3600):
        total += schedules.advance(sched)
    assert total == 75
    # And over 10 more minutes, still exact.
    for _ in range(10 * 3600):
        total += schedules.advance(sched)
    assert total == 75 * 11


def test_constant_schedule_releases_are_spread():
    lua = make_runtime()
    schedules = lua.eval('(require("fisl.schedules"))')
    sched = schedules.new_constant(1, 60)  # 60/min == 1/s
    releases = [schedules.advance(sched) for _ in range(180)]
    assert sum(releases) == 3
    assert max(releases) == 1  # never bursts


def test_contents_count_handles_dict_and_array_shapes():
    lua = make_runtime()
    lua.execute(
        """
        local util = require("fisl.util")
        function count_dict()
          return util.contents_count({["iron-plate"] = 7}, "iron-plate")
        end
        function count_array()
          return util.contents_count(
            {{name = "iron-plate", count = 3}, {name = "copper-plate", count = 9}},
            "iron-plate")
        end
        function count_missing()
          return util.contents_count({{name = "copper-plate", count = 9}}, "iron-plate")
        end
        """
    )
    assert lua.eval("count_dict()") == 7
    assert lua.eval("count_array()") == 3
    assert lua.eval("count_missing()") == 0
