"""Portable native observer replay entry points; producer paths remain labels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.reporting.native_pitch_source_admission import SourceCorrespondence

from infrastructure.reporting.native_office_mermaid_binding import OfficeMermaidReaderRuntime

from infrastructure.reporting.native_format_browser_replay import (
    replay_browser_observation as replay_browser_observation,
    replay_browser_controls as replay_browser_controls,
)
from infrastructure.reporting.native_format_observer_source_replay import (
    replay_office_conversion as replay_office_conversion,
)


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
    source_reference: PublicReference | None = None,
    verify_source_correspondence: SourceCorrespondence | None = None,
    office_mermaid_runtime: OfficeMermaidReaderRuntime | None = None,
) -> dict[str, Any]:
    """Independent current-source native observations for the actual artifact."""
    from infrastructure.reporting.native_format_observer_dispatch import OBSERVER_SCHEMA
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
            source_reference=source_reference,
            verify_source_correspondence=verify_source_correspondence,
        )
    elif artifact.format == "pdf":
        from infrastructure.reporting.native_format_content_contracts import compile_pdf_content_contract

        contract = compile_pdf_content_contract(root, scope, artifact, reader, deadline=deadline)
        if raw.get("content_contract") != contract.to_dict():
            raise ValueError("PDF source contracts changed")
        _raster(raw, snapshot, 0, directory, reader, run_id, versions, custody)
        pixels = tuple(
            _file({"path": item["path"], "sha256": item["sha256"]}, reader).content for item in raw["raster"]["rasters"]
        )
        observed = inspect_pdf_content(snapshot.content, pixels, contract, deadline=deadline)
        if raw.get("observation") != observed:
            raise ValueError("PDF independent glyph/geometry/pixel replay differs")
    elif artifact.format == "html":
        from infrastructure.reporting.native_format_html_admitted_source import replay_admitted_html_source

        contract, admitted = replay_admitted_html_source(
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
            source_reference=source_reference,
            verify_source_correspondence=verify_source_correspondence,
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
            metadata_source=admitted.metadata,
            admitted_source=admitted,
            deadline=deadline,
            env=env,
        )
        admitted.close(root, reader, deadline=deadline)
    elif artifact.format in {"docx", "epub"}:
        from infrastructure.reporting.native_office_full_replay import replay_office_full_source

        if set(raw) != {"schema_version", "id", "format", "input", "office_complete_source", "observation"}:
            raise ValueError("complete Office dispatch requires its exact original full-source fields")
        complete = raw["office_complete_source"]
        if not isinstance(complete, dict) or raw["observation"] != complete.get("observation"):
            raise ValueError("complete Office dispatch aggregate differs from the original full-source record")
        if source_reference is None or verify_source_correspondence is None:
            raise ValueError("portable complete Office source requires original source and current-mirror admission")
        if reader.root != root.resolve():
            raise ValueError("portable complete Office reader differs from its admitted current mirror")
        source_reference.verify_unchanged(deadline=deadline)
        verify_source_correspondence(source_reference, root, reader, deadline)
        replay_office_full_source(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            complete,
            reader,
            run_id=run_id,
            custody=custody,
            versions=versions,
            deadline=deadline,
            env=env,
            mermaid_runtime=office_mermaid_runtime,
        )
        verify_source_correspondence(source_reference, root, reader, deadline)
        source_reference.verify_unchanged(deadline=deadline)
    else:
        raise ValueError("complete independent replay for this source projection is not implemented")
    return raw
