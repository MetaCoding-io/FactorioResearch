"""Minimal Source-RCON client (PRD §35 allows an internal client).

Factorio implements the standard Source RCON framing:
  int32 little-endian size | int32 request id | int32 type | body \x00 | \x00
Auth type 3 (response 2), exec command type 2 (response 0).
"""

from __future__ import annotations

import socket
import struct

SERVERDATA_AUTH = 3
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_RESPONSE_VALUE = 0


class RconError(Exception):
    pass


class RconClient:
    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0):
        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._sock.settimeout(timeout)
        self._next_id = 0
        self._auth(password)

    def _send_packet(self, packet_type: int, body: bytes) -> int:
        self._next_id += 1
        request_id = self._next_id
        payload = struct.pack("<ii", request_id, packet_type) + body + b"\x00\x00"
        self._sock.sendall(struct.pack("<i", len(payload)) + payload)
        return request_id

    def _read_exact(self, count: int) -> bytes:
        chunks = []
        remaining = count
        while remaining > 0:
            chunk = self._sock.recv(remaining)
            if not chunk:
                raise RconError("connection closed by server")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _read_packet(self) -> tuple[int, int, bytes]:
        (size,) = struct.unpack("<i", self._read_exact(4))
        payload = self._read_exact(size)
        request_id, packet_type = struct.unpack("<ii", payload[:8])
        return request_id, packet_type, payload[8:-2]

    def _auth(self, password: str) -> None:
        self._send_packet(SERVERDATA_AUTH, password.encode("utf-8"))
        # Some servers send an empty RESPONSE_VALUE before AUTH_RESPONSE.
        for _ in range(2):
            request_id, packet_type, _body = self._read_packet()
            if packet_type == SERVERDATA_AUTH_RESPONSE:
                if request_id == -1:
                    raise RconError("RCON authentication failed")
                return
        raise RconError("no auth response from server")

    def command(self, text: str) -> str:
        self._send_packet(SERVERDATA_EXECCOMMAND, text.encode("utf-8"))
        _request_id, _packet_type, body = self._read_packet()
        return body.decode("utf-8", errors="replace")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def __enter__(self) -> "RconClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
