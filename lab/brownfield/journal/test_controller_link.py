#!/usr/bin/env python3
"""Socket-only checks of the fault injector, not database acceptance evidence."""
import socket
import socketserver
import threading
import unittest

from controller_link import ControllerLink


class LinkTests(unittest.TestCase):
    def test_cut_closes_existing_stream_refuses_new_and_restores_forwarding(self):
        class Echo(socketserver.BaseRequestHandler):
            def handle(self):
                try:
                    while data := self.request.recv(64):
                        self.request.sendall(data)
                except OSError:
                    pass

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True

        with Server(("127.0.0.1", 0), Echo) as backend:
            worker = threading.Thread(target=backend.serve_forever, daemon=True)
            worker.start()
            try:
                with ControllerLink(0, backend.server_address[1]) as link:
                    address = link.server.server_address
                    with socket.create_connection(address, timeout=2) as client:
                        client.sendall(b"before")
                        self.assertEqual(client.recv(64), b"before")
                        event = link.cut()
                        self.assertEqual(event["activeConnections"], 1)
                        self.assertEqual(client.recv(64), b"")
                    with socket.create_connection(address, timeout=2) as denied:
                        self.assertEqual(denied.recv(64), b"")
                    link.restore()
                    with socket.create_connection(address, timeout=2) as client:
                        client.sendall(b"after")
                        self.assertEqual(client.recv(64), b"after")
                    self.assertGreater(link.forwarded, 0)
            finally:
                backend.shutdown()
                worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
