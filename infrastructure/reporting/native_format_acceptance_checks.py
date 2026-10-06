"""Strict native byte parsers and actual bounded PDF tool observations."""

from __future__ import annotations

import hashlib
import math
import shutil
import re
import time
import zipfile
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import ParseError

from defusedxml.ElementTree import fromstring
from defusedxml.common import DefusedXmlException
from pypdf.errors import PyPdfError

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.secure_write import read_bytes_confined, atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_contracts import TOOL_SCHEMA
from infrastructure.reporting.release_readiness_artifacts import bounded_members
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, ArtifactSnapshot


class NativeToolUnavailable(RuntimeError):
    """A positively identified installed native tool is unavailable."""


class _HTMLDocument(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html = self.body = self.body_seen = False
        self.body_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "html":
            self.html = True
        if tag == "body":
            self.body = self.body_seen = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "body":
            self.body = False

    def handle_data(self, data: str) -> None:
        if self.body and data.strip():
            self.body_text.append(data.strip())


def parse_native_bytes(kind: str, content: bytes) -> dict[str, Any]:
    """Translate positively identified native parse failures into contract errors."""
    try:
        return _parse_native_bytes(kind, content)
    except (ParseError, DefusedXmlException, PyPdfError, zipfile.BadZipFile, KeyError, OSError) as error:
        raise ValueError(f"native {kind} parser rejected invalid bytes: {error}") from error


def _parse_native_bytes(kind: str, content: bytes) -> dict[str, Any]:
    """Observe all native pages/members; no existence or producer boolean is enough."""
    if not content:
        raise ValueError("native artifact is empty")
    if kind == "pdf":
        from pypdf import PdfReader

        if not content.startswith(b"%PDF-"):
            raise ValueError("native PDF signature is invalid")
        document = PdfReader(BytesIO(content), strict=True)
        if document.is_encrypted or not document.pages:
            raise ValueError("native PDF is encrypted or has no pages")
        boxes = []
        for page in document.pages:
            box = [float(value) for value in page.mediabox]
            if not all(math.isfinite(value) for value in box) or box[2] <= box[0] or box[3] <= box[1]:
                raise ValueError("native PDF page geometry is invalid")
            boxes.append(box)
        return {"pages": len(boxes), "page_boxes_pt": boxes}
    if kind == "html":
        document_html = _HTMLDocument()
        document_html.feed(content.decode("utf-8"))
        document_html.close()
        if not document_html.html or not document_html.body_seen or not document_html.body_text:
            raise ValueError("native HTML has no standalone document/body content")
        return {"body_text_sha256": hashlib.sha256("\n".join(document_html.body_text).encode()).hexdigest()}
    if kind == "png":
        from PIL import Image

        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            if image.format != "PNG" or min(image.size) <= 0:
                raise ValueError("native PNG has invalid format/dimensions")
            image.load()
            return {"width_px": image.width, "height_px": image.height, "mode": image.mode}
    if kind not in {"docx", "epub", "pptx"}:
        raise ValueError("native artifact format is unsupported")
    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = bounded_members(archive)
        if kind == "epub":
            from infrastructure.rendering._epub_package_validation import validate_epub_package

            validate_epub_package(archive)
            return {"members": len(names), "xhtml_documents": len([name for name in names if name.endswith(".xhtml")])}
        if "[Content_Types].xml" not in names:
            raise ValueError("native Office artifact lacks content types")
        types = fromstring(archive.read("[Content_Types].xml"))
        if types.tag != "{http://schemas.openxmlformats.org/package/2006/content-types}Types":
            raise ValueError("native Office content types are invalid")
        if kind == "docx":
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            document = fromstring(archive.read("word/document.xml"))
            body = document.find(namespace + "body")
            if document.tag != namespace + "document" or body is None or not list(body):
                raise ValueError("native DOCX has no document/body content")
            return {"members": len(names), "body_elements": len(list(body))}
        namespace = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
        presentation = fromstring(archive.read("ppt/presentation.xml"))
        slides = presentation.find(namespace + "sldIdLst")
        size = presentation.find(namespace + "sldSz")
        if presentation.tag != namespace + "presentation" or slides is None or not list(slides) or size is None:
            raise ValueError("native PPTX has no presentation/slides/geometry")
        width, height = int(size.attrib["cx"]), int(size.attrib["cy"])
        if width <= 0 or height <= 0:
            raise ValueError("native PPTX has invalid slide geometry")
        actual = sorted(name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
        if len(actual) != len(list(slides)):
            raise ValueError("native PPTX slide inventory is incomplete")
        for name in actual:
            if fromstring(archive.read(name)).tag != namespace + "sld":
                raise ValueError("native PPTX slide XML is invalid")
        return {"members": len(names), "slides": len(actual), "width_emu": width, "height_emu": height}


def native_tool_record(
    root: Path,
    directory: Path,
    name: str,
    arguments: list[str],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    purpose: str,
) -> dict[str, Any]:
    """Execute and bind exact tool bytes and the original observed process outcome."""
    selected = shutil.which(name, path=env.get("PATH"))
    if not selected:
        raise NativeToolUnavailable(f"{name} is not installed in the selected native environment")
    executable = Path(selected).resolve(strict=True)
    content = read_bytes_confined(executable.parent, executable, max_bytes=512 * 1024 * 1024)
    digest = hashlib.sha256(content).hexdigest()
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("native observer deadline expired before tool launch")
    command = [str(executable), *arguments]
    result = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 120), capture_output=True)
    if (
        hashlib.sha256(read_bytes_confined(executable.parent, executable, max_bytes=512 * 1024 * 1024)).hexdigest()
        != digest
    ):
        raise ValueError("native executable changed during tool observation")
    payload = {
        "schema_version": TOOL_SCHEMA,
        "run_id": run_id,
        "tool": name,
        "purpose": purpose,
        "executable": str(executable),
        "executable_sha256": digest,
        "command": command,
        "exit_code": result.returncode,
        "original_exit_code": result.original_returncode,
        "timed_out": result.timed_out,
        "custody_refused": result.custody_refused,
        "diagnostic": result.command_error,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    binding = write_json(root, directory / f"{purpose}.json", payload)
    if result.custody_refused:
        raise NativeToolUnavailable(f"native tool guardian positively refused source custody: {result.command_error}")
    if result.timed_out or result.returncode == 124:
        raise TimeoutError("actual native tool exceeded its original finite deadline")
    return {"artifact": binding, "exit_code": result.returncode, "original_exit_code": result.original_returncode}


def audit_pdf_raster(
    root: Path,
    directory: Path,
    artifact: ArtifactSnapshot,
    observation: dict[str, Any],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    ordinal: int,
) -> dict[str, Any]:
    """Rasterize every actual page at 150 dpi and bind native font observations."""
    prefix = directory / f"raster-{ordinal:04d}"
    # External tools consume the exact already-admitted bytes, never a second
    # read of mutable renderer output. The private input remains bound evidence.
    frozen = directory / f"input-{ordinal:04d}.pdf"
    if frozen.exists():
        raise ValueError("native tool input must be fresh")
    atomic_write_bytes_confined(root, frozen, artifact.content, mode=0o600)
    reader = SnapshotReader(root)
    consumed = reader.read(frozen.relative_to(root).as_posix())
    if consumed.sha256 != artifact.sha256:
        raise ValueError("native tool input differs from admitted artifact bytes")
    tools = []
    for name, args, purpose in (
        ("pdftoppm", ["-r", "150", "-png", str(frozen), str(prefix)], f"raster-{ordinal:04d}"),
        ("pdffonts", [str(frozen)], f"fonts-{ordinal:04d}"),
    ):
        record = native_tool_record(
            root, directory, name, args, env=env, deadline=deadline, run_id=run_id, purpose=purpose
        )
        tools.append(record["artifact"])
        if record["exit_code"] != 0 or record["original_exit_code"] != 0:
            raise ValueError(f"real native {name} failed; existing artifact bytes cannot grant acceptance")
    from PIL import Image, ImageStat

    numbered = []
    for path in directory.glob(prefix.name + "-*.png"):
        match = re.fullmatch(re.escape(prefix.name) + r"-([0-9]+)\.png", path.name)
        if match is None:
            raise ValueError("native raster page identity is malformed")
        numbered.append((int(match[1]), path))
    numbered.sort()
    if [number for number, _ in numbered] != list(range(1, observation["pages"] + 1)):
        raise ValueError("native raster page identities are incomplete")
    paths = [path for _, path in numbered]
    if len(paths) != observation["pages"]:
        raise ValueError("native raster page collection is incomplete")
    rasters = []
    for path in paths:
        snapshot = reader.read(path.relative_to(root).as_posix())
        with Image.open(BytesIO(snapshot.content)) as image:
            image.load()
            variance = sum(ImageStat.Stat(image.convert("RGB")).var)
            if not math.isfinite(variance) or variance <= 0:
                raise ValueError("native PDF raster is blank/uniform")
            rasters.append(
                {
                    "path": snapshot.relative,
                    "sha256": snapshot.sha256,
                    "width_px": image.width,
                    "height_px": image.height,
                    "variance": variance,
                }
            )
    if not reader.unchanged():
        raise ValueError("native raster bytes changed during inspection")
    return {
        "dpi": 150,
        "input_artifact": {"path": consumed.relative, "sha256": consumed.sha256},
        "rasters": rasters,
        "tool_artifacts": tools,
    }
