"""Configured newspaper print checks against source and actual native rasters.

This module does not trust edition layout reports. A private current-source
render supplies exact glyph/font/image geometry; source text presence is checked
independently. Receipt callers must separately admit runtime/font/tool custody.
"""

from __future__ import annotations

import hashlib
import html
import importlib
import json
import math
import re
import subprocess
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import pdfplumber
from pypdf import PdfReader

from infrastructure.reporting.native_storybook_source import (
    LIMIT,
    pixels,
    read_source_yaml,
    source_identity,
    source_package,
)


@dataclass(frozen=True)
class NewspaperReference:
    source_sha256: str
    dimensions: tuple[float, float]
    pdf: bytes
    obligations: tuple[tuple[str, ...], ...]


def _plain(text: str) -> str:
    # Only the source-supported ReportLab inline forms are admitted.
    for tag in re.findall(r"<[^>]+>", text):
        if not re.fullmatch(r"</?(?:b|i|u|super|sub)>|<br\s*/?>", tag):
            raise ValueError("unsupported newspaper inline source form")
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def _compact(text: str) -> str:
    return "".join(character.casefold() for character in text if character.isalnum())


def _texts(value: Any) -> list[str]:
    result = []
    if hasattr(value, "__dataclass_fields__"):
        for key in value.__dataclass_fields__:
            field = getattr(value, key)
            if (
                key
                in {
                    "headline",
                    "kicker",
                    "deck",
                    "byline",
                    "dateline",
                    "text",
                    "attribution",
                    "jump",
                    "caption",
                    "credit",
                    "title",
                    "footnote",
                    "sponsor",
                    "tagline",
                    "contact",
                    "department",
                }
                and isinstance(field, str)
                and field
            ):
                result.append(_plain(field))
            elif key in {"body", "items", "rows", "columns", "lead", "rail_items", "main_items", "figure"}:
                result.extend(_texts(field))
    elif isinstance(value, (list, tuple)):
        for item in value:
            result.extend(_texts(item))
    elif isinstance(value, str):
        result.append(_plain(value))
    return result


def _strict_forms(value: Any) -> None:
    """Reject source fields which the current typed parser could silently drop."""
    forms = {
        "number": {"number", "section", "department", "template", "columns", "rail_enabled", "lead", "rail", "main"},
        "headline": {"headline", "kicker", "deck", "byline", "dateline", "level", "body", "jump", "figure", "drop_cap"},
        "box": {"box", "title", "items", "rows", "columns", "body", "footnote"},
        "ad": {"ad"},
        "sponsor": {
            "sponsor",
            "tagline",
            "body",
            "contact",
            "graphic",
            "background",
            "accent",
            "border",
            "height",
            "graphic_height",
        },
        "path": {"path", "caption", "credit", "height"},
        "figure": {"figure"},
        "p": {"p"},
        "subhead": {"subhead"},
        "pull": {"pull"},
        "quote": {"quote", "by"},
    }
    if isinstance(value, dict):
        discriminator = next((key for key in forms if key in value), None)
        if discriminator is None or set(value) - forms[discriminator]:
            raise ValueError("unsupported newspaper source fields")
        for child in value.values():
            _strict_forms(child)
    elif isinstance(value, list):
        for child in value:
            _strict_forms(child)
    elif value is not None and not isinstance(value, (str, bool, int, float)):
        raise ValueError("unsupported newspaper source scalar")


def build_newspaper_reference(project: Path, directory: Path, *, deadline: float) -> NewspaperReference:
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("newspaper source reconstruction deadline")
    before = source_identity(project)
    manifest = read_source_yaml(project / "content/edition.yaml")
    if not isinstance(manifest, dict) or set(manifest) != {"masthead", "render", "pages"}:
        raise ValueError("unsupported newspaper manifest")
    if set(manifest["masthead"]) - {
        "nameplate",
        "motto",
        "established",
        "city",
        "state",
        "date",
        "volume",
        "number",
        "price",
        "edition_label",
        "weather_strip",
    }:
        raise ValueError("unsupported newspaper masthead fields")
    for leaf in manifest["pages"]:
        path = project / "content/pages" / leaf
        if path.is_symlink() or not path.resolve().is_relative_to((project / "content").resolve()):
            raise ValueError("newspaper page source escapes content")
        _strict_forms(read_source_yaml(path))
    engine = source_package(project, "newspaper")
    package = engine.__package__
    figures = importlib.import_module(package + ".figures")
    edition = engine.load_edition(project / "content")
    config = engine.load_newspaper_config(project / "content")
    if not 1 <= len(edition.pages) <= 32:
        raise ValueError("unsupported newspaper page count")
    directory.mkdir(parents=True, exist_ok=True)
    resource_names = set()
    for page_source in manifest["pages"]:
        raw_page = read_source_yaml(project / "content/pages" / page_source)

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"path", "graphic"} and child:
                        if (
                            not isinstance(child, str)
                            or not child.startswith("output/figures/")
                            or Path(child).name not in (figures._SCENES | figures._COLOR_GRAPHICS | figures._CHARTS)
                        ):
                            raise ValueError("unsupported newspaper image resource")
                        resource_names.add(child)
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(raw_page)
    if resource_names:
        figures.generate_all(directory / "output/figures")
    if time.monotonic() >= deadline:
        raise TimeoutError("newspaper source reconstruction deadline")
    path = directory / "source-edition.pdf"
    engine.render_edition(edition, config, project_root=directory, output_path=path)
    # Intentionally ignore the producer all_pages_fit/audit report.
    if source_identity(project) != before:
        raise ValueError("newspaper source changed during reconstruction")
    dimensions = (config.geometry().width, config.geometry().height)
    return NewspaperReference(
        before,
        dimensions,
        path.read_bytes(),
        tuple(
            tuple(text for text in _texts(page) if page.template != "front" or text != page.department)
            for page in edition.pages
        ),
    )


def _font_material(value: Any, depth: int = 0) -> Any:
    if depth > 12:
        raise ValueError("newspaper font resource exceeds structural bound")
    if hasattr(value, "get_object"):
        value = value.get_object()
    if hasattr(value, "get_data"):
        data = value.get_data()
        if len(data) > LIMIT:
            raise ValueError("newspaper font program exceeds bound")
        return (
            "stream",
            hashlib.sha256(data).hexdigest(),
            _font_material(
                {key: child for key, child in value.items() if key not in {"/Length", "/Filter", "/DecodeParms"}},
                depth + 1,
            ),
        )
    if isinstance(value, dict):
        return tuple((str(key), _font_material(child, depth + 1)) for key, child in sorted(value.items()))
    if isinstance(value, list):
        return tuple(_font_material(child, depth + 1) for child in value)
    return value


def _fonts(data: bytes) -> tuple[Any, ...]:
    document = PdfReader(BytesIO(data), strict=True)
    # Resource aliases may change during a PDF rewrite; the full font program,
    # encoding, metrics and descriptor remain exact after dereferencing.
    return tuple(
        tuple(sorted({repr(_font_material(font)) for font in cast(Any, page["/Resources"])["/Font"].values()}))
        for page in document.pages
    )


def _glyphs(data: bytes, reference: NewspaperReference) -> tuple[tuple[Any, ...], ...]:
    document = PdfReader(BytesIO(data), strict=True)
    if document.is_encrypted or len(document.pages) != len(reference.obligations):
        raise ValueError("newspaper page count/encryption")
    for pdf_page in document.pages:
        if (
            tuple(float(x) for x in pdf_page.mediabox) != (0, 0, *reference.dimensions)
            or tuple(pdf_page.cropbox) != tuple(pdf_page.mediabox)
            or pdf_page.rotation
            or pdf_page.get("/Annots")
        ):
            raise ValueError("newspaper configured page geometry")
    rows = []
    with pdfplumber.open(BytesIO(data)) as parsed:
        for index, page in enumerate(parsed.pages):
            visible = _compact("".join(char["text"] for char in page.chars))
            for phrase in reference.obligations[index]:
                if _compact(phrase) not in visible:
                    raise ValueError(f"newspaper source text missing on page {index + 1}: {phrase[:70]}")
            chars = []
            for char in page.chars:
                bounds = tuple(float(char[key]) for key in ("x0", "top", "x1", "bottom"))
                if (
                    not all(math.isfinite(x) for x in bounds)
                    or bounds[0] < 0
                    or bounds[1] < 0
                    or bounds[2] > page.width
                    or bounds[3] > page.height
                    or float(char["size"]) < 5
                ):
                    raise ValueError("newspaper clipped or unsupported tiny glyph")
                chars.append(
                    (char["text"], char["fontname"], float(char["size"]), bounds, char.get("non_stroking_color"))
                )
            rows.append(tuple(chars))
    return tuple(rows)


def inspect_newspaper_artifact(
    data: bytes, reference: NewspaperReference, directory: Path, *, pdftoppm: str, deadline: float
) -> dict[str, object]:
    if len(data) > LIMIT or len(reference.pdf) > LIMIT:
        raise ValueError("newspaper artifact exceeds bound")
    if _fonts(data) != _fonts(reference.pdf):
        raise ValueError("newspaper font encoding/program differs from source")
    expected = _glyphs(reference.pdf, reference)
    if _glyphs(data, reference) != expected:
        raise ValueError("newspaper glyph order/font/geometry differs from source")
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / "candidate.pdf", directory / "source.pdf"]
    for path, payload in zip(paths, (data, reference.pdf), strict=True):
        path.write_bytes(payload)
    processes = []
    for page in range(1, len(reference.obligations) + 1):
        images = []
        for label, path in zip(("candidate", "source"), paths, strict=True):
            if time.monotonic() >= deadline:
                raise TimeoutError("newspaper independent raster deadline")
            prefix = directory / f"{label}-page"
            command = [
                pdftoppm,
                "-f",
                str(page),
                "-l",
                str(page),
                "-r",
                "72",
                "-singlefile",
                "-png",
                str(path),
                str(prefix),
            ]
            process = subprocess.run(
                command, capture_output=True, timeout=max(0.01, deadline - time.monotonic()), check=False
            )
            processes.append(
                {
                    "command": command,
                    "original_exit_code": process.returncode,
                    "stdout": process.stdout.decode(errors="replace"),
                    "stderr": process.stderr.decode(errors="replace"),
                }
            )
            (directory / "raster-processes.json").write_text(json.dumps(processes, indent=2), encoding="utf-8")
            if process.returncode != 0:
                raise ValueError("newspaper native raster execution failed")
            images.append(pixels(prefix.with_suffix(".png").read_bytes()))
        if images[0] != images[1]:
            raise ValueError("newspaper rendered pixels differ from source (image/hidden/clipped content)")
    return {
        "schema_version": "template-newspaper-native-v1",
        "source_sha256": reference.source_sha256,
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "pages": len(reference.obligations),
        "raster_processes": processes,
    }
