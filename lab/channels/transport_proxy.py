"""One-shot LOOPBACK TCP faults for the disposable .NET/PostgreSQL channel fixture.

This is REAL local socket transport (not a modeled event trace) but NOT an
Ethernet/WAN partition, a production proxy, issuer/ATM hardware, ISO 8583,
a security boundary or permission to move money. It never opens a non-loopback
connection, never accepts a remote bind address, and never persists credentials
or financial HTTP payloads. It forwards at most ONE POST /transfer request.
"""
from __future__ import annotations

import hashlib
import os
import socket
import struct
import threading
import time


MODES = {"drop_before_forward", "drop_after_upstream_reply", "delay_after_upstream_reply", "hold_until_recovery"}


def _rst(conn):
    """Abort the one accepted TCP client without sending a synthetic HTTP reply."""
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    conn.close()


class OneShotTransportFault:
    def __init__(self, upstream_port: int, mode: str, delay_seconds: float = 0):
        if os.environ.get("CHANNELS_DISPOSABLE") != "YES":
            raise RuntimeError("Disposable channels fixture not authorized")
        if type(upstream_port) is not int or not 55444 <= upstream_port <= 55463:
            raise ValueError("Target must be the bounded disposable .NET loopback port")
        if mode not in MODES:
            raise ValueError("Unknown one-shot transport fault mode")
        if mode == "delay_after_upstream_reply":
            if not 0.5 <= delay_seconds <= 2.0:
                raise ValueError("Delay must be bounded 0.5..2.0 s")
        elif delay_seconds != 0:
            raise ValueError("Only delay mode accepts a delay")
        self.mode = mode
        self.upstream_port = upstream_port
        self.delay_seconds = delay_seconds
        self.reply_ready = threading.Event()
        self._release_reply = threading.Event()
        self.listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen.bind(("127.0.0.1", 0))
        self.listen.listen(1)
        self.listen.settimeout(8)
        self.port = self.listen.getsockname()[1]
        self.error = None
        self.result = {
            "mode": mode,
            "proxy": "127.0.0.1",
            "upstream": "127.0.0.1",
            "upstream_port": upstream_port,
            "source": "ACTUAL_LOOPBACK_TCP_SOCKET_NOT_KERNEL_OR_NETWORK_PARTITION",
            "request_forwarded": False,
            "upstream_connected": False,
            "upstream_response_status": None,
            "upstream_response_headers_seen": False,
            "downstream_response_bytes": 0,
            "request_sha256": None,
            "real_loopback_socket_used": False,
            "physical_link_partition_tested": False,
            "native_bank_issuer_tested": False,
            "physical_cash_device_tested": False,
            "production_approved": False,
        }
        self.thread = threading.Thread(target=self._serve, daemon=True,
                                       name="one-shot-channel-tcp-fault")
        self.started = False

    def __enter__(self):
        self.started = True
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if self.mode == "hold_until_recovery":
                self._release_reply.set()  # Cancel an unfinished controlled barrier safely.
            self.wait()
        finally:
            self.listen.close()

    def wait_for_upstream_reply(self, timeout=5):
        if self.mode != "hold_until_recovery":
            raise RuntimeError("Only held-reply mode exposes a recovery barrier")
        if not self.reply_ready.wait(timeout=timeout):
            raise TimeoutError("Upstream did not confirm original response within bound")
        return dict(self.result)

    def release_held_reply(self):
        if self.mode != "hold_until_recovery":
            raise RuntimeError("Not a held reply")
        if not self.reply_ready.is_set():
            raise RuntimeError("Cannot release a reply before upstream response")
        self.result["release_signalled_monotonic_ns"] = time.monotonic_ns()
        self._release_reply.set()

    def wait(self):
        if not self.started:
            raise RuntimeError("Proxy was not started")
        self.thread.join(timeout=9)
        if self.thread.is_alive():
            self.listen.close()
            raise TimeoutError("One-shot proxy did not finish within safety budget")
        if self.error is not None:
            raise RuntimeError("One-shot TCP failure fixture aborted") from self.error
        return dict(self.result)

    @staticmethod
    def _read_request(conn):
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                raise ValueError("Client disconnected before HTTP headers")
            data += chunk
            if len(data) > 65536:
                raise ValueError("Request headers too large")
        header, body = data.split(b"\r\n\r\n", 1)
        lines = header.split(b"\r\n")
        if lines[0] != b"POST /transfer HTTP/1.1":
            raise ValueError("Only disposable POST /transfer may pass proxy")
        headers = {}
        for line in lines[1:]:
            if b":" not in line:
                raise ValueError("Malformed HTTP header")
            key, value = line.split(b":", 1)
            key = key.strip().lower()
            if key in headers:
                raise ValueError("Duplicate HTTP header")
            headers[key] = value.strip()
        if b"transfer-encoding" in headers or b"expect" in headers:
            raise ValueError("Streaming requests are unsupported")
        if b"content-length" not in headers:
            raise ValueError("Explicit Content-Length required")
        try:
            length = int(headers[b"content-length"])
        except ValueError as error:
            raise ValueError("Invalid Content-Length") from error
        if not 1 <= length <= 8192 or len(body) > length:
            raise ValueError("Bounded exact request body required")
        while len(body) < length:
            chunk = conn.recv(length - len(body))
            if not chunk:
                raise ValueError("Request body truncated")
            body += chunk
        return header + b"\r\n\r\n" + body

    @staticmethod
    def _read_upstream_headers(conn):
        first = b""
        while b"\r\n\r\n" not in first:
            chunk = conn.recv(4096)
            if not chunk:
                raise RuntimeError("Upstream closed without HTTP response headers")
            first += chunk
            if len(first) > 65536:
                raise RuntimeError("Upstream HTTP response headers too large")
        status_line = first.split(b"\r\n", 1)[0]
        if not status_line.startswith(b"HTTP/1.1 200 "):
            raise RuntimeError("Expected successful owner response before injected loss")
        return first

    def _serve(self):
        conn = None
        try:
            conn, peer = self.listen.accept()
            if peer[0] != "127.0.0.1":
                raise RuntimeError("Non-loopback client refused")
            conn.settimeout(5)
            self.result["real_loopback_socket_used"] = True
            original = self._read_request(conn)
            self.result["request_sha256"] = hashlib.sha256(original).hexdigest()
            self.result["request_bytes"] = len(original)
            if self.mode == "drop_before_forward":
                # No upstream socket or original application request exists.
                _rst(conn)
                conn = None
                return
            with socket.create_connection(("127.0.0.1", self.upstream_port),
                                          timeout=5) as upstream:
                self.result["upstream_connected"] = True
                upstream.settimeout(5)
                upstream.sendall(original)
                self.result["request_forwarded"] = True
                first = self._read_upstream_headers(upstream)
                self.result["upstream_response_headers_seen"] = True
                self.result["upstream_response_status"] = 200
                self.result["upstream_response_initial_bytes"] = len(first)
                self.result["upstream_reply_seen_monotonic_ns"] = time.monotonic_ns()
                if self.mode == "hold_until_recovery":
                    self.reply_ready.set()
                    if not self._release_reply.wait(timeout=7):
                        raise TimeoutError("Held reply not released within safety budget")
                    self.result["response_release_monotonic_ns"] = time.monotonic_ns()
                # In Program.cs this response is produced AFTER the DB COMMIT,
                # which the independent SQL snapshot must verify separately.
                if self.mode == "drop_after_upstream_reply":
                    _rst(conn)
                    conn = None
                    return
                time.sleep(self.delay_seconds)
                self.result["delay_seconds"] = self.delay_seconds
                try:
                    count = conn.send(first)
                    self.result["downstream_response_bytes"] = count
                except OSError:
                    # Client timeout/closed before the delayed response.
                    self.result["downstream_write_failed_after_client_timeout"] = True
        except BaseException as error:
            self.error = error
        finally:
            if conn is not None:
                try:
                    conn.close()
                except OSError:
                    pass
            try:
                self.listen.close()
            except OSError:
                pass
