"""Reuse the actual complete candidate raster from the enclosing native run.

The genuine live producer or externally admitted Original supplies authority.
This reconstructs its full roster and ToolAPI checks; it never executes raster
tools, grants an owner or reads departed producer filesystem labels.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from infrastructure.rendering.config import RenderingConfig
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, native_artifact_contract
from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _tool
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def candidate_pdf_raster(
    scope: str,
    formats: tuple[str, ...],
    artifact: NativeArtifact,
    rows: list[dict[str, Any]],
    tools: list[dict[str, str]],
    reader: SnapshotReader,
    *,
    directory: Path,
    run_id: str,
    custody: dict[str, str],
) -> dict[str, Any]:
    """Verify the complete enclosing roster and exact original raster operands."""
    contract = native_artifact_contract(reader.root, scope, formats, reader)
    if len(rows) != len(contract) or any(
        {key: row.get(key) for key in ("id", "format", "path")}
        != {key: getattr(selected, key) for key in ("id", "format", "path")}
        for row, selected in zip(rows, contract, strict=True)
    ):
        raise ValueError("candidate raster reuse omitted/reordered the complete Source artifact contract")
    indices = [index for index, selected in enumerate(contract) if selected == artifact]
    if len(indices) != 1 or artifact.format != "pdf" or len(tools) != 4:
        raise ValueError("candidate raster reuse lacks its exact PDF role and full actual version probes")
    index = indices[0]
    row = rows[index]
    snapshot = _file({"path": artifact.path, "sha256": row["sha256"]}, reader)
    settings = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    if not isinstance(settings, dict):
        raise ValueError("candidate raster reuse lacks its held Source configuration")
    rendering = RenderingConfig.from_project_config(settings, env={})
    requests = (
        (rendering.pandoc_path, ["--version"]),
        (rendering.latex_compiler, ["--version"]),
        ("pdftoppm", ["-v"]),
        ("pdffonts", ["-v"]),
    )
    versions = {
        name: _tool(binding, reader, run_id, name, f"tool-version-{ordinal}", arguments)
        for ordinal, (binding, (name, arguments)) in enumerate(zip(tools, requests, strict=True))
    }
    _raster(row, snapshot, index, directory, reader, run_id, versions, custody)
    raster = row["raster"]
    if not isinstance(raster, dict):
        raise ValueError("candidate raster reuse lacks its actual complete raster object")
    # Return independent DATA so a caller cannot alter the enclosing raw row.
    retained = json.loads(json.dumps(raster, allow_nan=False))
    if not isinstance(retained, dict):
        raise ValueError("candidate raster retained DATA is not an object")
    return retained
