"""Source print witnesses bound to configured pipeline outputs, never surrogates.

The enclosing native worker authenticates source, runtime and decoder custody.
Installed fonts are observed before/after reference rendering and never copied.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import sys
import time
import zlib
from pathlib import Path
from typing import Any

from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.project.public_acceptance_evidence import runtime_identity, write_json
from infrastructure.reporting.native_format_acceptance_checks import (
    audit_pdf_raster,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, create_private_native_directory
from infrastructure.reporting.native_format_portable_custody import executable_observation
from infrastructure.reporting.native_newspaper_source import (
    NewspaperReference,
    _fonts,
    _glyphs,
    build_newspaper_reference,
)
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams
from infrastructure.reporting.native_print_font_custody import observe_print_fonts
from infrastructure.reporting.native_print_witness import source_inventory
from infrastructure.reporting.native_storybook_source import (
    StorybookReference,
    build_storybook_reference,
    inspect_storybook_artifact,
    pixels,
    read_source_yaml,
    source_package,
)
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

REFERENCE_SCHEMA = "template-configured-print-reference-v1"
PRINT_SCOPES = {"templates/template_storybook": "storybook", "templates/template_newspaper": "newspaper"}
PRINT_PLATFORMS = frozenset({"Linux", "Darwin"})
FINDING = "configured-print-source-parity"


def bounded_png_observation(content: bytes) -> dict[str, Any]:
    """Decode only bounded RGB PNGs with supported explicit color semantics."""
    if not 45 <= len(content) <= 64 * 1024 * 1024 or content[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("native PNG lacks a bounded exact container")
    chunks: list[bytes]
    offset, chunks, total_data = 8, [], 0
    compressed = []
    expected_scanlines = 0
    while offset < len(content):
        if offset + 12 > len(content):
            raise ValueError("native PNG has a truncated chunk")
        size = int.from_bytes(content[offset : offset + 4], "big")
        label = content[offset + 4 : offset + 8]
        end = offset + 12 + size
        if end > len(content) or label not in {b"IHDR", b"IDAT", b"IEND"}:
            raise ValueError("native PNG has unsupported animation/color/ancillary chunks")
        payload = content[offset + 8 : offset + 8 + size]
        if zlib.crc32(label + payload) != int.from_bytes(content[end - 4 : end], "big"):
            raise ValueError("native PNG chunk CRC differs")
        if label == b"IHDR":
            if chunks or size != 13:
                raise ValueError("native PNG header is repeated or malformed")
            width, height = int.from_bytes(payload[:4], "big"), int.from_bytes(payload[4:8], "big")
            if not width or not height or width * height > 10_000_000 or payload[8:] != b"\x08\x02\x00\x00\x00":
                raise ValueError("native PNG exceeds pixel budget or unsupported RGB/interlace semantics")
            expected_scanlines = height * (3 * width + 1)
        elif not chunks or chunks[-1] == b"IEND":
            raise ValueError("native PNG chunk order differs")
        if label == b"IDAT":
            total_data += size
            compressed.append(payload)
        if label == b"IEND" and (size or end != len(content)):
            raise ValueError("native PNG has malformed ending or trailing bytes")
        chunks.append(label)
        offset = end
    if len(chunks) < 3 or chunks[0] != b"IHDR" or chunks[-1] != b"IEND" or not total_data:
        raise ValueError("native PNG complete image data/ending is missing")
    decoder, decoded_size = zlib.decompressobj(), 0
    try:
        for payload in compressed:
            decoded_size += len(decoder.decompress(payload, expected_scanlines - decoded_size + 1))
            if decoded_size > expected_scanlines or decoder.unconsumed_tail or decoder.unused_data:
                raise ValueError("native PNG inflated stream exceeds exact finite scanline bound")
    except zlib.error as error:
        raise ValueError("native PNG invalid compressed scanline stream") from error
    if not decoder.eof or decoded_size != expected_scanlines:
        raise ValueError("native PNG compressed stream omits exact image scanlines")
    dimensions, decoded = pixels(content)
    return {
        "width_px": dimensions[0],
        "height_px": dimensions[1],
        "mode": "RGB",
        "pixels_sha256": hashlib.sha256(decoded).hexdigest(),
    }


def selected_print_artifact(scope: str, artifact: NativeArtifact) -> bool:
    """Select source-declared print roles before generic manuscript dispatch.

    Selection grants no path or format admission: configured_print_target then
    requires the exact current configured output before any observation.
    """
    if scope == "templates/template_newspaper":
        return artifact.id == "newspaper:edition:pdf"
    if scope == "templates/template_storybook":
        return (
            artifact.id in {"storybook:print:pdf", "storybook:contact-sheet"}
            or re.fullmatch(r"storybook:page:(0|[1-9][0-9]*)", artifact.id) is not None
        )
    return False


def configured_print_target(root: Path, scope: str, artifact: NativeArtifact) -> tuple[str, int | None]:
    """Bind each specialized obligation to its exact current configured path."""
    if scope not in PRINT_SCOPES:
        raise ValueError("unknown configured print scope")
    project = root / "projects" / scope
    base = f"projects/{scope}"
    if PRINT_SCOPES[scope] == "newspaper":
        manifest = read_source_yaml(project / "content/edition.yaml")
        name = manifest.get("render", {}).get("output_basename", "the-triplicate")
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) is None:
            raise ValueError("unsupported configured newspaper output name")
        if (artifact.id, artifact.format, artifact.path) != (
            "newspaper:edition:pdf",
            "pdf",
            f"{base}/output/pdf/{name}.pdf",
        ):
            raise ValueError("artifact is not the configured newspaper edition")
        return "pdf", None
    provider = source_package(project, "storybook")
    spec = provider.load_storybook(project)
    if artifact.id == "storybook:print:pdf":
        wanted = ("pdf", f"{base}/{spec.output_pdf.as_posix()}")
        kind, page = "pdf", None
    elif artifact.id == "storybook:contact-sheet":
        wanted = ("png", f"{base}/output/figures/storybook_contact_sheet.png")
        kind, page = "contact-sheet", None
    elif re.fullmatch(r"storybook:page:(0|[1-9][0-9]*)", artifact.id):
        page = int(artifact.id.rsplit(":", 1)[1])
        if not 0 <= page < len(spec.pages):
            raise ValueError("configured storybook page identity is outside source")
        wanted = ("png", f"{base}/output/figures/storybook_pages/{spec.pages[page].filename}")
        kind = "page"
    else:
        raise ValueError("artifact is not a configured storybook print/page/contact obligation")
    if (artifact.format, artifact.path) != wanted:
        raise ValueError("configured print artifact path/format differs from current source")
    return kind, page


def _source_reference(
    root: Path,
    directory: Path,
    scope: str,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, str]:
    """Retain one fresh source witness per scope under this original attempt."""
    kind = PRINT_SCOPES[scope]
    work = directory.parent / f"print-reference-{kind}"
    record = work / "source-reference.json"
    if record.exists():
        snapshot = reader.read(record.relative_to(root).as_posix())
        raw = snapshot.json_object()
        if raw.get("run_id") != run_id or raw.get("pid") != os.getpid() or raw.get("platform") != platform.system():
            raise ValueError("print reference belongs to another worker/attempt")
        return {"path": snapshot.relative, "sha256": snapshot.sha256}
    observed_platform = platform.system()
    if observed_platform not in PRINT_PLATFORMS:
        raise ValueError("configured print/font source witness requires a supported Linux or Darwin producer")
    if time.monotonic() >= deadline:
        raise TimeoutError("configured print source reconstruction deadline")
    create_private_native_directory(root, work)
    project = root / "projects" / scope
    before = source_inventory(root, original=True)
    fonts = observe_print_fonts(project, kind)
    interpreter = executable_observation(Path(sys.executable))
    runtime = runtime_identity()
    versions: dict[str, Any] = {}
    source: dict[str, Any]
    if kind == "storybook":
        story = build_storybook_reference(project, work / "source", deadline=deadline)
        source = {
            "source_sha256": story.source_sha256,
            "dimensions": list(story.dimensions),
            "filenames": list(story.filenames),
            "pages": [
                write_binary(root, work / f"page-{index:04d}.png", data) for index, data in enumerate(story.pages)
            ],
            "contact_sheet": write_binary(root, work / "contact.png", story.contact_sheet),
        }
    else:
        newspaper = build_newspaper_reference(project, work / "source", deadline=deadline)
        source = {
            "source_sha256": newspaper.source_sha256,
            "dimensions": list(newspaper.dimensions),
            "obligations": [list(page) for page in newspaper.obligations],
            "pdf": write_binary(root, work / "source.pdf", newspaper.pdf),
        }
        preflight_pdf_streams(newspaper.pdf, deadline=deadline)
        for name in ("pdftoppm", "pdffonts"):
            tool = native_tool_record(
                root, work, name, ["-v"], env=env, deadline=deadline, run_id=run_id, purpose=f"version-{name}"
            )
            if tool["exit_code"] != 0 or tool["original_exit_code"] != 0:
                raise ValueError("configured print raster tool version failed")
            versions[name] = tool["artifact"]
        snapshot = reader.read(source["pdf"]["path"])
        source["raster"] = audit_pdf_raster(
            root,
            work,
            snapshot,
            parse_native_bytes("pdf", newspaper.pdf),
            env=env,
            deadline=deadline,
            run_id=run_id,
            ordinal=0,
        )
    after_fonts = observe_print_fonts(project, kind)
    after = source_inventory(root, original=True)
    after_interpreter = executable_observation(Path(sys.executable))
    if (
        before != after
        or fonts != after_fonts
        or interpreter != after_interpreter
        or platform.system() != observed_platform
    ):
        raise ValueError("configured print source/font/interpreter changed during reference rendering")
    return write_json(
        root,
        record,
        {
            "schema_version": REFERENCE_SCHEMA,
            "scope": scope,
            "run_id": run_id,
            "producer_root": str(root.resolve()),
            "pid": os.getpid(),
            "platform": observed_platform,
            "runtime": runtime,
            "source_before": before,
            "source_after": after,
            "fonts_before": fonts,
            "fonts_after": after_fonts,
            "interpreter_before": interpreter,
            "interpreter_after": after_interpreter,
            "source": source,
            "versions": versions,
        },
    )


def inspect_configured_print(
    content: bytes,
    reference: StorybookReference | NewspaperReference,
    *,
    kind: str,
    page_number: int | None = None,
    candidate_rasters: tuple[bytes, ...] = (),
    source_rasters: tuple[bytes, ...] = (),
    deadline: float,
) -> dict[str, Any]:
    """Read actual source text, glyph/resource geometry and every decoded pixel."""
    if time.monotonic() >= deadline:
        raise TimeoutError("configured print artifact inspection deadline")
    try:
        if isinstance(reference, StorybookReference):
            if kind == "pdf":
                preflight_pdf_streams(content, deadline=deadline)
            else:
                bounded_png_observation(content)
            projection = inspect_storybook_artifact(content, reference, kind=kind, page_number=page_number)
        else:
            if kind != "pdf":
                raise ValueError("newspaper native artifact must be PDF")
            preflight_pdf_streams(content, deadline=deadline)
            preflight_pdf_streams(reference.pdf, deadline=deadline)
            if _fonts(content) != _fonts(reference.pdf) or _glyphs(content, reference) != _glyphs(
                reference.pdf, reference
            ):
                raise ValueError("newspaper actual source font/glyph geometry differs")
            if len(candidate_rasters) != len(reference.obligations) or len(source_rasters) != len(
                reference.obligations
            ):
                raise ValueError("newspaper actual complete raster pages were omitted")
            if any(pixels(a) != pixels(b) for a, b in zip(candidate_rasters, source_rasters, strict=True)):
                raise ValueError("newspaper actual source page pixels differ")
            projection = {
                "schema_version": "template-newspaper-print-projection-v1",
                "source_sha256": reference.source_sha256,
                "artifact_sha256": hashlib.sha256(content).hexdigest(),
                "pages": len(reference.obligations),
            }
    except ValueError as error:
        return {"status": "fail", "findings": [{"code": FINDING, "message": str(error)}], "blockers": []}
    return {"status": "pass", "findings": [], "blockers": [], "projection": projection}


def observe_print_artifact(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Observe the caller's exact configured output; only references are rendered."""
    kind, page = configured_print_target(root, scope, artifact)
    if snapshot.relative != artifact.path or snapshot.path != root / artifact.path:
        raise ValueError("configured print observer received a substitute artifact")
    binding = _source_reference(root, directory, scope, reader, env=env, deadline=deadline, run_id=run_id)
    from infrastructure.reporting.native_print_artifact_replay import admit_print_reference

    reference, source = admit_print_reference(
        root,
        directory,
        scope,
        binding,
        reader,
        run_id=run_id,
        custody={"root": str(root.resolve())},
        runtime=runtime_identity(),
        expected_pid=os.getpid(),
        expected_platform=platform.system(),
        deadline=deadline,
    )
    observed: dict[str, Any] = {"print_reference": binding}
    candidate_rasters: tuple[bytes, ...] = ()
    source_rasters: tuple[bytes, ...] = ()
    if artifact.format == "pdf":
        observed["raster"] = audit_pdf_raster(
            root,
            directory,
            snapshot,
            parse_native_bytes("pdf", snapshot.content),
            env=env,
            deadline=deadline,
            run_id=run_id,
            ordinal=0,
        )
        candidate_rasters = tuple(reader.read(item["path"]).content for item in observed["raster"]["rasters"])
    if isinstance(reference, NewspaperReference):
        source_rasters = tuple(reader.read(item["path"]).content for item in source["raster"]["rasters"])
    observed["observation"] = inspect_configured_print(
        snapshot.content,
        reference,
        kind=kind,
        page_number=page,
        candidate_rasters=candidate_rasters,
        source_rasters=source_rasters,
        deadline=deadline,
    )
    return observed
