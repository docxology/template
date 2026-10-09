"""Portable configured-print admission; producer font and tool paths are labels.

Original source scenes remain original authenticated worker observations. This
reader checks their complete closure and source obligations without selecting
or substituting fresh system fonts, or executing producer paths.
"""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from infrastructure.reporting.native_format_acceptance_checks import _read_pdf_rasters, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _tool
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
from infrastructure.reporting.native_newspaper_source import NewspaperReference, _texts
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams
from infrastructure.reporting.native_print_artifact_observer import (
    PRINT_SCOPES,
    PRINT_PLATFORMS,
    REFERENCE_SCHEMA,
    bounded_png_observation,
    configured_print_target,
    inspect_configured_print,
)
from infrastructure.reporting.native_print_font_custody import validate_print_fonts
from infrastructure.reporting.native_print_witness import source_inventory
from infrastructure.reporting.native_storybook_source import StorybookReference, source_identity, source_package
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _contact_tiles(reference: StorybookReference) -> None:
    """Independently verify every ordered thumbnail without loading any font."""
    with Image.open(BytesIO(reference.contact_sheet)) as sheet:
        thumbs = []
        for data in reference.pages:
            with Image.open(BytesIO(data)) as source_image:
                thumbnail = source_image.convert("RGB")
            thumbnail.thumbnail((320, 460), Image.Resampling.LANCZOS)
            thumbs.append(thumbnail)
        try:
            height = max(image.height for image in thumbs) + 58
            if sheet.size != (4 * 352, ((len(thumbs) + 3) // 4) * height):
                raise ValueError("original storybook contact geometry differs from source page closure")
            for index, image in enumerate(thumbs):
                x = (index % 4) * 352 + (352 - image.width) // 2
                y = (index // 4) * height + 8
                with sheet.crop((x, y, x + image.width, y + image.height)) as region:
                    if region.convert("RGB").tobytes() != image.tobytes():
                        raise ValueError("original storybook contact thumbnail order/pixels differ")
        finally:
            for image in thumbs:
                image.close()


def _admit_raster(
    raw: dict[str, Any],
    snapshot: ArtifactSnapshot,
    directory: Path,
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
) -> tuple[bytes, ...]:
    raster = raw.get("raster")
    if not isinstance(raster, dict) or set(raster) != {"dpi", "input_artifact", "rasters", "tool_artifacts"}:
        raise ValueError("configured print raster has incomplete native observations")
    rows = raster["rasters"]
    if not isinstance(rows, list) or len(rows) != parse_native_bytes("pdf", snapshot.content)["pages"]:
        raise ValueError("configured print raster omits actual PDF pages")
    files = [
        _file({"path": row.get("path"), "sha256": row.get("sha256")}, reader) for row in rows if isinstance(row, dict)
    ]
    if len(files) != len(rows) or _read_pdf_rasters(reader, [item.path for item in files], deadline=deadline) != rows:
        raise ValueError("configured print original raster bytes/geometry differ")
    _raster(raw, snapshot, 0, directory, reader, run_id, versions, custody)
    return tuple(item.content for item in files)


def admit_print_reference(
    root: Path,
    directory: Path,
    scope: str,
    binding: object,
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    expected_pid: int,
    expected_platform: str,
    deadline: float,
) -> tuple[StorybookReference | NewspaperReference, dict[str, Any]]:
    """Admit witnesses under the caller-authenticated original worker PID/OS.

    These expected values come from the admitted original controller and hosted
    origin when transported. Witness metadata cannot supply its own authority.
    """
    if time.monotonic() >= deadline:
        raise TimeoutError("portable configured print reference deadline")
    if (
        scope not in PRINT_SCOPES
        or type(expected_pid) is not int
        or expected_pid <= 0
        or type(expected_platform) is not str
        or expected_platform not in PRINT_PLATFORMS
    ):
        raise ValueError("configured print reference lacks actual worker/scope identity")
    kind = PRINT_SCOPES[scope]
    work = directory.parent / f"print-reference-{kind}"
    record = _file(binding, reader)
    raw = record.json_object()
    fields = {
        "schema_version",
        "scope",
        "run_id",
        "producer_root",
        "pid",
        "platform",
        "runtime",
        "source_before",
        "source_after",
        "fonts_before",
        "fonts_after",
        "interpreter_before",
        "interpreter_after",
        "source",
        "versions",
    }
    if (
        record.path != work / "source-reference.json"
        or set(raw) != fields
        or raw["schema_version"] != REFERENCE_SCHEMA
        or raw["scope"] != scope
        or raw["run_id"] != run_id
        or raw["pid"] != expected_pid
        or type(raw["pid"]) is not int
        or raw["producer_root"] != custody["root"]
        or raw["platform"] != expected_platform
        or raw["runtime"] != runtime
        or runtime.get("missing") != []
        or runtime.get("implementation") != "CPython"
        or runtime.get("python_version") not in {"3.12", "3.13", "3.14"}
    ):
        raise ValueError("configured print source witness differs from original authenticated worker")
    for name in ("interpreter_before", "interpreter_after"):
        validate_executable_observation(raw[name], runtime["executable"], runtime["interpreter_sha256"])
    if raw["source_before"] != source_inventory(root) or raw["source_before"] != raw["source_after"]:
        raise ValueError("configured print complete source/SDK custody differs")
    if raw["fonts_before"] != raw["fonts_after"]:
        raise ValueError("configured print original font selection changed")
    project = root / "projects" / scope
    validate_print_fonts(raw["fonts_before"], kind, project)
    source = raw["source"]
    if not isinstance(source, dict) or source.get("source_sha256") != source_identity(project):
        raise ValueError("configured print original source witness is stale")
    provider = source_package(project, kind)
    reference: StorybookReference | NewspaperReference
    if kind == "storybook":
        if (
            set(source) != {"source_sha256", "dimensions", "filenames", "pages", "contact_sheet"}
            or raw["versions"] != {}
        ):
            raise ValueError("storybook source scene closure is incomplete")
        spec = provider.load_storybook(project)
        names = [page.filename for page in spec.pages]
        if (
            source["dimensions"] != [spec.page_width, spec.page_height]
            or source["filenames"] != names
            or not isinstance(source["pages"], list)
            or len(source["pages"]) != len(names)
            or not 1 <= len(names) <= 32
        ):
            raise ValueError("storybook current source page identities differ")
        pages = []
        for index, item in enumerate(source["pages"]):
            page = _file(item, reader)
            png = bounded_png_observation(page.content)
            if page.path != work / f"page-{index:04d}.png" or (png["width_px"], png["height_px"]) != tuple(
                source["dimensions"]
            ):
                raise ValueError("storybook original source page geometry/path differs")
            pages.append(page.content)
        contact = _file(source["contact_sheet"], reader)
        if contact.path != work / "contact.png":
            raise ValueError("storybook original contact belongs to another attempt")
        bounded_png_observation(contact.content)
        reference = StorybookReference(
            source["source_sha256"], tuple(source["dimensions"]), tuple(names), tuple(pages), contact.content
        )
        _contact_tiles(reference)
        return reference, source
    if set(source) != {"source_sha256", "dimensions", "obligations", "pdf", "raster"}:
        raise ValueError("newspaper original source projection is incomplete")
    config = provider.load_newspaper_config(project / "content")
    edition = provider.load_edition(project / "content")
    obligations = [
        [text for text in _texts(page) if page.template != "front" or text != page.department] for page in edition.pages
    ]
    dimensions = [config.geometry().width, config.geometry().height]
    if source["dimensions"] != dimensions or source["obligations"] != obligations or not 1 <= len(obligations) <= 32:
        raise ValueError("newspaper current source text/page geometry differs")
    pdf = _file(source["pdf"], reader)
    if pdf.path != work / "source.pdf":
        raise ValueError("newspaper original source PDF belongs to another attempt")
    preflight_pdf_streams(pdf.content, deadline=deadline)
    versions = raw["versions"]
    if not isinstance(versions, dict) or set(versions) != {"pdftoppm", "pdffonts"}:
        raise ValueError("newspaper original raster tools are incomplete")
    admitted = {name: _tool(value, reader, run_id, name, f"version-{name}", ["-v"]) for name, value in versions.items()}
    _admit_raster(source, pdf, work, reader, run_id=run_id, custody=custody, versions=admitted, deadline=deadline)
    reference = NewspaperReference(
        source["source_sha256"], tuple(dimensions), pdf.content, tuple(tuple(row) for row in obligations)
    )
    return reference, source


def replay_print_artifact(
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
    expected_pid: int,
    expected_platform: str,
    deadline: float,
) -> dict[str, Any]:
    """Reconstruct admission from actual configured bytes and retained observations."""
    kind, page = configured_print_target(root, scope, artifact)
    fields = {"schema_version", "id", "format", "input", "print_reference", "observation"}
    if artifact.format == "pdf":
        fields.add("raster")
    if (
        set(raw) != fields
        or raw.get("schema_version") != "template-native-observer-dispatch-v1"
        or raw.get("id") != artifact.id
        or raw.get("format") != artifact.format
        or raw.get("input") != {"path": snapshot.relative, "sha256": snapshot.sha256}
        or snapshot.relative != artifact.path
        or snapshot.path != root / artifact.path
    ):
        raise ValueError("configured print replay was given a substitute native artifact")
    reference, source = admit_print_reference(
        root,
        directory,
        scope,
        raw["print_reference"],
        reader,
        run_id=run_id,
        custody=custody,
        runtime=runtime,
        expected_pid=expected_pid,
        expected_platform=expected_platform,
        deadline=deadline,
    )
    candidate_rasters: tuple[bytes, ...] = ()
    source_rasters: tuple[bytes, ...] = ()
    if artifact.format == "pdf":
        candidate_rasters = _admit_raster(
            raw, snapshot, directory, reader, run_id=run_id, custody=custody, versions=versions, deadline=deadline
        )
    if isinstance(reference, NewspaperReference):
        source_rasters = tuple(
            _file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in source["raster"]["rasters"]
        )
    observed = inspect_configured_print(
        snapshot.content,
        reference,
        kind=kind,
        page_number=page,
        candidate_rasters=candidate_rasters,
        source_rasters=source_rasters,
        deadline=deadline,
    )
    if raw["observation"] != observed:
        raise ValueError("configured print independent source/glyph/pixel replay differs")
    if not reader.unchanged():
        raise ValueError("configured print source/evidence changed during portable admission")
    return raw
