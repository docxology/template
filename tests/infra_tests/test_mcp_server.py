"""Current stdio MCP contract using real handlers and subprocesses."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from infrastructure.mcp_server import (
    ALLOW_MUTATING_ENV,
    PROTOCOL_VERSION,
    handle_request,
    invoke_cli,
    list_tools,
    serve,
)


def _request(method: str, *, request_id: int = 1, **params: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
                "io.modelcontextprotocol/clientInfo": {"name": "template-tests", "version": "1.0.0"},
                "io.modelcontextprotocol/clientCapabilities": {},
            },
            **params,
        },
    }


def _payload(response: dict[str, Any] | None) -> dict[str, Any]:
    assert response is not None
    result = response["result"]
    assert result["resultType"] == "complete" and result["isError"] is False
    return json.loads(result["content"][0]["text"])


def _run_stdio_subprocess(messages: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.mcp_server"],
        input="\n".join(json.dumps(message) for message in messages) + "\n",
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    # Every stdout line must remain JSON-RPC, including tools that load the DAG.
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return {line.get("id"): line for line in lines}


class TestProtocol:
    def test_discovery_has_current_version_and_namespaced_server_identity(self) -> None:
        response = handle_request(_request("server/discover"))
        assert response is not None
        result = response["result"]
        assert result["supportedVersions"] == [PROTOCOL_VERSION]
        assert PROTOCOL_VERSION == "2026-07-28"
        assert result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "humos-template"
        assert "serverInfo" not in result
        assert result["capabilities"] == {"tools": {}}
        assert result["resultType"] == "complete"
        assert result["ttlMs"] > 0 and result["cacheScope"] == "public"

    def test_tools_list_is_independent_and_cacheable(self) -> None:
        first = handle_request(_request("tools/list", request_id=2))
        second = handle_request(_request("tools/list", request_id=3))
        assert first is not None and second is not None
        assert first["result"] == second["result"]
        result = first["result"]
        assert result["resultType"] == "complete"
        assert result["ttlMs"] > 0 and result["cacheScope"] == "public"
        assert {tool["name"] for tool in result["tools"]} == {
            "list_operations",
            "describe_pipeline",
            "list_skills",
            "invoke_cli",
        }
        assert all("inputSchema" in tool for tool in list_tools())

    @pytest.mark.parametrize("method", ["server/discover", "tools/list", "tools/call"])
    def test_metadata_required_on_every_request(self, method: str) -> None:
        response = handle_request({"jsonrpc": "2.0", "id": 4, "method": method, "params": {}})
        assert response is not None and response["error"]["code"] == -32602
        assert "protocolVersion" in response["error"]["message"]

    @pytest.mark.parametrize(
        "field,value",
        [
            ("protocolVersion", ""),
            ("protocolVersion", 20260728),
            ("clientInfo", {}),
            ("clientInfo", {"name": "client", "version": ""}),
            ("clientCapabilities", None),
        ],
    )
    def test_incomplete_metadata_is_invalid(self, field: str, value: Any) -> None:
        request = _request("tools/list")
        request["params"]["_meta"][f"io.modelcontextprotocol/{field}"] = value
        response = handle_request(request)
        assert response is not None and response["error"]["code"] == -32602
        assert field in response["error"]["message"]

    def test_unsupported_version_returns_only_current_supported_version(self) -> None:
        request = _request("tools/list")
        request["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "1900-01-01"
        response = handle_request(request)
        assert response is not None
        assert response["error"] == {
            "code": -32022,
            "message": "Unsupported protocol version",
            "data": {"supported": [PROTOCOL_VERSION], "requested": "1900-01-01"},
        }

    @pytest.mark.parametrize("method", ["frobnicate", "initialize"])
    def test_unknown_method(self, method: str) -> None:
        response = handle_request(_request(method))
        assert response is not None and response["error"]["code"] == -32601

    def test_notification_has_no_response(self) -> None:
        notification = _request("notifications/progress", progressToken="owned", progress=1)
        del notification["id"]
        assert handle_request(notification) is None


class TestTools:
    def test_describe_pipeline(self) -> None:
        payload = _payload(handle_request(_request("tools/call", name="describe_pipeline", arguments={"mode": "core"})))
        assert len(payload["stages"]) == 8

    def test_list_operations(self) -> None:
        payload = _payload(handle_request(_request("tools/call", name="list_operations")))
        assert any(op["module"] == "infrastructure.skills" for op in payload["operations"])

    def test_list_skills_includes_agents_skill_lanes(self) -> None:
        payload = _payload(handle_request(_request("tools/call", name="list_skills")))
        paths = {skill["path"] for skill in payload["skills"]}
        assert ".agents/skills/context-fundamentals/SKILL.md" in paths
        assert "projects/templates/template_code_project/.agents/skills/template-code-project/SKILL.md" in paths

    def test_unknown_tool_is_error(self) -> None:
        response = handle_request(_request("tools/call", name="nope"))
        assert response is not None and response["error"]["code"] == -32602

    def test_tool_failure_retains_complete_error_result(self) -> None:
        response = handle_request(_request("tools/call", name="describe_pipeline", arguments={"unsupported": True}))
        assert response is not None
        result = response["result"]
        assert result["resultType"] == "complete" and result["isError"] is True
        assert "Unsupported pipeline-description option" in result["content"][0]["text"]


class TestInvokeCli:
    @pytest.mark.parametrize("module", ["os", "infrastructure.not_a_real_cli"])
    def test_refuses_unregistered_module(self, module: str) -> None:
        out = invoke_cli(module, ["--help"])
        assert out["exit_code"] == 2 and "refused" in out["stderr"]

    def test_invokes_registered_cli(self) -> None:
        out = invoke_cli("infrastructure.core.pipeline", ["describe-pipeline", "--format", "json"])
        assert out["exit_code"] == 0
        assert len(json.loads(out["stdout"])["stages"]) == 8

    def test_read_only_single_file_cli_is_reachable(self) -> None:
        out = invoke_cli("infrastructure.project.public_scope", ["source-paths"])
        assert out["exit_code"] == 0 and out["stdout"].strip()

    @pytest.mark.parametrize("module", ["infrastructure.publishing", "infrastructure.project.locked_dependency_export"])
    def test_refuses_mutating_op_by_default(self, module: str) -> None:
        out = invoke_cli(module, ["--help"])
        assert out["exit_code"] == 2 and out["stdout"] == "" and "mutating" in out["stderr"]
        for authorization in ({}, {"allow_mutating": False}):
            response = handle_request(
                _request(
                    "tools/call",
                    name="invoke_cli",
                    arguments={"module": module, "args": ["--help"], **authorization},
                )
            )
            assert _payload(response) == out

    @pytest.mark.parametrize("value", ["false", "true", 0, 1, 0.0, None, [], {}])
    def test_malformed_authorization_cannot_be_coerced(self, value: Any) -> None:
        out = invoke_cli("infrastructure.publishing", ["--help"], allow_mutating=value)
        assert out == {"exit_code": 2, "stdout": "", "stderr": "allow_mutating must be a boolean"}
        response = handle_request(
            _request(
                "tools/call",
                name="invoke_cli",
                arguments={"module": "infrastructure.publishing", "args": ["--help"], "allow_mutating": value},
            )
        )
        assert _payload(response) == out

    def test_mutating_op_allowed_with_flag(self) -> None:
        # Actual help is side-effect free; literal True admits the guarded tier.
        out = invoke_cli("infrastructure.publishing", ["--help"], allow_mutating=True)
        assert out["exit_code"] == 0 and "mutating" not in out["stderr"]
        response = handle_request(
            _request(
                "tools/call",
                name="invoke_cli",
                arguments={"module": "infrastructure.publishing", "args": ["--help"], "allow_mutating": True},
            )
        )
        payload = _payload(response)
        assert payload["exit_code"] == 0 and "mutating" not in payload["stderr"]

    def test_mutating_op_allowed_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ALLOW_MUTATING_ENV, "1")
        for value in (False, "false"):
            out = invoke_cli("infrastructure.publishing", ["--help"], allow_mutating=value)
            response = handle_request(
                _request(
                    "tools/call",
                    name="invoke_cli",
                    arguments={"module": "infrastructure.publishing", "args": ["--help"], "allow_mutating": value},
                )
            )
            payload = _payload(response)
            if value is False:
                assert out["exit_code"] == payload["exit_code"] == 0
                assert "mutating" not in out["stderr"] + payload["stderr"]
            else:
                assert out == payload == {"exit_code": 2, "stdout": "", "stderr": "allow_mutating must be a boolean"}


class TestServeLoop:
    def test_round_trip_recovers_after_malformed_input(self) -> None:
        notification = _request("notifications/progress", progressToken="owned", progress=1)
        del notification["id"]
        requests = "\n".join(
            [
                json.dumps(_request("server/discover")),
                json.dumps(notification),
                "",
                "{ not json",
                "[]",
                json.dumps(_request("tools/list", request_id=2)),
            ]
        )
        out = io.StringIO()
        assert serve(stdin=io.StringIO(requests), stdout=out) == 0
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        assert len(lines) == 4
        assert lines[0]["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "humos-template"
        assert [line["error"]["code"] for line in lines if "error" in line] == [-32700, -32600]
        assert "tools" in lines[-1]["result"]

    def test_discovery_does_not_waive_later_request_metadata(self) -> None:
        requests = [
            _request("server/discover"),
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            _request("tools/list", request_id=3),
        ]
        out = io.StringIO()
        assert serve(stdin=io.StringIO("\n".join(map(json.dumps, requests))), stdout=out) == 0
        by_id = {line["id"]: line for line in map(json.loads, out.getvalue().splitlines())}
        assert by_id[2]["error"]["code"] == -32602
        assert by_id[3]["result"]["resultType"] == "complete"

    def test_real_subprocess_stdio_with_optional_discovery(self) -> None:
        by_id = _run_stdio_subprocess(
            [
                _request("tools/call", name="describe_pipeline", arguments={"mode": "core"}),
                _request("server/discover", request_id=2),
                _request("tools/list", request_id=3),
            ]
        )
        assert len(_payload(by_id[1])["stages"]) == 8
        assert by_id[2]["result"]["supportedVersions"] == [PROTOCOL_VERSION]
        assert by_id[2]["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "humos-template"
        assert by_id[3]["result"]["resultType"] == "complete"
