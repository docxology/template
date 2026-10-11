"""Real indexed PDFs prove refusal before unsafe native stream/page parsing."""

from __future__ import annotations

import re
import time
import zlib
from io import BytesIO

import pytest
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, EncodedStreamObject, NameObject, NumberObject

from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


def encoded_pdf(program: bytes, *, attributes: dict | None = None, repeats: int = 1, cycle: bool = False) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=240, height=120)
    stream = EncodedStreamObject()
    stream[NameObject("/Filter")] = NameObject("/FlateDecode")
    stream._data = zlib.compress(program)
    if attributes:
        stream.update(attributes)
    reference = writer._add_object(stream)
    page[NameObject("/Contents")] = reference if repeats == 1 else ArrayObject([reference] * repeats)
    if cycle:
        pages = writer._root_object["/Pages"]
        pages[NameObject("/Kids")] = ArrayObject([writer._root_object.raw_get("/Pages")])
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


def test_genuine_classic_native_pdf_passes_without_changing_bytes() -> None:
    from infrastructure.reporting.native_format_pdf_oracles import pdf_control_bytes
    import hashlib

    content = pdf_control_bytes("baseline")
    before = hashlib.sha256(content).hexdigest()
    preflight_pdf_streams(content, deadline=time.monotonic() + 5)
    assert hashlib.sha256(content).hexdigest() == before


def test_compressed_page_content_bomb_refused_before_native_parser() -> None:
    content = encoded_pdf(b" " * (32 * 1024 * 1024 + 1))
    assert len(content) < 50_000
    with pytest.raises(ValueError, match="expansion exceeds finite decode budget"):
        preflight_pdf_streams(content, deadline=time.monotonic() + 5)


def test_length1_cannot_hide_executable_content_from_preflight() -> None:
    content = encoded_pdf(
        b"begincmap 1 beginbfrange <0000> <ffff> <0000> endbfrange endcmap",
        attributes={NameObject("/Length1"): NumberObject(1)},
    )
    with pytest.raises(ValueError, match="CMap range expansion"):
        preflight_pdf_streams(content, deadline=time.monotonic() + 5, max_objects=10000)


def test_repeated_original_content_programs_count_before_page_parsing() -> None:
    content = encoded_pdf(b"(ABCD) Tj\n" * 100, repeats=20)
    with pytest.raises(ValueError, match="repeated page program budget"):
        preflight_pdf_streams(content, deadline=time.monotonic() + 5, max_objects=3000)


def test_cyclic_pages_refuse_before_native_page_traversal() -> None:
    content = encoded_pdf(b"q Q", cycle=True)
    with pytest.raises(ValueError, match="page tree is cyclic"):
        preflight_pdf_streams(content, deadline=time.monotonic() + 5)


@pytest.mark.parametrize("subtype", ["/Form", "/Type3", "/PS"])
def test_unsupported_executable_programs_refuse(subtype: str) -> None:
    content = encoded_pdf(b"q Q", attributes={NameObject("/Subtype"): NameObject(subtype)})
    with pytest.raises(ValueError, match="require bounded support"):
        preflight_pdf_streams(content, deadline=time.monotonic() + 5)


def test_compressed_or_foreign_xref_pointer_cannot_use_scan_fallback() -> None:
    content = encoded_pdf(b"q Q")
    marker = re.search(rb"startxref\s+(\d+)\s+%%EOF", content)
    assert marker
    content = content[: marker.start(1)] + b"9" + content[marker.end(1) :]
    with pytest.raises(ValueError, match="compressed xref/object streams"):
        preflight_pdf_streams(content, deadline=time.monotonic() + 5)


def test_cid_width_range_cannot_expand_billions_of_entries() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=240, height=120)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/CIDFontType2"),
            NameObject("/W"): ArrayObject([NumberObject(0), NumberObject(2**31), NumberObject(500)]),
        }
    )
    writer._add_object(font)
    target = BytesIO()
    writer.write(target)
    with pytest.raises(ValueError, match="CID width range exceeds"):
        preflight_pdf_streams(target.getvalue(), deadline=time.monotonic() + 5)


def test_expired_original_preparse_budget_refuses() -> None:
    content = encoded_pdf(b"q Q")
    with pytest.raises(TimeoutError, match="deadline exhausted"):
        preflight_pdf_streams(content, deadline=time.monotonic() - 1)
