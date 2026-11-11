"""Run canonical exemplar export against an already admitted private snapshot."""

from __future__ import annotations

import json
import os
import sys
import time
import tempfile
from pathlib import Path

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.publishing.publication_tree import _Budget


def canonical_snapshot_export(
    snapshot: Path, project_rel: str, destination: Path, source_revision: str | None, budget: _Budget
) -> None:
    """Reuse canonical selection and resource bundling without reading the mutable origin.

    The caller has admitted every snapshot byte, mode and symbolic provider.
    The bounded child contains the canonical exporter's Git metadata probes;
    its snapshot has no repository and cannot discover an ancestor checkout.
    Current implementation imports are audited before execution, with a new
    empty bytecode prefix outside the copied source and post-execution checks.
    Only an admitted origin commit replaces the snapshot's ``unknown`` commit.
    """
    budget.check()
    environment = build_bounded_env()
    for name in tuple(environment):
        if name.startswith("GIT_") or name.startswith("PYTHON"):
            environment.pop(name)
    environment.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CEILING_DIRECTORIES=str(snapshot.parent),
        GIT_TERMINAL_PROMPT="0",
    )
    implementation = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="export-bytecode-", dir=snapshot.parent) as temporary:
        bytecode = Path(temporary).resolve()
        audit = bytecode_audit_bootstrap(
            (implementation / "infrastructure",),
            bytecode,
            audit_path=implementation / "infrastructure/core/bytecode_audit.py",
        )
        worker = (
            audit + "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
            "from infrastructure.project.copy_exemplar import export_exemplar; "
            "export_exemplar(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4])); "
            "_audit_scope['verify_executed_source_code'](Path(sys.argv[1])/'infrastructure',Path(sys.pycache_prefix))"
        )
        result = run_bounded_subprocess(
            [
                sys.executable,
                "-I",
                "-X",
                f"pycache_prefix={bytecode}",
                "-c",
                worker,
                str(implementation),
                str(snapshot),
                project_rel.removeprefix("projects/"),
                str(destination),
            ],
            cwd=snapshot,
            env=environment,
            timeout=max(0.001, budget.deadline - time.monotonic()),
        )
    if result.returncode != 0 or result.timed_out:
        raise ValueError("canonical standalone export failed within its finite execution budget")
    budget.check()
    manifest_path = destination / ".template-export.json"
    manifest = json.loads(read_bytes_confined(destination, manifest_path, max_bytes=64 * 1024 * 1024))
    if manifest.get("source_commit") != "unknown":
        raise ValueError("canonical snapshot unexpectedly acquired repository metadata")
    manifest["source_commit"] = source_revision or "unknown"
    content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    budget.check(len(content))
    atomic_write_bytes_confined(destination, manifest_path, content)
