"""Tests for the stdio MCP server (no mocks; real handler + real subprocess)."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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


MODERN_PROTOCOL_VERSION = "2026-07-28"


def _modern_meta(protocol_version: str = MODERN_PROTOCOL_VERSION) -> dict[str, object]:
    return {
        "io.modelcontextprotocol/protocolVersion": protocol_version,
        "io.modelcontextprotocol/clientInfo": {"name": "template-tests", "version": "1.0.0"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def _run_stdio_subprocess(messages: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, "-m", "infrastructure.mcp_server"],
        input="\n".join(json.dumps(message) for message in messages) + "\n",
        capture_output=True,
        text=True,
        cwd=_repo_root(),
        timeout=60,
    )
    assert proc.returncode == 0
    # EVERY non-blank stdout line must be valid JSON-RPC — no log leakage.
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return {line.get("id"): line for line in lines}


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

    def test_tools_call_list_skills_includes_agents_skill_lanes(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "list_skills"}})
        payload = json.loads(resp["result"]["content"][0]["text"])
        paths = {skill["path"] for skill in payload["skills"]}
        assert ".agents/skills/context-fundamentals/SKILL.md" in paths
        assert "projects/templates/template_code_project/.agents/skills/template-code-project/SKILL.md" in paths

    def test_unknown_tool_is_error(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "nope"}})
        assert "error" in resp

    def test_unknown_method(self) -> None:
        resp = handle_request({"jsonrpc": "2.0", "id": 7, "method": "frobnicate"})
        assert resp["error"]["code"] == -32601


class TestDualEraProtocol:
    def test_pure_handler_keeps_request_local_era_compatibility(self) -> None:
        legacy = handle_request({"jsonrpc": "2.0", "id": 18, "method": "tools/list"})
        modern = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/list",
                "params": {"_meta": _modern_meta()},
            }
        )
        assert legacy is not None and modern is not None
        assert set(legacy["result"]) == {"tools"}
        assert modern["result"]["resultType"] == "complete"

    def test_server_discover_advertises_modern_and_legacy_versions(self) -> None:
        resp = handle_request(
            {
                "jsonrpc": "2.0",
                "id": "discover-1",
                "method": "server/discover",
                "params": {"_meta": _modern_meta()},
            }
        )
        assert resp is not None
        result = resp["result"]
        assert result["resultType"] == "complete"
        assert result["supportedVersions"] == [MODERN_PROTOCOL_VERSION, PROTOCOL_VERSION]
        assert result["capabilities"] == {"tools": {}}
        assert result["serverInfo"]["name"] == "humos-template"
        assert result["ttlMs"] > 0
        assert result["cacheScope"] == "public"

    def test_modern_tools_list_is_stateless_and_cacheable(self) -> None:
        request = {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/list",
            "params": {"_meta": _modern_meta()},
        }
        first = handle_request(request)
        second = handle_request({**request, "id": 21})
        assert first is not None and second is not None
        assert first["result"]["resultType"] == "complete"
        assert first["result"]["tools"] == second["result"]["tools"]
        assert first["result"]["ttlMs"] > 0
        assert first["result"]["cacheScope"] == "public"

    def test_modern_tools_call_has_complete_result_without_initialize(self) -> None:
        resp = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {
                    "name": "describe_pipeline",
                    "arguments": {"core_only": True},
                    "_meta": _modern_meta(),
                },
            }
        )
        assert resp is not None
        assert resp["result"]["resultType"] == "complete"
        assert resp["result"]["isError"] is False
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert len(payload["stages"]) == 8

    def test_unsupported_modern_version_returns_negotiation_error(self) -> None:
        resp = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 23,
                "method": "tools/list",
                "params": {"_meta": _modern_meta("1900-01-01")},
            }
        )
        assert resp is not None
        assert resp["error"]["code"] == -32022
        assert resp["error"]["data"] == {
            "supported": [MODERN_PROTOCOL_VERSION, PROTOCOL_VERSION],
            "requested": "1900-01-01",
        }

    def test_incomplete_modern_metadata_is_invalid_params(self) -> None:
        resp = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 24,
                "method": "server/discover",
                "params": {
                    "_meta": {
                        "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL_VERSION,
                    }
                },
            }
        )
        assert resp is not None
        assert resp["error"]["code"] == -32602
        assert "clientInfo" in resp["error"]["message"]

    def test_legacy_initialize_and_tools_list_shape_remain_compatible(self) -> None:
        initialized = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 25,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}},
            }
        )
        listed = handle_request({"jsonrpc": "2.0", "id": 26, "method": "tools/list"})
        assert initialized is not None and listed is not None
        assert initialized["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert set(listed["result"]) == {"tools"}

    def test_legacy_request_metadata_does_not_select_modern_era(self) -> None:
        listed = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 27,
                "method": "tools/list",
                "params": {"_meta": {"progressToken": "legacy-progress"}},
            }
        )
        assert listed is not None
        assert set(listed["result"]) == {"tools"}


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
        assert len(payload["stages"]) == 16

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

    def test_serve_rejects_modern_request_after_legacy_open(self) -> None:
        requests = "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 30, "method": "initialize", "params": {}}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 31,
                        "method": "tools/list",
                        "params": {"_meta": _modern_meta()},
                    }
                ),
            ]
        )
        out = io.StringIO()
        assert serve(stdin=io.StringIO(requests), stdout=out) == 0
        by_id = {line["id"]: line for line in map(json.loads, out.getvalue().splitlines())}
        assert by_id[30]["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert by_id[31]["error"] == {
            "code": -32022,
            "message": "Protocol era mismatch: stdio process is pinned to legacy",
            "data": {"supported": [PROTOCOL_VERSION], "requested": MODERN_PROTOCOL_VERSION},
        }

    def test_serve_rejects_legacy_initialize_after_modern_open(self) -> None:
        requests = "\n".join(
            [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 32,
                        "method": "server/discover",
                        "params": {"_meta": _modern_meta()},
                    }
                ),
                json.dumps({"jsonrpc": "2.0", "id": 33, "method": "initialize", "params": {}}),
            ]
        )
        out = io.StringIO()
        assert serve(stdin=io.StringIO(requests), stdout=out) == 0
        by_id = {line["id"]: line for line in map(json.loads, out.getvalue().splitlines())}
        assert by_id[32]["result"]["resultType"] == "complete"
        assert by_id[33]["error"]["code"] == -32601

    def test_real_subprocess_legacy_stdio(self) -> None:
        # Include describe_pipeline: it loads the DAG (which logs to stdout), so this
        # guards against the loader log corrupting the JSON-RPC stream over real stdio.
        by_id = _run_stdio_subprocess(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "describe_pipeline"}},
            ]
        )
        assert by_id[1]["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert "tools" in by_id[2]["result"]
        pipeline_payload = json.loads(by_id[3]["result"]["content"][0]["text"])
        assert len(pipeline_payload["stages"]) == 16

    def test_real_subprocess_modern_stdio(self) -> None:
        by_id = _run_stdio_subprocess(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "server/discover",
                    "params": {"_meta": _modern_meta()},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/list",
                    "params": {"_meta": _modern_meta()},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "describe_pipeline",
                        "arguments": {"core_only": True},
                        "_meta": _modern_meta(),
                    },
                },
            ]
        )
        assert by_id[4]["result"]["supportedVersions"] == [MODERN_PROTOCOL_VERSION, PROTOCOL_VERSION]
        assert by_id[5]["result"]["resultType"] == "complete"
        assert by_id[6]["result"]["resultType"] == "complete"
