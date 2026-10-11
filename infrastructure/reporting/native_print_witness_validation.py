"""Independent portable print witness admission without producer font access."""

from __future__ import annotations

import re
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from infrastructure.project.native_format_library_custody import validate_native_library_custody
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes, _read_pdf_rasters
from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard
from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _tool
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
from infrastructure.reporting.native_newspaper_source import NewspaperReference, _fonts, _glyphs, _texts
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams
from infrastructure.reporting.native_print_font_custody import validate_print_fonts
from infrastructure.reporting.native_storybook_source import (
    StorybookReference,
    inspect_storybook_artifact,
    source_identity,
    source_package,
)
from infrastructure.reporting.native_print_witness import KINDS, SCHEMA, source_inventory
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def validate_print_witness(
    binding: object,
    reader: SnapshotReader,
    *,
    expected_pid: int,
    expected_runtime: dict[str, Any],
    deadline: float | None = None,
) -> None:
    """Reparse exact source/native bytes under original auxiliary/hosted custody.

    This checker does not authenticate a remote execution by itself. Its caller
    binds the original child and the existing same-run/SHA hosted artifact.
    The reader never opens fonts, decoder files or tool paths from the producer.
    """
    deadline = time.monotonic() + 180 if deadline is None else deadline
    with native_deadline_guard(deadline):
        record = _file(binding, reader)
        raw = record.json_object()
        names = {
            "schema_version",
            "run_id",
            "producer_root",
            "pid",
            "platform",
            "runtime",
            "interpreter_before",
            "interpreter_after",
            "source_before",
            "source_after",
            "fonts_before",
            "fonts_after",
            "library_before",
            "library_after",
            "versions",
            "prints",
            "raster_artifacts",
        }
        producer_root = raw.get("producer_root")
        nonce = raw.get("run_id")
        if (
            set(raw) != names
            or raw["schema_version"] != SCHEMA
            or raw["platform"] != "Darwin"
            or type(raw["pid"]) is not int
            or raw["pid"] != expected_pid
            or not isinstance(nonce, str)
            or re.fullmatch(r"[0-9a-f]{32}", nonce) is None
            or not isinstance(producer_root, str)
            or not Path(producer_root).is_absolute()
            or str(Path(producer_root)) != producer_root
            or ".." in Path(producer_root).parts
            or "\\" in producer_root
            or "\0" in producer_root
        ):
            raise ValueError("original Darwin print witness lacks exact worker/source custody")
        runtime = raw["runtime"]
        if (
            not isinstance(runtime, dict)
            or runtime.get("missing") != []
            or runtime.get("implementation") != "CPython"
            or runtime.get("python_version") not in {"3.12", "3.13", "3.14"}
            or runtime.get("executable") != expected_runtime.get("executable")
            or runtime.get("python_full_version") != expected_runtime.get("python_version")
        ):
            raise ValueError("original print runtime differs from the actual auxiliary worker")
        for key in ("interpreter_before", "interpreter_after"):
            validate_executable_observation(raw[key], runtime["executable"], runtime["interpreter_sha256"])
        if raw["source_before"] != source_inventory(reader.root) or raw["source_after"] != raw["source_before"]:
            raise ValueError("complete print source/SDK inventory differs or changed")
        validate_native_library_custody(
            raw["library_before"], raw["library_after"], formats=("pdf",), reader=reader, runtime=runtime
        )
        if (
            not isinstance(raw["fonts_before"], dict)
            or set(raw["fonts_before"]) != set(KINDS)
            or raw["fonts_before"] != raw["fonts_after"]
        ):
            raise ValueError("original complete font selection changed or was omitted")
        for kind in KINDS:
            validate_print_fonts(raw["fonts_before"][kind], kind, reader.root / f"projects/templates/template_{kind}")
        versions = raw["versions"]
        if not isinstance(versions, dict) or set(versions) != {"pdftoppm", "pdffonts"}:
            raise ValueError("original complete raster tool selection is missing")
        versions = {
            name: _tool(value, reader, nonce, name, f"version-{name}", ["-v"]) for name, value in versions.items()
        }
        rows = raw["prints"]
        if not isinstance(rows, list) or [row.get("kind") for row in rows if isinstance(row, dict)] != list(KINDS):
            raise ValueError("original print editions are missing, reordered or duplicated")
        raster_artifacts: list[dict[str, Any]] = []
        for row in rows:
            groups = [row.get("raster", {})] + (
                [row.get("source", {}).get("raster", {})] if row["kind"] == "newspaper" else []
            )
            for group in groups:
                raster_artifacts.extend(
                    {"path": page.get("path"), "sha256": page.get("sha256")}
                    for page in group.get("rasters", [])
                    if isinstance(page, dict)
                )
        if raw["raster_artifacts"] != raster_artifacts:
            raise ValueError("complete original print page artifact closure is missing or changed")
        for artifact in raster_artifacts:
            _file(artifact, reader)
        custody = {"root": producer_root}
        for ordinal, row in enumerate(rows):
            if set(row) != {"kind", "artifact", "observation", "source", "semantic", "raster"}:
                raise ValueError("original print edition has extra or missing native observations")
            kind = row["kind"]
            project = reader.root / f"projects/templates/template_{kind}"
            directory = record.path.parent / kind
            candidate = _file(row["artifact"], reader)
            if candidate.path != directory / "candidate.pdf":
                raise ValueError("native print artifact belongs to another attempt")
            preflight_pdf_streams(
                candidate.content,
                deadline=deadline,
                max_bytes=250 * 1024 * 1024 if kind == "storybook" else 64 * 1024 * 1024,
            )
            observation = parse_native_bytes("pdf", candidate.content)
            if row["observation"] != observation:
                raise ValueError("original print page inventory differs from actual PDF bytes")
            _admit_raster(row, candidate, ordinal, directory, reader, nonce, versions, custody, deadline)
            source = row["source"]
            if not isinstance(source, dict) or source.get("source_sha256") != source_identity(project):
                raise ValueError("native print reference differs from current public source")
            provider = source_package(project, kind)
            if kind == "storybook":
                if set(source) != {"source_sha256", "dimensions", "filenames", "pages", "contact_sheet"}:
                    raise ValueError("storybook source reference is incomplete")
                spec = provider.load_storybook(project)
                filenames = [page.filename for page in spec.pages]
                if (
                    source["dimensions"] != [spec.page_width, spec.page_height]
                    or source["filenames"] != filenames
                    or not isinstance(source["pages"], list)
                    or len(source["pages"]) != len(spec.pages)
                ):
                    raise ValueError("storybook source page identity differs")
                pages = tuple(_file(item, reader).content for item in source["pages"])
                reference = StorybookReference(
                    source["source_sha256"],
                    tuple(source["dimensions"]),
                    tuple(filenames),
                    pages,
                    _file(source["contact_sheet"], reader).content,
                )
                if row["semantic"] != inspect_storybook_artifact(candidate.content, reference, kind="pdf"):
                    raise ValueError("storybook native source/image projection differs")
            else:
                _newspaper(
                    row, candidate, project, provider, directory, reader, ordinal, nonce, versions, custody, deadline
                )
        if not reader.unchanged():
            raise ValueError("native print source/evidence changed during independent readback")


def _admit_raster(
    row: dict[str, Any],
    snapshot: Any,
    ordinal: int,
    directory: Path,
    reader: SnapshotReader,
    nonce: str,
    versions: dict[str, Any],
    custody: dict[str, str],
    deadline: float,
) -> None:
    raster = row.get("raster")
    if not isinstance(raster, dict) or set(raster) != {"dpi", "input_artifact", "rasters", "tool_artifacts"}:
        raise ValueError("native print raster has incomplete or extra observations")
    images = raster["rasters"]
    if not isinstance(images, list) or len(images) != row["observation"]["pages"]:
        raise ValueError("native print raster omits actual pages")
    paths = [
        _file({"path": image.get("path"), "sha256": image.get("sha256")}, reader).path
        for image in images
        if isinstance(image, dict)
    ]
    # Admit encoded closure and PNG headers before any full image load.
    if len(paths) != len(images) or _read_pdf_rasters(reader, paths, deadline=deadline) != images:
        raise ValueError("native print raster bytes or page facts differ")
    _raster(row, snapshot, ordinal, directory, reader, nonce, versions, custody)


def _newspaper(
    row: dict[str, Any],
    candidate: Any,
    project: Path,
    provider: Any,
    directory: Path,
    reader: SnapshotReader,
    ordinal: int,
    nonce: str,
    versions: dict[str, Any],
    custody: dict[str, str],
    deadline: float,
) -> None:
    source = row["source"]
    if set(source) != {"source_sha256", "dimensions", "obligations", "pdf", "raster"}:
        raise ValueError("newspaper source reference is incomplete")
    config = provider.load_newspaper_config(project / "content")
    edition = provider.load_edition(project / "content")
    dimensions = [config.geometry().width, config.geometry().height]
    obligations = [
        [text for text in _texts(page) if page.template != "front" or text != page.department] for page in edition.pages
    ]
    if source["dimensions"] != dimensions or source["obligations"] != obligations:
        raise ValueError("newspaper current source text/geometry obligations differ")
    pdf = _file(source["pdf"], reader)
    if pdf.path != directory / "source.pdf":
        raise ValueError("newspaper native source PDF belongs to another attempt")
    preflight_pdf_streams(pdf.content, deadline=deadline)
    reference = NewspaperReference(
        source["source_sha256"], tuple(dimensions), pdf.content, tuple(tuple(page) for page in obligations)
    )
    if _fonts(candidate.content) != _fonts(pdf.content) or _glyphs(candidate.content, reference) != _glyphs(
        pdf.content, reference
    ):
        raise ValueError("newspaper original source font/glyph projection differs")
    _admit_raster(
        {"raster": source["raster"], "observation": parse_native_bytes("pdf", pdf.content)},
        pdf,
        ordinal + len(KINDS),
        directory,
        reader,
        nonce,
        versions,
        custody,
        deadline,
    )
    for actual, expected in zip(row["raster"]["rasters"], source["raster"]["rasters"], strict=True):
        with (
            Image.open(BytesIO(reader.read(actual["path"]).content)) as a,
            Image.open(BytesIO(reader.read(expected["path"]).content)) as b,
        ):
            if a.size != b.size or a.convert("RGB").tobytes() != b.convert("RGB").tobytes():
                raise ValueError("newspaper original source page pixels differ")
    semantic = row["semantic"]
    if (
        not isinstance(semantic, dict)
        or set(semantic) != {"schema_version", "source_sha256", "artifact_sha256", "pages"}
        or semantic["schema_version"] != "template-newspaper-print-projection-v1"
        or semantic["source_sha256"] != source["source_sha256"]
        or semantic["artifact_sha256"] != candidate.sha256
        or semantic["pages"] != len(obligations)
    ):
        raise ValueError("newspaper original semantic projection is incomplete")
