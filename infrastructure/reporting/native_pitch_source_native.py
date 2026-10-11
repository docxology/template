"""Actual complete source-only Pitch PDF layout/theme/ink and portable replay."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection
from infrastructure.reporting.native_pitch_source import compile_pitch_source_model
from infrastructure.reporting.native_projection_contracts import compile_projection_contract, projection_contract_record
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _write_pdf(
    root: Path,
    directory: Path,
    scope: str,
    artifact: Any,
    reader: SnapshotReader,
    tracked_paths: tuple[str, ...],
    deadline: float,
) -> tuple[Path, Any]:
    import yaml
    from infrastructure.rendering.slide_deck import DeckTheme, render_pdf
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    create_private_native_directory(root, directory)
    model, source_base = compile_pitch_source_model(
        root,
        scope,
        artifact,
        reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
    config = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    theme = DeckTheme(**config["project_config"]["deck"].get("theme", {}))
    path = render_pdf(model, directory / "source-model.pdf", theme=theme, source_base_url=source_base)
    return path, compile_projection_contract(model, source_base_url=source_base, reader=reader)


def observe_pitch_pdf_source_reference(
    root: Path,
    directory: Path,
    scope: str,
    artifact: Any,
    snapshot: ArtifactSnapshot,
    candidate_rasters: tuple[bytes, ...],
    reader: SnapshotReader,
    *,
    tracked_paths: tuple[str, ...],
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Conjoin genuine source-only native layout with the literal projection oracle.

    This full layout/theme comparison must not replace independent original
    text/font/image/citation/QR witnesses in inspect_projection. Both gates and
    original Source/SDK/PID/deadline custody are required for production.
    """
    if artifact.format != "pdf" or artifact.path != snapshot.relative:
        raise ValueError("Pitch source PDF reference requires exact current artifact identity")
    path, pages = _write_pdf(root, directory, scope, artifact, reader, tracked_paths, deadline)
    reference = reader.read(path.relative_to(root).as_posix())
    raster = audit_pdf_raster(
        root,
        directory,
        reference,
        parse_native_bytes("pdf", reference.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])
    observed = inspect_office_reference_projection(
        reference.content, pixels, snapshot.content, candidate_rasters, deadline=deadline
    )
    if time.monotonic() >= deadline or not reader.unchanged():
        raise ValueError("Pitch complete source-only native PDF custody changed or original deadline expired")
    return {
        "schema_version": "template-native-pitch-source-pdf-reference-v1",
        "input_sha256": snapshot.sha256,
        "projection_contract": projection_contract_record(pages),
        "source_pdf": {"path": reference.relative, "sha256": reference.sha256},
        "raster": raster,
        "native_projection": observed,
        "status": "fail" if observed["findings"] else "pass",
        "findings": observed["findings"],
        "blockers": [],
    }


def replay_pitch_pdf_source_reference(
    source_root: Path,
    scope: str,
    artifact: Any,
    candidate_pdf: bytes,
    candidate_rasters: tuple[bytes, ...],
    original: dict[str, Any],
    reader: SnapshotReader,
    *,
    tracked_paths: tuple[str, ...],
    read_artifact: Callable[[dict[str, str]], bytes],
    validate_original_tool: Callable[[dict[str, Any]], None],
    deadline: float,
) -> dict[str, Any]:
    """Rebuild current source-only PDF; original host paths/fonts are never reopened."""
    from infrastructure.core.pipeline.fingerprints import canonical_digest
    from infrastructure.reporting.native_office_reference_visual import native_page_projection

    source_pdf = read_artifact(original["source_pdf"])
    for tool in original["raster"]["tool_artifacts"]:
        validate_original_tool(json.loads(read_artifact(tool["artifact"])))
    source_rasters = tuple(
        read_artifact({"path": row["path"], "sha256": row["sha256"]}) for row in original["raster"]["rasters"]
    )
    # The fresh renderer reads current admitted source assets/configuration. It
    # writes only its temporary PDF; it imports only current selected SDK code.
    import yaml
    from infrastructure.rendering.slide_deck import DeckTheme, render_pdf

    model, source_base = compile_pitch_source_model(
        source_root,
        scope,
        artifact,
        reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
    config = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    theme = DeckTheme(**config["project_config"]["deck"].get("theme", {}))
    with tempfile.TemporaryDirectory(prefix="native-pitch-pdf-replay-") as private:
        rebuilt = render_pdf(model, Path(private) / "source.pdf", theme=theme, source_base_url=source_base).read_bytes()
    if canonical_digest(native_page_projection(rebuilt, source_rasters, deadline=deadline)) != canonical_digest(
        native_page_projection(source_pdf, source_rasters, deadline=deadline)
    ):
        raise ValueError("portable current source-only Pitch PDF glyph/font/image/link/layout differs")
    pages = compile_projection_contract(model, source_base_url=source_base, reader=reader)
    if original.get("projection_contract") != projection_contract_record(pages):
        raise ValueError("portable Pitch full layout reference source contract differs")
    observed = inspect_office_reference_projection(
        source_pdf, source_rasters, candidate_pdf, candidate_rasters, deadline=deadline
    )
    if original.get("native_projection") != observed:
        raise ValueError("portable Pitch complete source-only native PDF observations differ")
    if time.monotonic() >= deadline or not reader.unchanged():
        raise ValueError("portable Pitch source PDF DATA changed or original deadline expired")
    return {
        "native_projection": observed,
        "status": "fail" if observed["findings"] else "pass",
        "findings": observed["findings"],
        "blockers": [],
    }
