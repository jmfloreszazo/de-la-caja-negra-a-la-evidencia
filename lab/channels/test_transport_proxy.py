"""Offline negative controls for the disposable one-shot TCP fault injector.

No actual bank system, payment device, mainframe, HSM or network operator.
The integrated original .NET/PostgreSQL campaign is the separate real-socket
proof: these fast tests validate the proxy's refusal and byte handling.
"""
from __future__ import annotations

from contextlib import contextmanager
from http.client import HTTPException
import os
import socket
import unittest
import urllib.error
import urllib.request

from transport_proxy import OneShotTransportFault


@contextmanager
def raw_request(wire):
    client, target = socket.socketpair()
    target.settimeout(1)
    try:
        client.sendall(wire)
        client.shutdown(socket.SHUT_WR)
        yield target
    finally:
        client.close()
        target.close()


def request(method="POST", path="/transfer", headers=b"", body=b'{"safe":true}'):
    return (f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n".encode()
            + b"Connection: close\r\nContent-Length: "
            + str(len(body)).encode() + b"\r\n" + headers + b"\r\n" + body)


class OneShotTransportGuards(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get("CHANNELS_DISPOSABLE")
        os.environ["CHANNELS_DISPOSABLE"] = "YES"

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("CHANNELS_DISPOSABLE", None)
        else:
            os.environ["CHANNELS_DISPOSABLE"] = self.previous

    def test_01_disposable_guard_enforced(self):
        os.environ.pop("CHANNELS_DISPOSABLE")
        with self.assertRaises(RuntimeError):
            OneShotTransportFault(55444, "drop_before_forward")

    def test_02_nonlocal_or_external_port_refused(self):
        for port in (0, 443, 55443, 55464, 65000, None, True):
            with self.subTest(port=port), self.assertRaises(ValueError):
                OneShotTransportFault(port, "drop_before_forward")

    def test_03_unknown_mode_refused(self):
        with self.assertRaises(ValueError):
            OneShotTransportFault(55444, "rewrite_financial_request")

    def test_04_unbounded_or_wrong_delay_refused(self):
        for bad in (0, -1, 3, 99):
            with self.subTest(delay=bad), self.assertRaises(ValueError):
                OneShotTransportFault(55444, "delay_after_upstream_reply", bad)
        with self.assertRaises(ValueError):
            OneShotTransportFault(55444, "drop_after_upstream_reply", 1)

    def test_05_accepted_http_transfer_is_exact(self):
        wire = request()
        with raw_request(wire) as target:
            self.assertEqual(OneShotTransportFault._read_request(target), wire)

    def test_06_get_request_cannot_be_forwarded(self):
        with raw_request(request(method="GET")) as target:
            with self.assertRaises(ValueError):
                OneShotTransportFault._read_request(target)

    def test_07_other_financial_route_cannot_be_forwarded(self):
        with raw_request(request(path="/settle")) as target:
            with self.assertRaises(ValueError):
                OneShotTransportFault._read_request(target)

    def test_08_duplicate_content_length_refused(self):
        with raw_request(request(headers=b"Content-Length: 4\r\n")) as target:
            with self.assertRaises(ValueError):
                OneShotTransportFault._read_request(target)

    def test_09_streaming_request_refused(self):
        with raw_request(request(headers=b"Transfer-Encoding: chunked\r\n")) as target:
            with self.assertRaises(ValueError):
                OneShotTransportFault._read_request(target)

    def test_10_oversized_body_refused(self):
        wire = request(body=b"x" * 8193)
        with raw_request(wire) as target:
            with self.assertRaises(ValueError):
                OneShotTransportFault._read_request(target)

    def test_11_truncated_body_refused(self):
        wire = request()
        wire = wire.replace(b"Content-Length: 13\r\n", b"Content-Length: 17\r\n")
        with raw_request(wire) as target:
            with self.assertRaises(ValueError):
                OneShotTransportFault._read_request(target)

    def test_12_wrong_upstream_reply_status_refused(self):
        left, right = socket.socketpair()
        try:
            right.sendall(b"HTTP/1.1 409 Conflict\r\nContent-Length: 0\r\n\r\n")
            with self.assertRaises(RuntimeError):
                OneShotTransportFault._read_upstream_headers(left)
        finally:
            left.close()
            right.close()

    def test_13_real_local_tcp_drop_never_opens_upstream(self):
        with OneShotTransportFault(55444, "drop_before_forward") as proxy:
            req = urllib.request.Request(
                f"http://127.0.0.1:{proxy.port}/transfer",
                data=b'{"test":1}', headers={"Content-Type": "application/json"})
            with self.assertRaises((OSError, HTTPException, urllib.error.URLError)):
                urllib.request.urlopen(req, timeout=3)
            observed = proxy.wait()
        self.assertTrue(observed["real_loopback_socket_used"])
        self.assertFalse(observed["upstream_connected"])
        self.assertFalse(observed["request_forwarded"])
        self.assertEqual(observed["downstream_response_bytes"], 0)
        self.assertFalse(observed["physical_link_partition_tested"])
        self.assertFalse(observed["production_approved"])
        self.assertEqual(len(observed["request_sha256"]), 64)
        self.assertNotIn("test", str(observed))  # raw command payload not recorded

    def test_14_downstream_proxy_binds_loopback_only(self):
        with OneShotTransportFault(55444, "drop_before_forward") as proxy:
            self.assertEqual(proxy.listen.getsockname()[0], "127.0.0.1")
            req = urllib.request.Request(
                f"http://127.0.0.1:{proxy.port}/transfer",
                data=b'{"mode":"loopback"}')
            with self.assertRaises((OSError, HTTPException, urllib.error.URLError)):
                urllib.request.urlopen(req, timeout=3)
            proxy.wait()


if __name__ == "__main__":
    unittest.main()
