"""Source-owned native Office equation and bookend layout projection."""

from __future__ import annotations

import os
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import SubElement, tostring

from defusedxml.ElementTree import fromstring

MAX_PACKAGE_BYTES = 250 * 1024 * 1024
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def office_semantics_filter_path() -> Path:
    """Resolve the installed filter; a missing package resource is an error."""
    path = Path(__file__).with_name("office_semantics.lua")
    if not path.is_file():
        raise RuntimeError("installed native Office semantic projection filter is missing")
    return path


def project_docx_transmission_layout(package: Path) -> None:
    """Retain declared compact, zero-spacing, same-page transmission bookends.

    Pandoc creates the named custom style while writing source-owned Divs. Its
    style is completed here rather than depending on an unconfigured external
    reference document. No source prose, equation, image or label is rewritten.
    """
    if package.is_symlink() or package.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError("native Office package violates bounded regular-file admission")
    original = package.read_bytes()
    with zipfile.ZipFile(BytesIO(original)) as source:
        rows = source.infolist()
        if len(rows) > 20_000 or sum(row.file_size for row in rows) > MAX_PACKAGE_BYTES:
            raise ValueError("native Office package exceeds finite archive budget")
        styles = fromstring(source.read("word/styles.xml"))
        style = next(
            (node for node in styles.findall(W + "style") if node.get(W + "styleId") == "TemplateTransmission"), None
        )
        if style is None:
            return
        properties = style.find(W + "pPr")
        if properties is None:
            properties = SubElement(style, W + "pPr")
        for name, attributes in (
            ("keepNext", {}),
            ("keepLines", {}),
            ("spacing", {W + "before": "0", W + "after": "0"}),
        ):
            node = properties.find(W + name)
            if node is None:
                node = SubElement(properties, W + name)
            node.attrib.update(attributes)
        runs = style.find(W + "rPr")
        if runs is None:
            runs = SubElement(style, W + "rPr")
        for name in ("sz", "szCs"):
            size = runs.find(W + name)
            if size is None:
                size = SubElement(runs, W + name)
            size.set(W + "val", "14")
        destination = BytesIO()
        with zipfile.ZipFile(destination, "w") as output:
            for row in rows:
                output.writestr(
                    row,
                    tostring(styles, encoding="utf-8", xml_declaration=True)
                    if row.filename == "word/styles.xml"
                    else source.read(row),
                )
    descriptor, temporary = tempfile.mkstemp(prefix=".office-projection-", suffix=".docx", dir=package.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(destination.getvalue())
        os.chmod(temporary, package.stat().st_mode & 0o777)
        os.replace(temporary, package)
    finally:
        Path(temporary).unlink(missing_ok=True)


def office_pandoc_metadata(settings: dict[str, Any]) -> dict[str, Any]:
    """Preserve declared book frontmatter in the native Office editions."""
    from infrastructure.rendering._pdf_title_page_config import build_pandoc_metadata

    metadata = build_pandoc_metadata(settings)
    book = settings.get("book")
    if isinstance(book, dict):
        for key in ("title", "subtitle"):
            if not metadata.get(key) and book.get(key):
                metadata[key] = str(book[key])
        if not metadata.get("author") and book.get("author"):
            metadata["author"] = [str(book["author"])]
    return metadata
