"""Controller <-> fisl-core protocol over RCON (ADR 0015 §3-§7).

Configuration transfer: canonical JSON -> zlib deflate -> base64 -> chunks.
Lua reassembles, decodes via helpers.decode_string, and verifies a CRC-32 of
the decoded JSON text before accepting the configuration.
"""

from __future__ import annotations

import base64
import json
import zlib
from typing import Any

from fisl.controller.rcon import RconClient

# Base64 alphabet is command-line safe; keep comfortably under console limits.
CHUNK_SIZE = 2000


class ProtocolError(Exception):
    pass


class FislProtocol:
    def __init__(self, rcon: RconClient):
        self.rcon = rcon

    def _call(self, function: str, *args: object) -> Any:
        rendered_args = "".join(", " + _lua_literal(arg) for arg in args)
        command = f'/silent-command rcon.print(remote.call("fisl", "{function}"{rendered_args}))'
        raw = self.rcon.command(command).strip()
        if not raw:
            raise ProtocolError(f"empty response from {function}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def get_protocol_version(self) -> int:
        return int(self._call("get_protocol_version"))

    def upload_configuration(self, document: dict) -> dict:
        """Chunked begin/append/commit transfer (ADR 0015 §6)."""
        from fisl.scenario.canonical import canonical_json_bytes

        payload = canonical_json_bytes(document)
        crc = zlib.crc32(payload)
        encoded = base64.b64encode(zlib.compress(payload)).decode("ascii")
        chunks = [encoded[i : i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)] or [""]

        run_id = document["run_configuration"]["run_id"]
        response = self._call("begin_configuration", run_id, crc, len(chunks))
        _expect_ok(response, "begin_configuration")
        for index, chunk in enumerate(chunks, start=1):
            response = self._call("append_configuration", index, chunk)
            _expect_ok(response, f"append_configuration[{index}]")
        response = self._call("commit_configuration")
        _expect_ok(response, "commit_configuration")
        return response

    def get_status(self) -> dict:
        return self._call("get_status")

    def get_summary(self) -> dict:
        response = self._call("get_summary")
        _expect_ok(response, "get_summary")
        return response["summary"]

    def request_start(self) -> None:
        _expect_ok(self._call("request_start"), "request_start")

    def request_abort(self, reason: str) -> None:
        self._call("request_abort", reason)

    def request_final_save(self, name: str) -> None:
        self._call("request_final_save", name)

    def set_game_speed(self, speed: float) -> None:
        """Operational control for headless fixtures only (ADR 0001 §4:
        game speed changes wall-clock rate, not experiment time)."""
        self.rcon.command(f"/silent-command game.speed = {speed}")


def _lua_literal(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    raise ProtocolError(f"cannot render {type(value)!r} as Lua literal")


def _expect_ok(response: Any, context: str) -> None:
    if not isinstance(response, dict) or response.get("ok") is not True:
        raise ProtocolError(f"{context} failed: {response!r}")
