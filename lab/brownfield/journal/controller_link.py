#!/usr/bin/env python3
"""Test-only TCP link: cut active controller sockets, refuse reconnect, restore.

This injects a connection-loss fault, not packet blackholing, a directional
partition or independent physical failure domains. PostgreSQL bytes are opaque.
"""
from __future__ import annotations

import select
import socket
import socketserver
import threading
import time


class ControllerLink:
    def __init__(self, listen_port: int = 55440, backend_port: int = 55441):
        self.backend_port = backend_port
        self.lock = threading.Lock()
        self.blocked = False
        self.sockets: set[socket.socket] = set()
        self.events: list[dict] = []
        self.accepted = 0
        self.forwarded = 0
        owner = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                front = self.request
                back = None
                try:
                    with owner.lock:
                        if owner.blocked:
                            return
                        back = socket.create_connection(("127.0.0.1", owner.backend_port), timeout=3)
                        back.settimeout(None)
                        owner.sockets.update((front, back))
                        owner.accepted += 1
                    while True:
                        ready, _, _ = select.select([front, back], [], [], 0.1)
                        for source in ready:
                            packet = source.recv(65536)
                            if not packet:
                                return
                            (back if source is front else front).sendall(packet)
                            with owner.lock:
                                owner.forwarded += len(packet)
                except (OSError, ValueError):
                    # Cutting the link deliberately invalidates active sockets.
                    return
                finally:
                    with owner.lock:
                        owner.sockets.discard(front)
                        if back is not None:
                            owner.sockets.discard(back)
                    if back is not None:
                        back.close()

        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self.server = Server(("127.0.0.1", listen_port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def cut(self) -> dict:
        with self.lock:
            self.blocked = True
            active = list(self.sockets)
            event = {"event": "TCP_LINK_CUT", "monotonicNs": time.monotonic_ns(),
                     "activeConnections": len(active) // 2,
                     "acceptedConnections": self.accepted, "forwardedBytes": self.forwarded}
            self.events.append(event)
            for stream in active:
                try:
                    stream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                stream.close()
            return event

    def restore(self) -> None:
        with self.lock:
            self.blocked = False
            self.events.append({"event": "TCP_LINK_RESTORED", "monotonicNs": time.monotonic_ns()})

    def __exit__(self, *exc):
        self.cut()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
