"""RCON client framing test against an in-process fake Source-RCON server."""

import socket
import struct
import threading

import pytest

from fisl.controller.rcon import RconClient, RconError

PASSWORD = "sekrit"


def run_fake_server(server_sock: socket.socket, responses: list[str]):
    connection, _addr = server_sock.accept()
    with connection:
        def read_packet():
            size = struct.unpack("<i", connection.recv(4))[0]
            payload = b""
            while len(payload) < size:
                payload += connection.recv(size - len(payload))
            request_id, packet_type = struct.unpack("<ii", payload[:8])
            return request_id, packet_type, payload[8:-2]

        def send_packet(request_id, packet_type, body=b""):
            payload = struct.pack("<ii", request_id, packet_type) + body + b"\x00\x00"
            connection.sendall(struct.pack("<i", len(payload)) + payload)

        request_id, packet_type, body = read_packet()
        assert packet_type == 3
        if body.decode() == PASSWORD:
            send_packet(request_id, 2)
        else:
            send_packet(-1, 2)
            return
        for response in responses:
            request_id, packet_type, _body = read_packet()
            assert packet_type == 2
            send_packet(request_id, 0, response.encode())


@pytest.fixture()
def fake_server():
    server_sock = socket.socket()
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]
    yield server_sock, port
    server_sock.close()


def test_auth_and_command(fake_server):
    server_sock, port = fake_server
    thread = threading.Thread(target=run_fake_server, args=(server_sock, ['{"ok":true}']), daemon=True)
    thread.start()
    client = RconClient("127.0.0.1", port, PASSWORD)
    assert client.command("/silent-command rcon.print('x')") == '{"ok":true}'
    client.close()
    thread.join(timeout=2)


def test_bad_password_raises(fake_server):
    server_sock, port = fake_server
    thread = threading.Thread(target=run_fake_server, args=(server_sock, []), daemon=True)
    thread.start()
    with pytest.raises(RconError):
        RconClient("127.0.0.1", port, "wrong")
    thread.join(timeout=2)
