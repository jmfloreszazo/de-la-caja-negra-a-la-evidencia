#!/usr/bin/env python3
"""Deterministic negative and positive tests for the provenance API retry policy.

The check_evidence module is intentionally a CLI that reads repo files and
exits. Extract only its real github_resource() function via Python AST; do
not monkey-patch the CI audit, external network, or historical run results.
"""
import ast
from contextlib import contextmanager
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "check_evidence.py"
SENTINEL = "https://api.github.com/repos/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/123"


class Response(BytesIO):
    pass


def compile_function(sequence, sleeps):
    syntax = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [node for node in syntax.body
             if isinstance(node, ast.FunctionDef)
             and node.name == "github_resource"]
    assert len(nodes) == 1, "Missing actual provenance function"
    scope = {
        "data": {"repository": "jmfloreszazo/de-la-caja-negra-a-la-evidencia"},
        "json": json, "Request": Request, "HTTPError": HTTPError,
        "URLError": URLError,
        "time": SimpleNamespace(sleep=lambda seconds: sleeps.append(seconds))
    }
    def fake_urlopen(request, timeout):
        assert request.full_url == SENTINEL
        assert request.headers.get("Authorization") == "Bearer test-token"
        assert timeout == 25
        try:
            result = next(sequence)
        except StopIteration as exc:
            raise AssertionError("Unexpected extra GitHub request") from exc
        if isinstance(result, Exception):
            raise result
        return Response(json.dumps(result).encode("utf-8"))
    scope["urlopen"] = fake_urlopen
    compiled = compile(
        ast.Module(body=nodes, type_ignores=[]),
        str(SOURCE), "exec"
    )
    exec(compiled, scope)
    return scope["github_resource"]


def error(status):
    return HTTPError(SENTINEL, status, "synthetic error", {}, None)


def expect_failure(values, expected, sleeps):
    call = compile_function(iter(values), sleeps)
    try:
        call("actions/runs/123", "test-token")
    except HTTPError as exc:
        assert exc.code == expected, exc
    except URLError:
        assert expected == "url-error"
    else:
        raise AssertionError("Transient/untrusted API failure was silently accepted")


def main():
    slept = []
    calls = compile_function(iter([
        error(502), error(503), {"status": "completed", "conclusion": "success"}
    ]), slept)
    assert calls("actions/runs/123", "test-token") == {
        "status": "completed", "conclusion": "success"
    }
    assert slept == [1, 2], slept

    slept = []
    expect_failure([error(403)], 403, slept)
    assert slept == [], "Never retry authorization failures"

    slept = []
    expect_failure([error(404)], 404, slept)
    assert slept == [], "Never retry missing GitHub resources"

    slept = []
    expect_failure([error(502)] * 4, 502, slept)
    assert slept == [1, 2, 4], "Four failed attempts must fail closed"

    slept = []
    expect_failure([URLError("temporary transport failure")] * 4,
                   "url-error", slept)
    assert slept == [1, 2, 4], slept

    print("EVIDENCE API RETRY POLICY: PASS (502/503 recovery, 403/404 immediate fail, persistent transport failure fail-closed)")


if __name__ == "__main__":
    main()
