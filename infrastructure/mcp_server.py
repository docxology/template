"""Self-contained stdio MCP server exposing the template's agent surface.

This is the capstone of the package's agentic-operability surface: it makes
every discovered capability reachable to agents implementing MCP ``2026-07-28``.
It is the server counterpart to the shared ``.agents/`` catalog and
discovery registries — :mod:`infrastructure.skills.operation_registry`,
:mod:`infrastructure.core.pipeline.cli`, and
:mod:`infrastructure.skills.discovery` — surfacing them as MCP *tools*.

**Zero new dependencies.** It speaks MCP's stdio transport directly: one
JSON-RPC 2.0 message per line on stdin/stdout, using only the standard library.
Requests carry self-contained protocol, client identity and capability metadata.
Clients can discover the server with ``server/discover`` or invoke tools directly.
The handler and stdio transport share this single stateless wire contract.

Tools exposed:

* ``list_operations`` — the machine-readable CLI operation catalog.
* ``describe_pipeline`` — the declared pipeline contract derived from pipeline.yaml.
* ``list_skills`` — discovered ``SKILL.md`` descriptors.
* ``invoke_cli`` — run ``python -m infrastructure.<module> <args...>`` and return
  ``{exit_code, stdout, stderr}``. Restricted to ``infrastructure.*`` modules that
  the operation registry reports as invocable (no arbitrary command execution).

Run it::

    uv run python -m infrastructure.mcp_server          # serve on stdio
    uv run python scripts/runner/mcp_server_template.py         # thin launcher

It is intentionally NOT wired into the default pipeline or CI — it is an
opt-in agent-facing surface. See ``docs/architecture/capability-surfaces.md``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from infrastructure.core.pipeline.cli import pipeline_description
from infrastructure.skills.discovery import (
    discover_skills,
    skill_descriptors_as_json_serializable,
)
from infrastructure.skills.operation_registry import (
    OperationDescriptor,
    build_operations_payload,
    discover_operations,
)

# Configured opt-in for file-writing, external/paid, or unaudited CLI modules.
# The existing parser admits only the declared true strings.
ALLOW_MUTATING_ENV = "TEMPLATE_MCP_ALLOW_MUTATING"

__all__ = [
    "PROTOCOL_VERSION",
    "SERVER_INFO",
    "SUPPORTED_PROTOCOL_VERSIONS",
    "handle_request",
    "invoke_cli",
    "list_tools",
    "main",
    "serve",
]

PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_PROTOCOL_VERSIONS = (PROTOCOL_VERSION,)
SERVER_INFO = {"name": "humos-template", "version": "1.0.0"}
SERVER_CAPABILITIES: dict[str, Any] = {"tools": {}}
SERVER_INSTRUCTIONS = (
    "Discover the template's registered operations, pipeline stages, and skills; "
    "invoke only curated infrastructure.* command-line operations."
)
LIST_CACHE_TTL_MS = 300_000
LIST_CACHE_SCOPE = "public"

_PROTOCOL_VERSION_META = "io.modelcontextprotocol/protocolVersion"
_CLIENT_INFO_META = "io.modelcontextprotocol/clientInfo"
_CLIENT_CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
_SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"


def _repo_root() -> Path:
    """Repo root = two levels up from this file (infrastructure/mcp_server.py)."""
    return Path(__file__).resolve().parents[1]


# ── Tool implementations ──────────────────────────────────────────────────


def _tool_list_operations(_args: dict[str, Any]) -> dict[str, Any]:
    return build_operations_payload(discover_operations(_repo_root()))


def _tool_describe_pipeline(args: dict[str, Any]) -> dict[str, Any]:
    if set(args) - {"mode", "view", "project"}:
        raise ValueError("Unsupported pipeline-description option")
    return pipeline_description(
        repo_root=_repo_root(),
        mode=args.get("mode", "core"),
        view=args.get("view", "execution"),
        project=args.get("project"),
    )


def _tool_list_skills(_args: dict[str, Any]) -> dict[str, Any]:
    skills = discover_skills(_repo_root())
    return {"version": 1, "skills": skill_descriptors_as_json_serializable(skills)}


def _operations_by_module() -> dict[str, OperationDescriptor]:
    return {op.module: op for op in discover_operations(_repo_root())}


def _mutating_opt_in_env() -> bool:
    return os.environ.get(ALLOW_MUTATING_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def invoke_cli(
    module: str,
    args: list[str] | None = None,
    *,
    timeout: float = 120.0,
    allow_mutating: bool = False,
) -> dict[str, Any]:
    """Run ``python -m <module> <args...>`` for an invocable ``infrastructure.*`` module.

    Returns ``{exit_code, stdout, stderr}``. Refuses any module outside
    ``infrastructure.*`` or not reported as invocable by the operation registry —
    this is a curated tool surface, not an arbitrary shell.

    Capability tiering: known file-writing, external/paid and unaudited operations
    require opt-in. Only explicitly reviewed ``read_only`` modules run without it.
    ``allow_mutating`` must be a boolean; literal ``True`` or the existing configured
    ``TEMPLATE_MCP_ALLOW_MUTATING`` opt-in authorizes the guarded tier. A valid
    ``False`` does not disable that configured opt-in; malformed values are refused.
    """
    if type(allow_mutating) is not bool:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": "allow_mutating must be a boolean",
        }
    args = list(args or [])
    if not module.startswith("infrastructure."):
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": f"refused: {module!r} is not an infrastructure.* module",
        }
    operations = _operations_by_module()
    descriptor = operations.get(module)
    if descriptor is None:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": f"refused: {module!r} is not a registered invocable CLI (see list_operations)",
        }
    if descriptor.effect == "mutating" and not (allow_mutating or _mutating_opt_in_env()):
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": (
                f"refused: {module!r} is a mutating or unaudited operation; re-invoke with "
                f"allow_mutating=true (or set {ALLOW_MUTATING_ENV}=1) to opt in"
            ),
        }
    proc = subprocess.run(  # noqa: S603 - curated module list, not arbitrary input
        [sys.executable, "-m", module, *args],
        capture_output=True,
        text=True,
        cwd=_repo_root(),
        timeout=timeout,
    )
    return {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def _tool_invoke_cli(args: dict[str, Any]) -> dict[str, Any]:
    allow_mutating = args.get("allow_mutating", False)
    if type(allow_mutating) is not bool:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": "allow_mutating must be a boolean",
        }
    module = str(args.get("module", ""))
    cli_args = args.get("args") or []
    if not isinstance(cli_args, list):
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": "args must be a list of strings",
        }
    return invoke_cli(module, [str(a) for a in cli_args], allow_mutating=allow_mutating)


# name -> (handler, description, inputSchema)
_TOOLS: dict[str, tuple[Callable[[dict[str, Any]], dict[str, Any]], str, dict[str, Any]]] = {
    "list_operations": (
        _tool_list_operations,
        "List every agent-invocable CLI operation (module, invocation, subcommands, exports).",
        {"type": "object", "properties": {}, "additionalProperties": False},
    ),
    "describe_pipeline": (
        _tool_describe_pipeline,
        "Return the pipeline stage catalog derived from pipeline.yaml.",
        {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["core", "live"], "default": "core"},
                "view": {
                    "type": "string",
                    "enum": ["execution", "declared"],
                    "default": "execution",
                },
                "project": {"type": "string"},
            },
            "additionalProperties": False,
        },
    ),
    "list_skills": (
        _tool_list_skills,
        "List discovered SKILL.md descriptors (name, description, path).",
        {"type": "object", "properties": {}, "additionalProperties": False},
    ),
    "invoke_cli": (
        _tool_invoke_cli,
        "Run a registered infrastructure.* CLI via 'python -m <module>' and return exit_code/stdout/stderr. "
        "Only audited read-only modules run without opt-in; other CLIs require boolean allow_mutating=true "
        "or the configured environment opt-in.",
        {
            "type": "object",
            "properties": {
                "module": {
                    "type": "string",
                    "description": "Dotted module, e.g. infrastructure.core.pipeline",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI arguments",
                },
                "allow_mutating": {
                    "type": "boolean",
                    "description": "Explicit boolean opt-in for file-writing, external/paid, or unaudited operations",
                },
            },
            "required": ["module"],
            "additionalProperties": False,
        },
    ),
}


def list_tools() -> list[dict[str, Any]]:
    """Return the MCP ``tools/list`` payload."""
    return [
        {"name": name, "description": desc, "inputSchema": schema} for name, (_handler, desc, schema) in _TOOLS.items()
    ]


# ── JSON-RPC / MCP protocol ───────────────────────────────────────────────


def _ok(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str, *, data: dict[str, Any] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": error}


def _request_meta(request: dict[str, Any]) -> dict[str, Any] | None:
    params = request.get("params")
    if not isinstance(params, dict):
        return None
    meta = params.get("_meta")
    return meta if isinstance(meta, dict) else None


def _request_error(request: dict[str, Any]) -> dict[str, Any] | None:
    """Validate metadata required by the stateless protocol."""
    req_id = request.get("id")
    meta = _request_meta(request)
    if meta is None:
        return _err(req_id, -32602, f"missing required params._meta.{_PROTOCOL_VERSION_META}")

    requested = meta.get(_PROTOCOL_VERSION_META)
    if not isinstance(requested, str) or not requested:
        return _err(req_id, -32602, f"missing required params._meta.{_PROTOCOL_VERSION_META}")
    if requested != PROTOCOL_VERSION:
        return _err(
            req_id,
            -32022,
            "Unsupported protocol version",
            data={
                "supported": list(SUPPORTED_PROTOCOL_VERSIONS),
                "requested": requested,
            },
        )

    client_info = meta.get(_CLIENT_INFO_META)
    if not isinstance(client_info, dict) or not all(
        isinstance(client_info.get(key), str) and client_info[key] for key in ("name", "version")
    ):
        return _err(req_id, -32602, f"missing or invalid params._meta.{_CLIENT_INFO_META}")
    if not isinstance(meta.get(_CLIENT_CAPABILITIES_META), dict):
        return _err(
            req_id,
            -32602,
            f"missing or invalid params._meta.{_CLIENT_CAPABILITIES_META}",
        )
    return None


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC request object; return a response, or None for notifications.

    Each request validates its own protocol and client metadata before invoking
    a tool. Discovery is optional and cannot authorize a later metadata-free call.
    """
    method = request.get("method")
    req_id = request.get("id")

    # Notifications (no id) get no response.
    if req_id is None:
        return None

    request_error = _request_error(request)
    if request_error is not None:
        return request_error

    if method == "server/discover":
        return _ok(
            req_id,
            {
                "resultType": "complete",
                "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
                "capabilities": SERVER_CAPABILITIES,
                "_meta": {_SERVER_INFO_META: SERVER_INFO},
                "instructions": SERVER_INSTRUCTIONS,
                "ttlMs": LIST_CACHE_TTL_MS,
                "cacheScope": LIST_CACHE_SCOPE,
            },
        )

    if method == "tools/list":
        return _ok(
            req_id,
            {
                "resultType": "complete",
                "tools": list_tools(),
                "ttlMs": LIST_CACHE_TTL_MS,
                "cacheScope": LIST_CACHE_SCOPE,
            },
        )

    if method == "tools/call":
        params = request.get("params") or {}
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        entry = _TOOLS.get(name)
        if entry is None:
            return _err(req_id, -32602, f"unknown tool: {name}")
        handler = entry[0]
        try:
            payload = handler(arguments)
        except Exception as exc:  # noqa: BLE001 - report tool errors as MCP isError content
            error_result: dict[str, Any] = {
                "resultType": "complete",
                "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True,
            }
            return _ok(
                req_id,
                error_result,
            )
        call_result: dict[str, Any] = {
            "resultType": "complete",
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
            "isError": False,
        }
        return _ok(req_id, call_result)

    return _err(req_id, -32601, f"method not found: {method}")


def serve(stdin: Any = None, stdout: Any = None) -> int:
    """Run newline-delimited JSON-RPC with independent request admission."""
    src = stdin if stdin is not None else sys.stdin
    dst = stdout if stdout is not None else sys.stdout
    for line in src:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            dst.write(json.dumps(_err(None, -32700, "parse error")) + "\n")
            dst.flush()
            continue
        response = handle_request(request) if isinstance(request, dict) else _err(None, -32600, "invalid request")
        if response is not None:
            dst.write(json.dumps(response, ensure_ascii=False) + "\n")
            dst.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: serve the MCP server on stdio."""
    return serve()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
