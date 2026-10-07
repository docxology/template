"""Portable native observer replay entry points; producer paths remain labels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_content_contracts import NativeContentContract
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

from infrastructure.reporting.native_format_browser_replay import (
    replay_browser_observation as replay_browser_observation,
    replay_browser_controls as replay_browser_controls,
)
from infrastructure.reporting.native_format_observer_source_replay import replay_html_source, replay_office_conversion


def replay_native_observer(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
) -> dict[str, Any]:
    """Independent current-source native observations for the actual artifact."""
    from infrastructure.reporting.native_format_observer_dispatch import OBSERVER_SCHEMA, _manuscript_contracts
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster
    from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content

    if (
        raw.get("schema_version") != OBSERVER_SCHEMA
        or raw.get("id") != artifact.id
        or raw.get("format") != artifact.format
        or raw.get("input") != {"path": snapshot.relative, "sha256": snapshot.sha256}
    ):
        raise ValueError("native observer identity differs from source-owned obligation")
    if artifact.format in {"pdf", "pptx"} and (artifact.id.endswith(":slides") or artifact.id.startswith("pitch:")):
        from infrastructure.reporting.native_format_observer_projection_replay import replay_projection_observer

        replay_projection_observer(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            raw,
            reader,
            run_id=run_id,
            custody=custody,
            versions=versions,
            deadline=deadline,
            env=env,
        )
    elif artifact.format == "pdf":
        from infrastructure.reporting.native_format_content_contracts import compile_pdf_content_contract

        contract = compile_pdf_content_contract(root, scope, artifact, reader, deadline=deadline)
        if raw.get("content_contract") != contract.to_dict():
            raise ValueError("PDF source contracts changed")
        _raster(raw, snapshot, 0, directory, reader, run_id, versions, custody)
        pixels = tuple(_file(item, reader).content for item in raw["raster"]["rasters"])
        observed = inspect_pdf_content(snapshot.content, pixels, contract, deadline=deadline)
        if raw.get("observation") != observed:
            raise ValueError("PDF independent glyph/geometry/pixel replay differs")
    elif artifact.format == "html":
        contract = replay_html_source(
            root,
            directory,
            scope,
            artifact,
            raw["semantic_source"],
            reader,
            run_id=run_id,
            custody=custody,
            deadline=deadline,
            env=env,
        )
        if raw.get("content_contract") != contract.to_dict():
            raise ValueError("HTML source contract changed")
        replay_browser_observation(
            root,
            directory,
            snapshot,
            contract,
            raw["observation"],
            reader,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
        )
    elif artifact.format == "docx":
        chapters = _manuscript_contracts(root, scope, reader)
        contract = NativeContentContract(
            artifact.id,
            tuple(item for chapter in chapters for item in chapter.sources),
            tuple(item for chapter in chapters for item in chapter.blocks),
            tuple(item for chapter in chapters for item in chapter.blockers),
        )
        layout = raw["observation"]
        converted = replay_office_conversion(
            root, directory, snapshot, layout["conversion"], reader, run_id=run_id, custody=custody
        )
        _raster(layout, converted, 0, directory, reader, run_id, versions, custody)
        observed = inspect_pdf_content(
            converted.content,
            tuple(_file(item, reader).content for item in layout["raster"]["rasters"]),
            contract,
            deadline=deadline,
        )
        if raw.get("content_contract") != contract.to_dict() or layout.get("observation") != observed:
            raise ValueError("DOCX independent source/layout replay differs")
    elif artifact.format == "epub":
        from infrastructure.reporting.native_format_observer_projection_replay import replay_epub_observer

        replay_epub_observer(
            root,
            directory,
            scope,
            snapshot,
            raw,
            reader,
            run_id=run_id,
            custody=custody,
            versions=versions,
            deadline=deadline,
        )
    else:
        raise ValueError("complete independent replay for this source projection is not implemented")
    return raw
