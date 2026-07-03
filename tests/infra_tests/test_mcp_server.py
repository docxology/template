"""Tests for the stdio MCP server (no mocks; real handler + real subprocess)."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

from infrastructure.mcp_server import (
    ALLOW_MUTATING_ENV,
    PROTOCOL_VERSION,
    handle_request,
    invoke_cli,
    list_tools,
    serve,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class TestHandleRequest:
    def test_initialize(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp is not None
        assert resp["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert resp["result"]["serverInfo"]["name"] == "humos-template"
        assert "tools" in resp["result"]["capabilities"]

    def test_initialized_notification_has_no_response(self) -> None:
        assert handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None

    def test_tools_list(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {t["name"] for t in resp["result"]["tools"]}
        assert {"list_operations", "describe_pipeline", "list_skills", "invoke_cli"} <= names
        # every tool advertises an inputSchema
        assert all("inputSchema" in t for t in list_tools())

    def test_tools_call_describe_pipeline(self) -> None:
        resp = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "describe_pipeline", "arguments": {"core_only": True}},
            }
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert len(payload["stages"]) == 8

    def test_tools_call_list_operations(self) -> None:
        resp = handle_request(
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "list_operations"}}
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert any(op["module"] == "infrastructure.skills" for op in payload["operations"])

    def test_unknown_tool_is_error(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "nope"}})
        assert "error" in resp

    def test_unknown_method(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 6, "method": "frobnicate"})
        assert resp["error"]["code"] == -32601


class TestInvokeCli:
    def test_refuses_non_infrastructure_module(self) -> None:
        out = invoke_cli("os", ["--help"])
        assert out["exit_code"] == 2
        assert "refused" in out["stderr"]

    def test_refuses_unregistered_module(self) -> None:
        out = invoke_cli("infrastructure.not_a_real_cli", [])
        assert out["exit_code"] == 2
        assert "refused" in out["stderr"]

    def test_invokes_registered_cli(self) -> None:
        out = invoke_cli("infrastructure.core.pipeline", ["describe-pipeline", "--format", "json"])
        assert out["exit_code"] == 0
        payload = json.loads(out["stdout"])
        assert len(payload["stages"]) == 14

    def test_read_only_single_file_cli_is_reachable(self) -> None:
        # R7: a documented single-file CLI (read_only) runs via invoke_cli.
        out = invoke_cli("infrastructure.project.public_scope", ["source-paths"])
        assert out["exit_code"] == 0
        assert out["stdout"].strip()

    def test_refuses_mutating_op_by_default(self) -> None:
        # R18: a publish/paid (mutating) op is refused without opt-in — and never spawned.
        out = invoke_cli("infrastructure.publishing", ["--help"])
        assert out["exit_code"] == 2
        assert "mutating" in out["stderr"]

    def test_mutating_op_allowed_with_flag(self) -> None:
        # --help is side-effect free; opt-in must bypass the tier refusal.
        out = invoke_cli("infrastructure.publishing", ["--help"], allow_mutating=True)
        assert "mutating" not in out["stderr"]

    def test_mutating_op_allowed_with_env(self, monkeypatch) -> None:
        monkeypatch.setenv(ALLOW_MUTATING_ENV, "1")
        out = invoke_cli("infrastructure.publishing", ["--help"])
        assert "mutating" not in out["stderr"]


class TestServeLoop:
    def test_serve_round_trip_in_process(self) -> None:
        requests = "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                "",  # blank line ignored
                "{ not json",  # parse error -> error response, loop continues
            ]
        )
        out = io.StringIO()
        rc = serve(stdin=io.StringIO(requests), stdout=out)
        assert rc == 0
        lines = [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]
        # initialize result, tools/list result, and one parse error (notification produced nothing)
        assert lines[0]["result"]["serverInfo"]["name"] == "humos-template"
        assert any("tools" in line.get("result", {}) for line in lines)
        assert any(line.get("error", {}).get("code") == -32700 for line in lines)

    def test_real_subprocess_stdio(self) -> None:
        # Include describe_pipeline: it loads the DAG (which logs to stdout), so this
        # guards against the loader log corrupting the JSON-RPC stream over real stdio.
        requests = (
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            + "\n"
            + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            + "\n"
            + json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "describe_pipeline"}})
            + "\n"
        )
        proc = subprocess.run(
            [sys.executable, "-m", "infrastructure.mcp_server"],
            input=requests,
            capture_output=True,
            text=True,
            cwd=_repo_root(),
            timeout=60,
        )
        assert proc.returncode == 0
        # EVERY non-blank stdout line must be valid JSON-RPC — no log leakage.
        lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        by_id = {line.get("id"): line for line in lines}
        assert by_id[1]["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert "tools" in by_id[2]["result"]
        pipeline_payload = json.loads(by_id[3]["result"]["content"][0]["text"])
        assert len(pipeline_payload["stages"]) == 14
