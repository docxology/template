"""Refresh or rebind one exemplar's rendered-provenance receipt.

`refresh` runs the canonical render and validation stages and then writes the
receipt. `rebind` revalidates unchanged rendered bytes and rewrites the receipt
for the current stage implementation, refusing any project whose tracked output
tree is dirty. The CLI wrapper stays thin; every producer invocation lives here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from infrastructure.core.pipeline.artifacts import (
    output_inventory_mode_for_project,
    snapshot_current_artifact_manifest,
)
from infrastructure.core.project_paths import resolve_project_root
from infrastructure.rendering.pipeline import execute_render_pipeline
from infrastructure.validation.output.pipeline import execute_validation_pipeline
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
from infrastructure.validation.publication.rendered_provenance import (
    RenderedProvenanceError,
    write_rendered_provenance_receipt,
)


def _manifest_paths(project_root: Path) -> set[str]:
    manifest = project_root / "output" / "reports" / "artifact_manifest.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
        return set()
    return {
        str(row["path"])
        for row in payload.get("entries", [])
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }


def refresh_project(name: str, root: Path) -> tuple[bool, str]:
    """Render, snapshot, validate and write one project's receipt."""
    project_root = resolve_project_root(root, name)
    old_paths = _manifest_paths(project_root)
    render_code = execute_render_pipeline(name, repo_root=root)
    if render_code != 0:
        # A refused render usually means the admitted analysis boundary no longer
        # matches the project data. `output/.pipeline` is disposable derived
        # state, so clear it, re-run the canonical analysis stage once and retry.
        import shutil

        shutil.rmtree(project_root / "output" / ".pipeline", ignore_errors=True)
        reanalysis = subprocess.run(
            [sys.executable, str(root / "scripts" / "pipeline" / "stage_02_analysis.py"), "--project", name],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if reanalysis.returncode == 0:
            render_code = execute_render_pipeline(name, repo_root=root)
        if render_code != 0:
            return False, "[RENDER_FAILED] canonical Stage 3 render failed after re-admitting the analysis boundary"
    try:
        manifest = snapshot_current_artifact_manifest(
            project_root / "output",
            inventory_mode=output_inventory_mode_for_project(root, project_root),
        )
        if execute_validation_pipeline(name, repo_root=root) != 0:
            return False, "[VALIDATION_FAILED] canonical Stage 4 validation failed"
        receipt = write_rendered_provenance_receipt(root, name)
    except (OSError, ValueError, RenderedProvenanceError) as error:
        code = error.code if isinstance(error, RenderedProvenanceError) else "IO_ERROR"
        return False, f"[{code}] {error}"
    new_paths = {entry.path for entry in manifest.entries}
    added, removed = len(new_paths - old_paths), len(old_paths - new_paths)
    return True, (
        f"{receipt.source.file_count} source, {receipt.config.file_count} config, "
        f"{receipt.output.file_count} output files; manifest +{added}/-{removed}"
    )


def _recorded_output_fingerprint(project_root: Path) -> str | None:
    receipt = project_root / "output" / "reports" / "rendered_provenance.json"
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
        return None
    fingerprints = payload.get("fingerprints")
    if not isinstance(fingerprints, dict):
        return None
    output = fingerprints.get("output")
    return output.get("sha256") if isinstance(output, dict) else None


def rebind_project(name: str, root: Path) -> tuple[bool, str]:
    """Revalidate unchanged rendered bytes and rewrite the receipt for current tooling.

    Safe only while the output tree still hashes to what the receipt recorded:
    rebinding never re-renders, so it must not silently attest new bytes.
    """
    project_root = resolve_project_root(root, name)
    recorded = _recorded_output_fingerprint(project_root)
    current = build_current_rendered_snapshot(root, name).output.sha256
    if recorded is None or recorded != current:
        return False, "rendered bytes changed since the receipt; run a full refresh"
    if execute_validation_pipeline(name, repo_root=root) != 0:
        return False, "[VALIDATION_FAILED] canonical Stage 4 validation failed"
    receipt = write_rendered_provenance_receipt(root, name)
    return True, f"rebound {receipt.output.file_count} output files"


def _worker(name: str, root_text: str, rebind: bool) -> tuple[bool, str]:
    root = Path(root_text)
    return rebind_project(name, root) if rebind else refresh_project(name, root)


def run(root: Path, names: list[str], *, jobs: int = 1, rebind: bool = False) -> list[tuple[str, bool, str]]:
    """Apply the requested operation to every project, optionally in worker processes."""
    if jobs < 1:
        raise ValueError("jobs must be a positive integer")
    action = rebind_project if rebind else refresh_project
    if jobs == 1 or len(names) == 1:
        return [(name, *action(name, root)) for name in names]
    results: list[tuple[str, bool, str]] = []
    with ProcessPoolExecutor(max_workers=min(jobs, len(names))) as pool:
        futures = {pool.submit(_worker, name, str(root), rebind): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            results.append((name, *future.result()))
    return results


__all__ = ["rebind_project", "refresh_project", "run"]
