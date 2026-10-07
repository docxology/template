"""Independent source-bound projected pages and EPUB native layout replay."""

from __future__ import annotations

import copy
import hashlib
import tempfile
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def replay_epub_observer(
    root: Path,
    directory: Path,
    scope: str,
    snapshot: ArtifactSnapshot,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
) -> None:
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster
    from infrastructure.reporting.native_format_observer_dispatch import _manuscript_contracts
    from infrastructure.reporting.native_epub_observer import (
        replay_epub_conversion,
        inspect_epub_spine,
        inspect_epub_reader_layout,
    )

    chapters = _manuscript_contracts(root, scope, reader)
    if raw.get("chapter_contracts") != [item.to_dict() for item in chapters]:
        raise ValueError("EPUB complete source chapter obligations differ")
    replay_epub_conversion(
        raw["conversion"],
        snapshot.content,
        read_artifact=lambda binding: _file(binding, reader).content,
        producer_path=lambda relative: str(producer_path(custody, root, root / relative)),
        run_id=run_id,
    )
    pdf = _file(raw["conversion"]["pdf"], reader)
    _raster(raw, pdf, 0, directory, reader, run_id, versions, custody)
    if raw.get("spine") != inspect_epub_spine(snapshot.content, chapters):
        raise ValueError("EPUB independent exact ordered spine source parity differs")
    observed = inspect_epub_reader_layout(
        pdf.content,
        tuple(_file(item, reader).content for item in raw["raster"]["rasters"]),
        chapters,
        deadline=deadline,
    )
    if raw.get("observation") != observed:
        raise ValueError("EPUB independent native glyph/geometry/pixel replay differs")


def replay_projection_observer(
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
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
) -> None:
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster
    from infrastructure.reporting.native_format_observer_validation import replay_office_conversion
    from infrastructure.reporting.native_projection_contracts import (
        compile_scope_projection_contract,
        projection_contract_record,
        ProjectionSourceUnsupported,
    )
    from infrastructure.reporting.native_projection_checks import inspect_projection

    try:
        pages = compile_scope_projection_contract(root, scope, artifact, reader)
    except ProjectionSourceUnsupported as error:
        expected = {"status": "blocked", "findings": [], "blockers": [str(error)]}
        if raw.get("observation") != expected or "projection_contract" in raw:
            raise ValueError("unsupported source projection was promoted to observed acceptance") from error
        return
    if raw.get("projection_contract") != projection_contract_record(pages):
        raise ValueError("projected page source obligations differ")
    layout = raw["observation"] if artifact.format == "pptx" else raw
    pdf = (
        replay_office_conversion(
            root, directory, snapshot, layout["conversion"], reader, run_id=run_id, custody=custody
        )
        if artifact.format == "pptx"
        else snapshot
    )
    _raster(layout, pdf, 0, directory, reader, run_id, versions, custody)
    rasters = tuple(_file(item, reader).content for item in layout["raster"]["rasters"])
    # Fresh reader-local decoder outputs are independently observed; only their
    # transport file bindings differ from the producer's original receipts.
    from infrastructure.reporting.native_qr_runtime import replay_projection_qr_runtime

    if len(layout["observation"]["pages"]) != len(rasters):
        raise ValueError("retained projection observations omit original page rasters")
    for ordinal, page in enumerate(layout["observation"]["pages"], 1):
        if "qr" in page:
            qr = page["qr"]
            expected_runtime = (directory / f"qr-runtime-{ordinal}.json").relative_to(root).as_posix()
            expected_tool = (directory / f"qr-decode-{ordinal}.json").relative_to(root).as_posix()
            expected_raster = (directory / f"qr-page-{ordinal}.png").relative_to(root).as_posix()
            if qr["runtime_artifact"]["path"] != expected_runtime or qr["tool_artifact"]["path"] != expected_tool:
                raise ValueError("retained QR receipts differ from original observer/page paths")
            consumed = _file({"path": expected_raster, "sha256": qr["raster_sha256"]}, reader)
            if (
                consumed.content != rasters[ordinal - 1]
                or consumed.sha256 != hashlib.sha256(rasters[ordinal - 1]).hexdigest()
            ):
                raise ValueError("retained native QR input differs from admitted page raster")
            replay_projection_qr_runtime(
                page["qr"],
                read_artifact=lambda binding: _file(binding, reader).content,
                producer_path=lambda relative: str(producer_path(custody, root, root / relative)),
                run_id=run_id,
            )
    with tempfile.TemporaryDirectory(prefix="projection-replay-") as private:
        temporary_root = Path(private).resolve()
        temporary_directory = temporary_root / "output/readiness/qr"
        temporary_directory.mkdir(parents=True, mode=0o700)
        observed = inspect_projection(
            pdf.content,
            rasters,
            pages,
            deadline=deadline,
            native_context=(temporary_root, temporary_directory, env, run_id),
        )
    recorded = copy.deepcopy(layout["observation"])
    independent = copy.deepcopy(observed)
    for value in (recorded, independent):
        for page in value["pages"]:
            if "qr" in page:
                page["qr"].pop("tool_artifact", None)
                page["qr"].pop("runtime_artifact", None)
    if recorded != independent:
        raise ValueError("independent projected glyph/figure/QR geometry/pixels differ")
