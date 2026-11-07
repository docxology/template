"""Refresh or rebind one exemplar's rendered-provenance receipt.

`refresh` runs the canonical render and validation stages and then writes the
receipt. `rebind` revalidates unchanged rendered bytes and rewrites the receipt
for the current stage implementation, refusing any project whose tracked output
tree is dirty. The CLI wrapper stays thin; every producer invocation lives here.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from functools import partial
from pathlib import Path

from infrastructure.core.analysis_pipeline import execute_analysis_stage
from infrastructure.core.files.project_lock import owned_project_output_lock, project_output_lock
from infrastructure.core.pipeline.artifacts import (
    output_inventory_mode_for_project,
    snapshot_current_artifact_manifest,
)
from infrastructure.core.pipeline.hydration_recovery import HydrationRecoveryEvidence, supports_hydration_recovery
from infrastructure.core.project_paths import resolve_project_root
from infrastructure.core.secrets import strip_secret_env
from infrastructure.rendering._manuscript_source import run_manuscript_hydration
from infrastructure.rendering.pipeline import RenderPipelineDependencies, execute_render_pipeline
from infrastructure.validation.output.pipeline import execute_validation_pipeline
from infrastructure.validation.publication.rendered_provenance import (
    RenderedProvenanceError,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot


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


def _render_with_recovery(name: str, root: Path, project_root: Path, scope: str) -> str | None:
    evidence = HydrationRecoveryEvidence()
    render_dependencies = replace(
        RenderPipelineDependencies(),
        hydrate_manuscript=partial(run_manuscript_hydration, recovery_evidence=evidence),
    )
    render_code = execute_render_pipeline(name, repo_root=root, dependencies=render_dependencies)
    if render_code == 0:
        return None

    original_failure = f"[RENDER_FAILED] canonical Stage 3 render exited {render_code}"
    observation = evidence.observation
    if render_code != 1 or observation is None or not observation.matches_current(project_root):
        return original_failure

    environment = strip_secret_env()
    for key in ("PIPELINE_RUN_ID", "PIPELINE_PLAN_DIGEST", "PIPELINE_STAGE_KEY", "ANALYSIS_ALLOW_SECRETS"):
        environment.pop(key, None)
    analysis_code = execute_analysis_stage(root, scope, expected_project_root=project_root, base_env=environment)
    if analysis_code != 0:
        return f"{original_failure}; recovery Stage 02 exited {analysis_code}"

    if resolve_project_root(root, name) != project_root:
        return f"{original_failure}; selected project moved before retry"

    # Run the same Stage 3 with a fresh audited hydration leaf and no further
    # fallback. The first failed receipt and every older checkpoint stay intact.
    retry_dependencies = replace(
        render_dependencies,
        hydrate_manuscript=partial(run_manuscript_hydration, recovery_evidence=HydrationRecoveryEvidence()),
    )
    retry_code = execute_render_pipeline(name, repo_root=root, dependencies=retry_dependencies)
    return f"{original_failure}; recovery Stage 3 exited {retry_code}" if retry_code else None


def refresh_project(name: str, root: Path, *, analysis_recovery: bool = True) -> tuple[bool, str]:
    """Render, snapshot, validate and write one project's receipt."""
    project_root = resolve_project_root(root, name)
    scope = f"templates/{project_root.name}"
    recovery = (
        analysis_recovery
        and supports_hydration_recovery(scope)
        and project_root == root.resolve() / "projects" / scope
        and os.environ.get("RENDER_SECURITY_PROFILE", "trusted-local") == "trusted-local"
    )
    owner = owned_project_output_lock(project_root, timeout=30.0) if recovery else project_output_lock(project_root)
    try:
        with owner:
            if resolve_project_root(root, name) != project_root:
                return False, "[RENDER_FAILED] project moved before refresh acquired its output lock"
            return _refresh_locked(name, root, project_root, recovery_scope=scope if recovery else None)
    except (OSError, ValueError) as error:
        return False, f"[IO_ERROR] {error}"


def _refresh_locked(name: str, root: Path, project_root: Path, *, recovery_scope: str | None) -> tuple[bool, str]:
    old_paths = _manifest_paths(project_root)
    if recovery_scope is not None:
        failure = _render_with_recovery(name, root, project_root, recovery_scope)
        if failure is not None:
            return False, failure
    else:
        render_code = execute_render_pipeline(name, repo_root=root)
        if render_code != 0:
            return False, f"[RENDER_FAILED] canonical Stage 3 render exited {render_code}"
    if resolve_project_root(root, name) != project_root:
        return False, "[VALIDATION_FAILED] project moved before validation"
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
    with project_output_lock(project_root):
        if resolve_project_root(root, name) != project_root:
            return False, "[VALIDATION_FAILED] project moved before rebind acquired its output lock"
        return _rebind_locked(name, root, project_root)


def _rebind_locked(name: str, root: Path, project_root: Path) -> tuple[bool, str]:
    recorded = _recorded_output_fingerprint(project_root)
    current = build_current_rendered_snapshot(root, name).output.sha256
    if recorded is None or recorded != current:
        return False, "rendered bytes changed since the receipt; run a full refresh"
    if execute_validation_pipeline(name, repo_root=root) != 0:
        return False, "[VALIDATION_FAILED] canonical Stage 4 validation failed"
    receipt = write_rendered_provenance_receipt(root, name)
    return True, f"rebound {receipt.output.file_count} output files"


def _worker(name: str, root_text: str, rebind: bool, analysis_recovery: bool) -> tuple[bool, str]:
    root = Path(root_text)
    return rebind_project(name, root) if rebind else refresh_project(name, root, analysis_recovery=analysis_recovery)


def run(
    root: Path,
    names: list[str],
    *,
    jobs: int = 1,
    rebind: bool = False,
    analysis_recovery: bool = True,
) -> list[tuple[str, bool, str]]:
    """Apply the requested operation to every project, optionally in worker processes."""
    if jobs < 1:
        raise ValueError("jobs must be a positive integer")
    if jobs == 1 or len(names) == 1:
        return [(name, *_worker(name, str(root), rebind, analysis_recovery)) for name in names]
    results: list[tuple[str, bool, str]] = []
    with ProcessPoolExecutor(max_workers=min(jobs, len(names))) as pool:
        futures = {pool.submit(_worker, name, str(root), rebind, analysis_recovery): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            results.append((name, *future.result()))
    return results


__all__ = ["rebind_project", "refresh_project", "run"]
