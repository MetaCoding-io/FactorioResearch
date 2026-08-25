"""One-workpiece vertical-slice fixture (RUNTIME_VALIDATION.md 'First
validation fixture').

Builds, against a real Factorio server:

    fisl-source-port -> inserter -> belt x3 -> inserter
        -> assembling-machine-1 (fisl-machine-workpiece, 1:1)
        -> inserter -> belt x2 -> inserter -> fisl-sink-port

Inserter pickup/drop positions are set explicitly via
LuaEntity.pickup_position / drop_position so the fixture does not depend on
direction-placement conventions.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from fisl.controller.process import FactorioServer, locate_repo_mods
from fisl.controller.protocol import FislProtocol
from fisl.scenario.compiler import compile_author_scenario, validate_author_dict

MAP_GEN_SETTINGS = {
    "width": 192,
    "height": 96,
    "seed": 424242,
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

# Coordinates of the line (y = 0.5 row). The zone comfortably contains it.
SOURCE_POS = (-8.5, 0.5)
SINK_POS = (9.5, 0.5)

BOOTSTRAP_LUA = r"""
local surface = game.surfaces["nauvis"]
surface.always_day = true
for _, entity in pairs(surface.find_entities_filtered{area = {{-30, -15}, {30, 15}}}) do
  if entity.type ~= "character" then entity.destroy() end
end
local function make(name, x, y)
  return surface.create_entity{name = name, position = {x, y}, force = "player", raise_built = false}
end
local function inserter(x, y, pick_x, pick_y, drop_x, drop_y)
  local e = make("fast-inserter", x, y)
  e.pickup_position = {pick_x, pick_y}
  e.drop_position = {drop_x, drop_y}
  return e
end
-- power
local eei = make("electric-energy-interface", -3.0, -4.0)
eei.power_production = 100000000
eei.electric_buffer_size = 100000000
make("substation", 0.0, -4.0)
-- apparatus + line
make("fisl-source-port", %(source_x)s, %(source_y)s)
inserter(-7.5, 0.5, %(source_x)s, %(source_y)s, -6.5, 0.5)
for x = -6, -4 do
  local belt = surface.create_entity{
    name = "transport-belt", position = {x + 0.5, 0.5},
    direction = defines.direction.east, force = "player", raise_built = false}
end
inserter(-2.5, 0.5, -3.5, 0.5, -0.5, 0.5)
local asm = make("assembling-machine-1", 0.5, 0.5)
asm.set_recipe("fisl-machine-workpiece")
inserter(2.5, 0.5, 0.5, 0.5, 3.5, 0.5)
for x = 3, 4 do
  surface.create_entity{
    name = "transport-belt", position = {x + 0.5, 0.5},
    direction = defines.direction.east, force = "player", raise_built = false}
end
inserter(5.5, 0.5, 4.5, 0.5, %(sink_x)s, %(sink_y)s)
make("fisl-sink-port", %(sink_x)s, %(sink_y)s)
rcon.print("bootstrap-ok")
""" % {
    "source_x": SOURCE_POS[0], "source_y": SOURCE_POS[1],
    "sink_x": SINK_POS[0], "sink_y": SINK_POS[1],
}


def fixture_scenario(
    *,
    warmup: str = "5s",
    measured: str = "60s",
    supply: dict | None = None,
    census_every: str = "60t",
) -> dict:
    """Author-form scenario dict for the fixture line."""
    supply = supply or {"mode": "replenish", "target": 20}
    return {
        "spec": "fisl/v1",
        "scenario": {
            "id": "rv-spike-fixture",
            "version": "0.1.0",
            "title": "Runtime validation spike fixture",
        },
        "factorio": {
            "version": {"minimum": "2.0.0"},
            "baseline_save": "baseline.zip",
            "required_mods": {"fisl-core": "compatible", "fisl-factory-physics": "compatible"},
        },
        "experiment": {
            "seed": 1,
            "time": {
                "game_speed": {"policy": "fixed", "value": 1.0},
                "pause_policy": "prohibited",
            },
            "phases": [
                {"id": "warmup", "duration": warmup},
                {"id": "measured", "duration": measured},
            ],
        },
        "zones": {
            "factory_floor": {
                "surface": "nauvis",
                "area": {"left_top": [-20, -10], "right_bottom": [20, 10]},
            }
        },
        "systems": {"factory": {"primary_zone": "factory_floor"}},
        "ports": {
            "workpiece_source": {
                "system": "factory",
                "direction": "source",
                "binding": {
                    "surface": "nauvis",
                    "position": list(SOURCE_POS),
                    "prototype": "fisl-source-port",
                },
                "material": {"item": "fisl-rough-workpiece"},
                "supply": supply,
            },
            "finished_goods": {
                "system": "factory",
                "direction": "sink",
                "binding": {
                    "surface": "nauvis",
                    "position": list(SINK_POS),
                    "prototype": "fisl-sink-port",
                },
                "material": {"item": "fisl-machined-workpiece"},
            },
        },
        "flows": {
            "workpiece_flow": {
                "system": "factory",
                "unit": "workpiece",
                "basis": {
                    "type": "conserved_work_unit",
                    "materials": {"fisl-rough-workpiece": 1, "fisl-machined-workpiece": 1},
                },
                "entry_ports": ["workpiece_source"],
                "completion_ports": ["finished_goods"],
            }
        },
        "metrics": {
            "line_wip": {
                "type": "wip",
                "flow": "workpiece_flow",
                "validation": {
                    "physical_census": {
                        "required": True,
                        "every": census_every,
                        "discrepancy_tolerance": 0,
                        "include_player_inventory": True,
                    }
                },
            },
            "average_wip": {
                "type": "aggregate",
                "source": "line_wip",
                "aggregation": "time_mean",
                "window": {"phase": "measured"},
            },
            "measured_throughput": {
                "type": "throughput",
                "flow": "workpiece_flow",
                "window": {"phase": "measured"},
            },
            "loaded_cycle_time": {
                "type": "cycle_time",
                "flow": "workpiece_flow",
                "method": "little_law_derived",
                "wip_metric": "average_wip",
                "throughput_metric": "measured_throughput",
            },
        },
    }


def create_baseline(factorio_bin: Path, workspace: Path) -> Path:
    """Create the pristine fixture baseline save (once per session)."""
    workspace.mkdir(parents=True, exist_ok=True)
    mgs_path = workspace / "map-gen-settings.json"
    mgs_path.write_text(json.dumps(MAP_GEN_SETTINGS))
    baseline = workspace / "baseline.zip"
    mods_dir = workspace / "create-mods"
    mods_dir.mkdir(exist_ok=True)
    import shutil

    mod_list = [{"name": "base", "enabled": True}]
    for mod_path in locate_repo_mods():
        target = mods_dir / mod_path.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(mod_path, target)
        mod_list.append({"name": mod_path.name, "enabled": True})
    (mods_dir / "mod-list.json").write_text(json.dumps({"mods": mod_list}))

    result = subprocess.run(
        [
            str(factorio_bin),
            "--create", str(baseline),
            "--map-gen-settings", str(mgs_path),
            "--mod-directory", str(mods_dir),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if not baseline.exists():
        raise RuntimeError(f"baseline creation failed:\n{result.stdout}\n{result.stderr}")
    return baseline


class SpikeSession:
    """A live server + bootstrapped fixture line + configured FISL run."""

    def __init__(self, factorio_bin: Path, workspace: Path, baseline: Path, scenario_dict: dict):
        self.scenario_dict = scenario_dict
        self.author = validate_author_dict(scenario_dict)
        self.resolved = compile_author_scenario(self.author)
        self.server = FactorioServer(factorio_bin, workspace, baseline)
        self.protocol: FislProtocol | None = None
        self.run_config: dict | None = None

    def __enter__(self) -> "SpikeSession":
        self.server.prepare()
        self.server.launch()
        rcon = self.server.wait_for_rcon()
        self.protocol = FislProtocol(rcon)
        response = rcon.command("/silent-command " + BOOTSTRAP_LUA.replace("\n", " "))
        assert "bootstrap-ok" in response, f"bootstrap failed: {response!r}"
        return self

    def configure(self, seed: int = 1) -> dict:
        from fisl.scenario.canonical import file_sha256
        from fisl.scenario.compiler import resolved_hash
        from fisl.scenario.runconfig import build_run_configuration, default_run_profile

        self.run_config = build_run_configuration(
            resolved_scenario_hash=resolved_hash(self.resolved),
            seed=seed,
            baseline_path="baseline.zip",
            baseline_sha256=file_sha256(str(self.server.baseline_save)),
            run_profile=default_run_profile("headless"),
        )
        return self.protocol.upload_configuration(
            {"run_configuration": self.run_config, "resolved_scenario": self.resolved}
        )

    def start(self, speed: float = 10.0) -> None:
        self.protocol.request_start()
        if speed != 1.0:
            self.protocol.set_game_speed(speed)

    def wait_done(self, timeout: float = 300.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.protocol.get_status()
            if status.get("lifecycle") in ("COMPLETED", "ABORTED"):
                return status
            time.sleep(0.5)
        raise TimeoutError(f"run did not finish; last status: {self.protocol.get_status()}")

    def telemetry_path(self) -> Path:
        return self.server.script_output / "fisl" / self.run_config["run_id"] / "telemetry.jsonl"

    def telemetry_records(self) -> list[dict]:
        return [
            json.loads(line)
            for line in self.telemetry_path().read_text().splitlines()
            if line.strip()
        ]

    def sc(self, lua: str) -> str:
        """Raw silent-command escape hatch for evidence probes."""
        return self.protocol.rcon.command("/silent-command " + lua)

    def __exit__(self, *_exc) -> None:
        self.server.stop()
