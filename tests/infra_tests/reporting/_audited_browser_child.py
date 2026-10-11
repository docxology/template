"""Run the actual browser oracle inside a genuinely preimport-audited child.

``audit_browser_html`` holds a Source-owned HTML parent capability. Its child
custodian requires the calling interpreter to have installed the stdlib
executed-bytecode audit before ``infrastructure`` was imported, exactly as the
trusted native launchers do. An ordinary pytest worker never has that audit,
so these helpers start a real child with the same frozen hook bootstrap. No
browser, process or custodian is replaced; the child only returns its actual
observation DATA through a private file.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap

REPO = Path(__file__).resolve().parents[3]

_CHILD = (
    "import json,sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0,sys.argv[1])\n"
    "request=json.loads(Path(sys.argv[2]).read_text())\n"
    "from infrastructure.core.execution_boundary import build_bounded_env\n"
    "from infrastructure.reporting.native_format_browser_oracles import "
    "audit_browser_html,browser_control_bytes,browser_control_contract\n"
    "from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast\n"
    "from infrastructure.reporting.native_format_observer_dispatch import _chrome\n"
    "from infrastructure.reporting.release_readiness_snapshot import SnapshotReader\n"
    "root=Path(request['root'])\n"
    "env=build_bounded_env()\n"
    "if request['control'] is not None:\n"
    "    artifact=None\n"
    "    content=browser_control_bytes(request['control'])\n"
    "    contract=browser_control_contract()\n"
    "else:\n"
    "    artifact=SnapshotReader(root).read(request['artifact'])\n"
    "    content=artifact.content\n"
    "    sources=tuple((name,(root/name).read_bytes()) for name in request['sources'])\n"
    "    contract=semantic_content_contract_from_ast("
    "request['artifact_id'],sources,Path(request['ast']).read_bytes())\n"
    "observation=audit_browser_html(root,Path(request['directory']),content,contract,"
    "chrome=_chrome(env),env=env,deadline=request['deadline'],run_id=request['run_id'],artifact=artifact)\n"
    "_audit_scope['verify_executed_source_code'](Path(sys.argv[1])/'infrastructure',Path(sys.pycache_prefix))\n"
    "Path(request['output']).write_text(json.dumps(observation,sort_keys=True))\n"
)


def _run(workspace: Path, request: dict[str, Any], ast: bytes | None = None) -> dict[str, Any]:
    workspace.mkdir(mode=0o700)
    if ast is not None:
        (workspace / "ast.json").write_bytes(ast)
        request = {**request, "ast": str(workspace / "ast.json")}
    prefix = workspace / "bytecode"
    prefix.mkdir(mode=0o700)
    output = workspace / "observation.json"
    request_path = workspace / "request.json"
    request_path.write_text(json.dumps({**request, "output": str(output)}, sort_keys=True))
    result = run_bounded_subprocess(
        (
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            bytecode_audit_bootstrap((REPO / "infrastructure",), prefix) + _CHILD,
            str(REPO),
            str(request_path),
        ),
        cwd=workspace,
        env=build_bounded_env(),
        timeout=max(1.0, request["deadline"] - time.monotonic() + 30),
    )
    assert result.returncode == result.original_returncode == 0, (result.command_error, result.stderr[-4000:])
    assert result.timed_out is result.custody_refused is False
    observation: dict[str, Any] = json.loads(output.read_text())
    return observation


def audited_browser_control(
    root: Path, directory: Path, name: str, *, workspace: Path, deadline: float, run_id: str
) -> dict[str, Any]:
    """Observe one valid public browser control in an audited child."""
    return _run(
        workspace,
        {
            "root": str(root),
            "directory": str(directory),
            "control": name,
            "deadline": deadline,
            "run_id": run_id,
        },
    )


def audited_browser_artifact(
    root: Path,
    directory: Path,
    artifact: str,
    *,
    sources: tuple[str, ...],
    artifact_id: str,
    ast: bytes,
    workspace: Path,
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Observe one retained HTML artifact against its semantic source contract."""
    return _run(
        workspace,
        {
            "root": str(root),
            "directory": str(directory),
            "control": None,
            "artifact": artifact,
            "sources": list(sources),
            "artifact_id": artifact_id,
            "deadline": deadline,
            "run_id": run_id,
        },
        ast,
    )
