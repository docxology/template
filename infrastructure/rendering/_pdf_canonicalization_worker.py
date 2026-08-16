"""Isolated worker for deterministic PDF metadata canonicalization.

Tagged-PDF structure trees can exceed Python's default recursion budget while
pypdf clones and walks their object graph. The elevated budget therefore lives
only in this disposable process; worker failure cannot mutate the renderer's
process-global recursion policy or partially replace the source PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<([0-9A-Fa-f]{32})>\s*<([0-9A-Fa-f]{32})>\s*\]")
_FONT_SUBSET_RE = re.compile(r"^/[A-Z]{6}\+(?P<font>.+)$")
_FONT_SUBSET_BYTES_RE = re.compile(rb"[A-Z]{6}\+")
_RECURSION_LIMIT = 100_000


def _canonicalize_pdf_objects(objects: Sequence[object]) -> None:
    """Remove TeX's random six-letter font-subset prefixes in-place."""
    from pypdf.generic import ArrayObject, DictionaryObject, NameObject, StreamObject

    def visit(value: object) -> None:
        if isinstance(value, StreamObject):
            # Never decode/re-encode raster image streams during metadata
            # canonicalization. pypdf's get_data() path can rewrite
            # XeTeX/dvipdfmx image filters and silently corrupt wide PNGs.
            if str(value.get("/Subtype", "")) == "/Image":
                return
            stream_data = value.get_data()
            canonical_data = _FONT_SUBSET_BYTES_RE.sub(b"AAAAAA+", stream_data)
            if canonical_data != stream_data:
                value.set_data(canonical_data)
            return
        if isinstance(value, DictionaryObject):
            for key, child in list(value.items()):
                if str(key) in {"/BaseFont", "/FontName"} and isinstance(child, NameObject):
                    match = _FONT_SUBSET_RE.match(str(child))
                    if match:
                        value[key] = NameObject(f"/AAAAAA+{match.group('font')}")
                else:
                    visit(child)
        elif isinstance(value, ArrayObject):
            for child in value:
                visit(child)

    for obj in objects:
        visit(obj)


def _normalize_pdf_identifier(pdf_bytes: bytes) -> bytes:
    """Replace a compiler-generated PDF ID with a content-derived stable ID."""
    from infrastructure.core.exceptions import CompilationError

    match = _PDF_ID_RE.search(pdf_bytes)
    if match is None:
        raise CompilationError("Deterministic PDF canonicalization found no PDF file identifier")

    placeholder = b"/ID [ <" + (b"0" * 32) + b"> <" + (b"0" * 32) + b"> ]"
    without_id = pdf_bytes[: match.start()] + placeholder + pdf_bytes[match.end() :]
    stable_id = hashlib.sha256(without_id).hexdigest()[:32].encode("ascii")
    replacement = b"/ID [ <" + stable_id + b"> <" + stable_id + b"> ]"
    return pdf_bytes[: match.start()] + replacement + pdf_bytes[match.end() :]


def canonicalize_pdf_to_path(source: Path, destination: Path, *, epoch: int) -> None:
    """Write a deterministic clone of ``source`` to ``destination``."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, ByteStringObject

    reader = PdfReader(str(source))
    writer = PdfWriter(clone_from=str(source), keep_initial_header=True)

    # PDF identifiers are optional. Install a deterministic placeholder before
    # writing so every valid compiler output can receive a content-based ID.
    # pypdf currently exposes no public trailer-ID setter.
    placeholder = b"\x00" * 16
    writer._ID = ArrayObject([ByteStringObject(placeholder), ByteStringObject(placeholder)])
    _canonicalize_pdf_objects(writer._objects)  # pypdf has no public tree mutator

    metadata = {
        key: str(value)
        for key, value in (reader.metadata or {}).items()
        if key in {"/Producer", "/Keywords", "/Subject", "/Title"} and value is not None
    }
    metadata["/Creator"] = "XeTeX deterministic output"
    metadata["/CreationDate"] = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
    writer.add_metadata(metadata)

    with destination.open("wb") as handle:
        writer.write(handle)
    destination.write_bytes(_normalize_pdf_identifier(destination.read_bytes()))


def main(argv: Sequence[str] | None = None) -> int:
    """Run one isolated canonicalization request."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("epoch", type=int)
    arguments = parser.parse_args(argv)

    try:
        sys.setrecursionlimit(_RECURSION_LIMIT)
        canonicalize_pdf_to_path(arguments.source, arguments.destination, epoch=arguments.epoch)
    except Exception as exc:  # noqa: BLE001 - subprocess boundary reports all worker failures
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the parent subprocess
    raise SystemExit(main())
