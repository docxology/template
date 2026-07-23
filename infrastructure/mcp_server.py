"""Self-contained stdio MCP server exposing the template's agent surface.

This is the capstone of the package's agentic-operability surface: it makes
every discovered capability reachable to *any* MCP-speaking agent, not just an
editor that reads ``.cursor/*.json``. It is the server counterpart to the
discovery registries — :mod:`infrastructure.skills.operation_registry`,
:mod:`infrastructure.core.pipeline.cli`, and
:mod:`infrastructure.skills.discovery` — surfacing them as MCP *tools*.

**Zero new dependencies.** It speaks MCP's stdio transport directly: one
JSON-RPC 2.0 message per line on stdin/stdout, using only the standard library.
It is dual-era: legacy clients use the ``2024-11-05`` initialize lifecycle,
while ``2026-07-28`` clients use ``server/discover`` and self-contained request
metadata. That keeps the default install untouched and lets both eras be tested
via the pure :func:`handle_request` function without any transport or SDK.

Tools exposed:

* ``list_operations`` — the machine-readable CLI operation catalog.
* ``describe_pipeline`` — the 16-stage pipeline contract derived from pipeline.yaml.
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
from typing import Any, Callable, Literal

from infrastructure.core.pipeline.cli import CORE_ONLY_EXCLUDED_TAGS, DEFAULT_PIPELINE_YAML, stage_rows
from infrastructure.skills.discovery import (
    discover_skills,
    skill_descriptors_as_json_serializable,
)
from infrastructure.skills.operation_registry import (
    OperationDescriptor,
    build_operations_payload,
    discover_operations,
)

# Env var that opts an agent into running ``mutating`` (publish / upload / paid)
# CLIs through :func:`invoke_cli`. Any truthy value enables it.
ALLOW_MUTATING_ENV = "TEMPLATE_MCP_ALLOW_MUTATING"

__all__ = [
    "LEGACY_PROTOCOL_VERSION",
    "MODERN_PROTOCOL_VERSION",
    "PROTOCOL_VERSION",
    "SERVER_INFO",
    "SUPPORTED_PROTOCOL_VERSIONS",
    "handle_request",
    "invoke_cli",
    "list_tools",
    "main",
    "serve",
]

LEGACY_PROTOCOL_VERSION = "2024-11-05"
MODERN_PROTOCOL_VERSION = "2026-07-28"
# Backward-compatible public name: existing callers use this as the version
# returned by the legacy ``initialize`` handshake.
PROTOCOL_VERSION = LEGACY_PROTOCOL_VERSION
SUPPORTED_PROTOCOL_VERSIONS = (MODERN_PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION)
ProtocolEra = Literal["legacy", "modern"]
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


def _repo_root() -> Path:
    """Repo root = two levels up from this file (infrastructure/mcp_server.py)."""
    return Path(__file__).resolve().parents[1]


# ── Tool implementations ──────────────────────────────────────────────────


def _tool_list_operations(_args: dict[str, Any]) -> dict[str, Any]:
    return build_operations_payload(discover_operations(_repo_root()))


def _tool_describe_pipeline(args: dict[str, Any]) -> dict[str, Any]:
    exclude = set(CORE_ONLY_EXCLUDED_TAGS) if args.get("core_only") else None
    rows = stage_rows(DEFAULT_PIPELINE_YAML, exclude_tags=exclude)
    return {"version": 1, "source": DEFAULT_PIPELINE_YAML.as_posix(), "stages": rows}


def _tool_list_skills(_args: dict[str, Any]) -> dict[str, Any]:
    skills = discover_skills(_repo_root())
    return {"version": 1, "skills": skill_descriptors_as_json_serializable(skills)}


def _operations_by_module() -> dict[str, OperationDescriptor]:
    return {op.module: op for op in discover_operations(_repo_root())}


def _mutating_opt_in_env() -> bool:
    return os.environ.get(ALLOW_MUTATING_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


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

    Capability tiering: a ``mutating`` operation (publish / upload / paid CLI, per
    the operation registry's ``effect`` tier) is refused unless the caller passes
    ``allow_mutating=True`` or sets the ``TEMPLATE_MCP_ALLOW_MUTATING`` env var.
    ``read_only`` operations run unconditionally.
    """
    args = list(args or [])
    if not module.startswith("infrastructure."):
        return {"exit_code": 2, "stdout": "", "stderr": f"refused: {module!r} is not an infrastructure.* module"}
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
                f"refused: {module!r} is a mutating/paid operation; re-invoke with "
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
    module = str(args.get("module", ""))
    cli_args = args.get("args") or []
    if not isinstance(cli_args, list):
        return {"exit_code": 2, "stdout": "", "stderr": "args must be a list of strings"}
    return invoke_cli(module, [str(a) for a in cli_args], allow_mutating=bool(args.get("allow_mutating", False)))


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
                "core_only": {
                    "type": "boolean",
                    "description": "Exclude LLM-tagged and opt-in publishing/archive stages",
                }
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
        "Mutating/paid CLIs are refused unless allow_mutating is true.",
        {
            "type": "object",
            "properties": {
                "module": {"type": "string", "description": "Dotted module, e.g. infrastructure.core.pipeline"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "CLI arguments"},
                "allow_mutating": {
                    "type": "boolean",
                    "description": "Opt in to running a mutating/paid (publish/upload) operation",
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


def _request_era(request: dict[str, Any]) -> ProtocolEra:
    """Classify a request without consulting transport or prior messages."""
    method = request.get("method")
    meta = _request_meta(request)
    if method == "server/discover" or (
        meta is not None
        and any(key in meta for key in (_PROTOCOL_VERSION_META, _CLIENT_INFO_META, _CLIENT_CAPABILITIES_META))
    ):
        return "modern"
    return "legacy"


def _modern_request_error(request: dict[str, Any]) -> dict[str, Any] | None:
    """Validate metadata required by the stateless 2026-07-28 protocol era."""
    req_id = request.get("id")
    meta = _request_meta(request)
    if meta is None:
        return _err(req_id, -32602, f"missing required params._meta.{_PROTOCOL_VERSION_META}")

    requested = meta.get(_PROTOCOL_VERSION_META)
    if not isinstance(requested, str) or not requested:
        return _err(req_id, -32602, f"missing required params._meta.{_PROTOCOL_VERSION_META}")
    if requested != MODERN_PROTOCOL_VERSION:
        return _err(
            req_id,
            -32022,
            "Unsupported protocol version",
            data={"supported": list(SUPPORTED_PROTOCOL_VERSIONS), "requested": requested},
        )

    client_info = meta.get(_CLIENT_INFO_META)
    if not isinstance(client_info, dict) or not all(
        isinstance(client_info.get(key), str) and client_info[key] for key in ("name", "version")
    ):
        return _err(req_id, -32602, f"missing or invalid params._meta.{_CLIENT_INFO_META}")
    if not isinstance(meta.get(_CLIENT_CAPABILITIES_META), dict):
        return _err(req_id, -32602, f"missing or invalid params._meta.{_CLIENT_CAPABILITIES_META}")
    return None


def handle_request(
    request: dict[str, Any],
    *,
    protocol_era: ProtocolEra | None = None,
) -> dict[str, Any] | None:
    """Handle one JSON-RPC request object; return a response, or None for notifications.

    Pure function over a parsed request — no I/O — so it is directly unit-testable.
    Without ``protocol_era`` it classifies each request independently, preserving
    the original handler API. The stdio transport supplies its process-pinned era
    so one client cannot switch wire semantics after its opening request.
    """
    method = request.get("method")
    req_id = request.get("id")

    # Notifications (no id) get no response.
    if method == "notifications/initialized" or (req_id is None and method != "initialize"):
        return None

    inferred_era = _request_era(request)
    if protocol_era == "legacy" and inferred_era == "modern":
        modern_error = _modern_request_error(request)
        if modern_error is not None:
            return modern_error
        meta = _request_meta(request)
        requested = meta.get(_PROTOCOL_VERSION_META) if meta is not None else MODERN_PROTOCOL_VERSION
        return _err(
            req_id,
            -32022,
            "Protocol era mismatch: stdio process is pinned to legacy",
            data={"supported": [LEGACY_PROTOCOL_VERSION], "requested": requested},
        )
    if protocol_era == "modern" and inferred_era == "legacy" and method == "initialize":
        return _err(req_id, -32601, "method not found in the modern protocol era: initialize")

    modern = protocol_era == "modern" or inferred_era == "modern"
    if modern:
        modern_error = _modern_request_error(request)
        if modern_error is not None:
            return modern_error

    if method == "server/discover":
        return _ok(
            req_id,
            {
                "resultType": "complete",
                "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
                "capabilities": SERVER_CAPABILITIES,
                "serverInfo": SERVER_INFO,
                "instructions": SERVER_INSTRUCTIONS,
                "ttlMs": LIST_CACHE_TTL_MS,
                "cacheScope": LIST_CACHE_SCOPE,
            },
        )

    if method == "initialize":
        if modern:
            return _err(req_id, -32601, "method not found in the modern protocol era: initialize")
        return _ok(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": SERVER_CAPABILITIES,
                "serverInfo": SERVER_INFO,
            },
        )

    if method == "tools/list":
        list_result: dict[str, Any] = {"tools": list_tools()}
        if modern:
            list_result = {
                "resultType": "complete",
                **list_result,
                "ttlMs": LIST_CACHE_TTL_MS,
                "cacheScope": LIST_CACHE_SCOPE,
            }
        return _ok(req_id, list_result)

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
                "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True,
            }
            if modern:
                error_result["resultType"] = "complete"
            return _ok(
                req_id,
                error_result,
            )
        call_result: dict[str, Any] = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}
        if modern:
            call_result = {"resultType": "complete", **call_result, "isError": False}
        return _ok(req_id, call_result)

    return _err(req_id, -32601, f"method not found: {method}")


def serve(stdin: Any = None, stdout: Any = None) -> int:
    """Run stdio JSON-RPC with the protocol era pinned by the opening request."""
    src = stdin if stdin is not None else sys.stdin
    dst = stdout if stdout is not None else sys.stdout
    protocol_era: ProtocolEra | None = None
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
        if protocol_era is None and request.get("id") is not None:
            protocol_era = _request_era(request)
        response = handle_request(request, protocol_era=protocol_era)
        if response is not None:
            dst.write(json.dumps(response, ensure_ascii=False) + "\n")
            dst.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: serve the MCP server on stdio."""
    return serve()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
