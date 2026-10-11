"""Public artifact context for a bound human review."""

from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_text_confined, read_bytes_confined
from infrastructure.core.pipeline.types import StageSpec, StageContract
from infrastructure.core.pipeline.fingerprints import paths_digest, canonical_digest
from infrastructure.core.pipeline.artifact_contracts import declared_input_paths
from infrastructure.core.pipeline.artifacts import declared_output_paths


def reviewed_content_digest(
    output_dir: Path,
    input_artifacts: tuple[str, ...],
    repo_root: Path | None = None,
    output_artifacts: tuple[str, ...] = (),
    *,
    project_dir: Path | None = None,
) -> str:
    """Bind human review to consumed bytes as well as generated artifacts."""
    project_dir = project_dir if project_dir is not None else output_dir.parent
    deliverables = project_dir / "output"
    root = repo_root or next(
        (parent.parent for parent in project_dir.parents if parent.name == "projects"), project_dir.parent
    )
    paths = declared_input_paths(root, project_dir, StageContract(input_artifacts=input_artifacts))
    inputs = [
        (
            raw,
            paths_digest(
                (path,),
                source=not path.absolute().is_relative_to(deliverables.absolute()),
                excluded_roots=frozenset({deliverables.absolute()}),
                output_roots=(deliverables,),
            ),
        )
        for raw, path in zip(input_artifacts, paths, strict=True)
    ]
    outputs = declared_output_paths(root, project_dir, StageContract(output_artifacts=output_artifacts))
    return canonical_digest(
        {
            "artifacts": paths_digest((deliverables,), control_output=True),
            "inputs": inputs,
            "declared_outputs": paths_digest(outputs, control_output=True),
        }
    )


def _stage_contract_payload(stage_spec: StageSpec | None) -> dict[str, Any]:
    if stage_spec is None:
        return {}
    return asdict(stage_spec.contract)


def _declared_artifact_payloads(
    output_dir: Path,
    stage_spec: StageSpec | None,
    *,
    project_dir: Path | None = None,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    if stage_spec is None:
        return []
    payloads: list[dict[str, Any]] = []
    project = project_dir if project_dir is not None else output_dir.parent
    root = repo_root or next((parent.parent for parent in project.parents if parent.name == "projects"), project.parent)
    paths = declared_output_paths(root, project, stage_spec.contract)
    for raw, path in zip(stage_spec.contract.output_artifacts, paths, strict=True):
        row: dict[str, Any] = {
            "declared": raw,
            "path": _display_path(output_dir, path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        }
        if path.exists() and path.is_file():
            confinement = project if path.absolute().is_relative_to(project.absolute()) else root
            row["sha256"] = hashlib.sha256(read_bytes_confined(confinement, path)).hexdigest()
        payloads.append(row)
    return payloads


def _display_path(output_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(output_dir))
    except ValueError:
        return str(path)


def _validation_status(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "reports" / "validation_report.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text_confined(output_dir, path))
    except json.JSONDecodeError:
        return {"error": "invalid validation_report.json"}
    if not isinstance(payload, dict):
        return {"error": "validation_report.json must be an object"}
    return {
        "checks": payload.get("checks", {}),
        "summary": payload.get("summary", {}),
        "output_statistics": payload.get("output_statistics", {}),
    }


def _guidance_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in history if row.get("action") == "guide"]
