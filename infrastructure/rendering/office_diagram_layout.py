"""Complete the already declared original-diagram DOCX 4.2-inch height cap.

Only exact original PNG bindings are eligible. Mathematical/prose source and
all unrelated images are retained. Actual native visibility/font/placement
observation remains mandatory; writing matching extent bytes cannot prove it.
"""

from __future__ import annotations

import hashlib
import os
import posixpath
import re
import tempfile
import zipfile
from collections import Counter
from io import BytesIO
from typing import Any
from pathlib import Path
from xml.parsers import expat

from defusedxml.ElementTree import fromstring

from infrastructure.core.files.archive_members import bounded_members

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PIC = "{http://schemas.openxmlformats.org/drawingml/2006/picture}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MAX_HEIGHT_EMU = 3_840_480  # exact declared 4.2in; 914400 EMU/in
MAX_BYTES = 250 * 1024 * 1024


def _extent_bytes(original: bytes, width: int, height: int) -> bytes:
    for name, value in ((b"cx", width), (b"cy", height)):
        pattern = rb"(\b" + name + rb"\s*=\s*)([\"'])([0-9]+)\2"
        original, count = re.subn(
            pattern, lambda match: match[1] + match[2] + str(value).encode("ascii") + match[2], original
        )
        if count != 1:
            raise ValueError("source-bound DOCX extent has ambiguous literal integer attributes")
    return original


def _start_tag_end(data: bytes, start: int) -> int:
    quote = 0
    for index in range(start, min(len(data), start + 1024 * 1024)):
        char = data[index]
        if quote:
            if char == quote:
                quote = 0
        elif char in (34, 39):
            quote = char
        elif char == 62:
            return index + 1
    raise ValueError("source-bound DOCX extent has an unbounded literal XML start tag")


def project_docx_diagram_layout(data: bytes, diagram_png_sha256: tuple[str, ...]) -> tuple[bytes, dict[str, Any]]:
    """Cap actual source-linked DrawingML extents and preserve aspect to one EMU."""
    if len(data) > MAX_BYTES or len(diagram_png_sha256) > 100:
        raise ValueError("original diagram DOCX projection exceeds its finite package/source bound")
    if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value) for value in diagram_png_sha256):
        raise ValueError("original diagram DOCX projection requires exact original PNG SHA256 bindings")
    expected = Counter(diagram_png_sha256)
    if not expected:
        return data, {
            "schema_version": "template-office-original-diagram-height-projection-v1",
            "maximum_height_emu": MAX_HEIGHT_EMU,
            "occurrences": [],
        }
    with zipfile.ZipFile(BytesIO(data)) as source:
        names = bounded_members(source)
        if sum(row.file_size for row in source.infolist()) > MAX_BYTES:
            raise ValueError("original diagram DOCX decoded archive exceeds the existing package bound")
        original_xml = source.read("word/document.xml")
        original_xml.decode("utf-8")  # current source writer's actual encoding
        document = fromstring(original_xml)
        starts = []
        parser = expat.ParserCreate(namespace_separator="}")
        parser.StartElementHandler = lambda name, attributes: starts.append(
            ("{" + name if "}" in name else name, parser.CurrentByteIndex)
        )
        parser.Parse(original_xml, True)
        elements = list(document.iter())
        if len(elements) > 1_000_000:
            raise ValueError("source-bound DOCX diagram XML exceeds its finite element bound")
        if len(elements) != len(starts) or any(
            element.tag != row[0] for element, row in zip(elements, starts, strict=True)
        ):
            raise ValueError("source-bound DOCX XML byte positions differ from independent safe parsing")
        positions = {id(element): row[1] for element, row in zip(elements, starts, strict=True)}
        replacements = {}
        relationships = fromstring(source.read("word/_rels/document.xml.rels"))
        targets = {}
        for relationship in relationships.findall(REL + "Relationship"):
            if relationship.get("TargetMode") == "External":
                continue
            target = relationship.get("Target", "")
            if not target or "\\" in target or target.startswith("/"):
                raise ValueError("native DOCX diagram relationship escapes its package")
            target = posixpath.normpath(posixpath.join("word", target))
            if target not in names or not target.startswith("word/"):
                raise ValueError("native DOCX diagram relationship lacks a confined actual member")
            targets[relationship.get("Id")] = target
        actual: Counter[str] = Counter()
        occurrences: list[dict[str, Any]] = []
        changed = False
        digests = {}
        for drawing in document.iter(W + "drawing"):
            containers = list(drawing.findall(WP + "inline")) + list(drawing.findall(WP + "anchor"))
            for container in containers:
                pictures = list(container.iter(PIC + "pic"))
                for picture in pictures:
                    blips = list(picture.iter(A + "blip"))
                    if len(blips) != 1:
                        raise ValueError("native DOCX picture has unsupported ambiguous image resources")
                    target = targets.get(blips[0].get(R + "embed"))
                    if target is None:
                        continue
                    if target not in digests:
                        digests[target] = hashlib.sha256(source.read(target)).hexdigest()
                    digest = digests[target]
                    if digest not in expected:
                        continue
                    actual[digest] += 1
                    extent = container.find(WP + "extent")
                    transform = picture.find(PIC + "spPr/" + A + "xfrm")
                    inner_extent = None if transform is None else transform.find(A + "ext")
                    if (
                        extent is None
                        or transform is None
                        or inner_extent is None
                        or any(transform.get(key, "0") not in {"0", "false"} for key in ("rot", "flipH", "flipV"))
                    ):
                        raise ValueError("original DOCX diagram has unimplemented rotation/extent geometry")
                    if any(
                        any(value not in {"0", "0.0"} for value in crop.attrib.values())
                        for crop in picture.iter(A + "srcRect")
                    ):
                        raise ValueError("original DOCX diagram contains an unsupported cropped source picture")
                    width, height = int(extent.attrib["cx"]), int(extent.attrib["cy"])
                    if min(width, height) <= 0 or (int(inner_extent.attrib["cx"]), int(inner_extent.attrib["cy"])) != (
                        width,
                        height,
                    ):
                        raise ValueError("original DOCX diagram has collapsed or inconsistent source extents")
                    projected_width = width if height <= MAX_HEIGHT_EMU else width * MAX_HEIGHT_EMU // height
                    projected_height = min(height, MAX_HEIGHT_EMU)
                    if projected_width <= 0:
                        raise ValueError("original DOCX diagram aspect projection collapsed its width")
                    occurrences.append(
                        {
                            "ordinal": len(occurrences),
                            "png_sha256": digest,
                            "member": target,
                            "original_extent_emu": [width, height],
                            "projected_extent_emu": [projected_width, projected_height],
                        }
                    )
                    if projected_height != height:
                        changed = True
                        for node in (extent, inner_extent):
                            start = positions[id(node)]
                            end = _start_tag_end(original_xml, start)
                            if start in replacements:
                                raise ValueError("source-bound DOCX diagram shares an ambiguous extent instruction")
                            replacements[start] = (
                                end,
                                _extent_bytes(original_xml[start:end], projected_width, projected_height),
                            )
        if actual != expected:
            raise ValueError(
                "DOCX diagram height projection dropped or duplicated an exact original source PNG occurrence"
            )
        if tuple(row["png_sha256"] for row in occurrences) != diagram_png_sha256:
            raise ValueError("DOCX diagram height projection changed original source diagram occurrence order")
        if not changed:
            result = data
        else:
            projected_xml = original_xml
            for start, (end, replacement) in sorted(replacements.items(), reverse=True):
                projected_xml = projected_xml[:start] + replacement + projected_xml[end:]
            # Preserve original prefix declarations, mc:Ignorable, all prose,
            # formula/caption XML and every unrelated byte in the document.
            fromstring(projected_xml)
            output = BytesIO()
            with zipfile.ZipFile(output, "w") as destination:
                for row in source.infolist():
                    destination.writestr(
                        row, projected_xml if row.filename == "word/document.xml" else source.read(row)
                    )
            result = output.getvalue()
    if len(result) > MAX_BYTES:
        raise ValueError("projected DOCX diagram package exceeds its original byte bound")
    return result, {
        "schema_version": "template-office-original-diagram-height-projection-v1",
        "maximum_height_emu": MAX_HEIGHT_EMU,
        "occurrences": occurrences,
    }


def apply_docx_diagram_layout(package: Path, diagram_png_sha256: tuple[str, ...]) -> None:
    """Atomically finish a genuine writer package at its existing output path."""
    if not diagram_png_sha256:
        return
    if package.is_symlink() or package.stat().st_size > MAX_BYTES:
        raise ValueError("source-bound DOCX diagram layout requires a bounded regular package")
    original = package.read_bytes()
    projected, _ = project_docx_diagram_layout(original, diagram_png_sha256)
    if projected == original:
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".office-diagram-layout-", suffix=".docx", dir=package.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(projected)
        os.chmod(temporary, package.stat().st_mode & 0o777)
        os.replace(temporary, package)
    finally:
        Path(temporary).unlink(missing_ok=True)
