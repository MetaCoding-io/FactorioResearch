"""Run orchestration: FR-CTRL-003 happy path for interactive and headless runs.

    compile -> run workspace -> launch server -> negotiate protocol
    -> upload config -> READY -> start -> monitor -> collect -> summarize
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from fisl import COMPILER_VERSION
from fisl.controller.process import FactorioServer, ProcessError
from fisl.controller.protocol import FislProtocol, ProtocolError
from fisl.metrics.aggregation import compute_summary
from fisl.scenario.canonical import canonical_json_bytes, file_sha256
from fisl.scenario.compiler import (
    CompilationError,
    compile_author_scenario,
    load_author_yaml,
    resolved_hash,
)
from fisl.scenario.runconfig import (
    build_run_configuration,
    default_run_profile,
    reproducibility_fingerprint,
)


class RunError(Exception):
    pass


@dataclass
class RunResult:
    run_id: str
    run_dir: Path
    lifecycle: str


def execute_run(
    *,
    scenario_dir: Path,
    headless: bool,
    factorio_bin: Path | None,
    runs_dir: Path,
    run_ticks: int | None = None,
    headless_speed: float = 10.0,
    console: Console | None = None,
    seed: int | None = None,
) -> RunResult:
    console = console or Console()
    if factorio_bin is None:
        raise RunError("no Factorio binary: pass --factorio or set FACTORIO_BIN")
    factorio_bin = Path(factorio_bin)
    if not factorio_bin.exists():
        raise RunError(f"Factorio binary not found: {factorio_bin}")

    # 1. compile
    try:
        author = load_author_yaml(scenario_dir / "scenario.yaml")
        resolved = compile_author_scenario(author)
    except CompilationError as exc:
        raise RunError(str(exc)) from exc
    scenario_hash = resolved_hash(resolved)

    baseline = scenario_dir / resolved["factorio"]["baseline_save"]
    if not baseline.exists():
        raise RunError(f"baseline save missing: {baseline}")
    baseline_hash = file_sha256(str(baseline))

    # 2. run identity + workspace
    profile = default_run_profile("headless" if headless else "interactive")
    run_config = build_run_configuration(
        resolved_scenario_hash=scenario_hash,
        seed=seed if seed is not None else resolved["experiment"]["default_seed"],
        baseline_path=str(baseline.name),
        baseline_sha256=baseline_hash,
        run_profile=profile,
    )
    run_id = run_config["run_id"]
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    workspace = run_dir / "server"

    (run_dir / "scenario.resolved.json").write_bytes(canonical_json_bytes(resolved))
    (run_dir / "run-config.json").write_text(json.dumps(run_config, indent=2))

    manifest = {
        "run_id": run_id,
        "spec": resolved["spec"],
        "scenario": {
            "id": resolved["scenario"]["id"],
            "version": resolved["scenario"]["version"],
            "resolved_hash": scenario_hash,
        },
        "baseline": {"save": str(baseline.name), "sha256": baseline_hash},
        "software": {
            "compiler_version": COMPILER_VERSION,
            "fisl_core_version": _mod_version("fisl-core"),
            "fisl_factory_physics_version": _mod_version("fisl-factory-physics"),
        },
        "experiment_seed": run_config["experiment_seed"],
        "run_profile": profile,
        "status": "launching",
        "wall_clock": {"started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
    }
    _write_manifest(run_dir, manifest)

    server = FactorioServer(factorio_bin, workspace, baseline)
    console.print(f"Run {run_id}: preparing workspace…")
    server.prepare()
    console.print("Launching Factorio server…")
    server.launch()
    lifecycle = "ABORTED"
    try:
        rcon = server.wait_for_rcon()
        protocol = FislProtocol(rcon)

        # 3. protocol negotiation + config upload (ADR 0015 §13)
        version = protocol.get_protocol_version()
        if version != resolved["protocol_version"]:
            raise RunError(f"protocol mismatch: runtime={version} compiler={resolved['protocol_version']}")
        console.print("Uploading resolved configuration…")
        protocol.upload_configuration({"run_configuration": run_config, "resolved_scenario": resolved})
        status = protocol.get_status()
        if status.get("lifecycle") != "READY":
            raise RunError(f"runtime not READY after configuration: {status}")
        console.print("[green]READY[/green]")

        manifest["factorio_version"] = _server_factorio_version(server)
        manifest["reproducibility_fingerprint"] = reproducibility_fingerprint(
            resolved_scenario_hash=scenario_hash,
            seed=run_config["experiment_seed"],
            baseline_sha256=baseline_hash,
            factorio_version=manifest.get("factorio_version") or "unknown",
            fisl_versions={
                "compiler": COMPILER_VERSION,
                "fisl-core": manifest["software"]["fisl_core_version"],
            },
            mod_manifest={
                "fisl-core": manifest["software"]["fisl_core_version"],
                "fisl-factory-physics": manifest["software"]["fisl_factory_physics_version"],
            },
            run_profile=profile,
        )
        manifest["status"] = "ready"
        _write_manifest(run_dir, manifest)

        # 4. start
        if headless:
            protocol.request_start()
            if headless_speed != 1.0:
                protocol.set_game_speed(headless_speed)
                manifest["operational"] = {"headless_game_speed": headless_speed}
        else:
            console.print(
                f"Connect a Factorio client to [bold]localhost:{server.game_port}[/bold] "
                "and press Start Experiment in the FISL panel."
            )

        # 5. monitor until COMPLETED/ABORTED
        total_ticks = resolved["experiment"]["total_duration_ticks"]
        deadline = time.monotonic() + _monitor_timeout(total_ticks, headless, headless_speed)
        while True:
            status = protocol.get_status()
            lifecycle = status.get("lifecycle", "UNKNOWN")
            if lifecycle in ("COMPLETED", "ABORTED"):
                break
            if time.monotonic() > deadline:
                protocol.request_abort("controller_timeout")
                lifecycle = "ABORTED"
                break
            if run_ticks is not None and status.get("experiment_tick", 0) >= run_ticks:
                protocol.request_abort("controller_run_ticks_reached")
                lifecycle = "ABORTED"
                break
            time.sleep(1.0)
        console.print(f"Lifecycle: {lifecycle}")
        manifest["status"] = lifecycle.lower()
    except (ProcessError, ProtocolError) as exc:
        manifest["status"] = "failed"
        manifest["failure"] = str(exc)
        _write_manifest(run_dir, manifest)
        server.stop()
        raise RunError(str(exc)) from exc
    finally:
        server.stop()

    # 6. collect artifacts
    telemetry_src = server.script_output / "fisl" / run_id / "telemetry.jsonl"
    telemetry_dst = run_dir / "telemetry.jsonl"
    if telemetry_src.exists():
        shutil.copyfile(telemetry_src, telemetry_dst)
    else:
        manifest["warnings"] = ["no telemetry collected"]

    # 7. authoritative Python recomputation -> summary.json
    if telemetry_dst.exists():
        summary = compute_summary(resolved, run_config, telemetry_dst)
        summary["lifecycle"] = lifecycle
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    manifest["wall_clock"]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["artifacts"] = {
        path.name: file_sha256(str(path))
        for path in sorted(run_dir.iterdir())
        if path.is_file() and path.name != "manifest.json"
    }
    _write_manifest(run_dir, manifest)
    return RunResult(run_id=run_id, run_dir=run_dir, lifecycle=lifecycle)


def _monitor_timeout(total_ticks: int, headless: bool, speed: float) -> float:
    real_seconds = total_ticks / 60.0
    if headless:
        real_seconds = real_seconds / max(speed, 1.0)
        return real_seconds * 3 + 120
    return real_seconds * 2 + 1800  # generous: learner may take their time to press start


def _write_manifest(run_dir: Path, manifest: dict) -> None:
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def _mod_version(mod_name: str) -> str:
    info = Path(__file__).resolve().parents[3] / "factorio" / mod_name / "info.json"
    if info.exists():
        return json.loads(info.read_text())["version"]
    return "unknown"


def _server_factorio_version(server: FactorioServer) -> str | None:
    log = server.log_path
    if log.exists():
        for line in log.read_text(errors="replace").splitlines():
            if "Factorio" in line and "(build" in line:
                for token_index, token in enumerate(parts := line.split()):
                    if token == "Factorio" and token_index + 1 < len(parts):
                        return parts[token_index + 1]
    return None
