"""Factorio server process management (ADR 0015 §1-§2, FR-CTRL-003/004).

Each run gets an isolated workspace: the server's write-data directory is the
workspace itself (config.ini `write-data`), so saves, mods, logs, and
script-output are all run-scoped. The immutable baseline is copied, never
mutated. RCON binds loopback with a random per-run password.
"""

from __future__ import annotations

import secrets
import shutil
import socket
import subprocess
import time
from pathlib import Path


class ProcessError(Exception):
    pass


def find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def locate_repo_mods() -> list[Path]:
    repo = Path(__file__).resolve().parents[3]
    return [repo / "factorio" / "fisl-core", repo / "factorio" / "fisl-factory-physics"]


class FactorioServer:
    def __init__(
        self,
        factorio_bin: Path,
        workspace: Path,
        baseline_save: Path,
        *,
        extra_mods: list[Path] | None = None,
        rcon_port: int | None = None,
    ):
        self.factorio_bin = Path(factorio_bin)
        self.workspace = Path(workspace)
        self.baseline_save = Path(baseline_save)
        self.rcon_port = rcon_port or find_free_port()
        self.game_port = find_free_port()
        self.rcon_password = secrets.token_hex(16)
        self.extra_mods = extra_mods if extra_mods is not None else locate_repo_mods()
        self.process: subprocess.Popen | None = None
        self.log_path = self.workspace / "server.log"

    # -- workspace preparation ------------------------------------------------

    def prepare(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "saves").mkdir(exist_ok=True)
        mods_dir = self.workspace / "mods"
        mods_dir.mkdir(exist_ok=True)
        if not self.baseline_save.exists():
            raise ProcessError(f"baseline save missing: {self.baseline_save}")
        shutil.copyfile(self.baseline_save, self.workspace / "saves" / "run.zip")

        mod_list = [{"name": "base", "enabled": True}]
        for mod_path in self.extra_mods:
            target = mods_dir / mod_path.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(mod_path, target)
            mod_list.append({"name": mod_path.name, "enabled": True})
        import json

        (mods_dir / "mod-list.json").write_text(json.dumps({"mods": mod_list}, indent=2))

        # write-data = workspace keeps script-output/saves/logs run-scoped.
        data_dir = self.factorio_bin.resolve().parents[2] / "data"
        (self.workspace / "config.ini").write_text(
            "[path]\n"
            f"read-data={data_dir}\n"
            f"write-data={self.workspace}\n"
        )
        # ADR 0018 §2 / RV-011: zero connected players must not pause a
        # running experiment.
        (self.workspace / "server-settings.json").write_text(
            json.dumps(
                {
                    "name": "FISL run",
                    "description": "FISL controlled experiment",
                    "visibility": {"public": False, "lan": False},
                    "require_user_verification": False,
                    "max_players": 4,
                    "auto_pause": False,
                    "auto_pause_when_players_connect": False,
                },
                indent=2,
            )
        )

    # -- lifecycle ------------------------------------------------------------

    def launch(self) -> None:
        command = [
            str(self.factorio_bin),
            "--start-server", str(self.workspace / "saves" / "run.zip"),
            "--config", str(self.workspace / "config.ini"),
            "--mod-directory", str(self.workspace / "mods"),
            "--server-settings", str(self.workspace / "server-settings.json"),
            "--port", str(self.game_port),
            "--bind", "127.0.0.1",
            "--rcon-bind", f"127.0.0.1:{self.rcon_port}",
            "--rcon-password", self.rcon_password,
        ]
        log = open(self.log_path, "wb")
        self.process = subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT, cwd=self.workspace
        )

    def wait_for_rcon(self, timeout: float = 90.0):
        from fisl.controller.rcon import RconClient, RconError

        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                raise ProcessError(
                    f"Factorio exited early (code {self.process.returncode}); see {self.log_path}"
                )
            try:
                return RconClient("127.0.0.1", self.rcon_port, self.rcon_password)
            except (OSError, RconError) as exc:
                last_error = exc
                time.sleep(0.5)
        raise ProcessError(f"RCON not reachable within {timeout}s: {last_error}")

    def stop(self, timeout: float = 15.0) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
        self.process = None

    @property
    def script_output(self) -> Path:
        return self.workspace / "script-output"

    def __enter__(self) -> "FactorioServer":
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()
