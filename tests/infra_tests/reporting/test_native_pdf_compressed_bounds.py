"""Actual compressed-index PDFs exercise bounded admission and native text."""

from __future__ import annotations

import hashlib
import time
import zlib
from io import BytesIO

import pytest
from pdfminer.high_level import extract_text

from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


def compressed_pdf(fault: str = "healthy") -> bytes:
    values = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 240 120] /Contents 6 0 R /Resources << /Font << /F1 4 0 R >> >> >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    positions = []
    body = b""
    for value in values:
        positions.append(len(body))
        body += value + b"\n"
    header = b" ".join(str(item).encode() for pair in enumerate(positions, 1) for item in pair) + b"\n"
    data = header + body
    if fault == "object-bomb":
        data = b" " * (32 * 1024 * 1024 + 1)
    if fault == "duplicate-member":
        header = header.replace(b"2 35", b"1 35") if b"2 35" in header else header.replace(b"2 ", b"1 ", 1)
        data = header + body
    object_data = zlib.compress(data)
    count = 2**31 if fault == "member-count" else 4
    first = len(header) + 1 if fault == "first" else len(header)
    content = b"%PDF-1.7\n"
    offsets = {5: len(content)}
    content += (
        f"5 0 obj\n<< /Type /ObjStm /N {count} /First {first} /Filter /FlateDecode /Length {len(object_data)} >>\nstream\n".encode()
        + object_data
        + b"\nendstream\nendobj\n"
    )
    offsets[6] = len(content)
    program = b"BT /F1 12 Tf 50 80 Td (Native compressed PDF) Tj ET"
    content += f"6 0 obj\n<< /Length {len(program)} >>\nstream\n".encode() + program + b"\nendstream\nendobj\n"
    offsets[7] = len(content)
    entries = [(0, 0, 65535)] + [(2, 5, index) for index in range(4)] + [(1, offsets[item], 0) for item in (5, 6, 7)]
    if fault == "member-index":
        entries[1] = (2, 5, 8)
    elif fault == "missing-stream":
        entries[1] = (2, 6, 0)
    elif fault == "overlap":
        entries[6] = entries[5]
    elif fault == "entry-kind":
        entries[1] = (3, 5, 0)
    raw = b"".join(
        kind.to_bytes(1, "big") + position.to_bytes(4, "big") + detail.to_bytes(2, "big")
        for kind, position, detail in entries
    )
    if fault == "xref-bomb":
        raw = b"x" * 100000
    index_data = zlib.compress(raw)
    size = 2**31 if fault == "index-size" else 8
    widths = b"[1 255 2]" if fault == "width" else b"[1 4 2]"
    index = b" /Index [0 4 3 5]" if fault == "range-overlap" else b""
    if fault == "incremental":
        index += b" /Prev 9"
    content += (
        f"7 0 obj\n<< /Type /XRef /Size {size} /Root 1 0 R /Length {len(index_data)} /Filter /FlateDecode /W ".encode()
        + widths
        + index
        + b" >>\nstream\n"
        + index_data
        + b"\nendstream\nendobj\n"
    )
    return content + f"startxref\n{offsets[7]}\n%%EOF\n".encode()


def test_original_compressed_index_and_objects_reach_native_text_unchanged() -> None:
    content = compressed_pdf()
    original = hashlib.sha256(content).hexdigest()
    preflight_pdf_streams(content, deadline=time.monotonic() + 5)
    assert "Native compressed PDF" in extract_text(BytesIO(content))
    assert hashlib.sha256(content).hexdigest() == original


@pytest.mark.parametrize(
    "fault",
    [
        "object-bomb",
        "xref-bomb",
        "member-count",
        "first",
        "duplicate-member",
        "member-index",
        "missing-stream",
        "overlap",
        "entry-kind",
        "index-size",
        "width",
        "range-overlap",
        "incremental",
    ],
)
def test_compressed_source_cannot_hide_unbounded_or_changed_indexes(fault: str) -> None:
    with pytest.raises(ValueError):
        preflight_pdf_streams(compressed_pdf(fault), deadline=time.monotonic() + 5)


@pytest.mark.parametrize(
    "program",
    [
        b"begincmap 1 beginbfrange <0000> <0002> <0061> endbfrange endcmap",
        b"begincmap 1 beginbfrange <0000> <0002> [<0061> <0062> <0063>] endbfrange endcmap",
        b"begincmap 1 begincidrange <0000> <0002> 0 endcidrange endcmap",
    ],
)
def test_finite_cmap_range_rows_are_admitted_without_expansion(program: bytes) -> None:
    from tests.infra_tests.reporting.test_native_pdf_stream_bounds import encoded_pdf

    preflight_pdf_streams(encoded_pdf(program), deadline=time.monotonic() + 5)


@pytest.mark.parametrize(
    "program",
    [
        b"begincmap 1 beginbfrange <00000000> <ffffffff> <0061> endbfrange endcmap",
        b"begincmap 1 beginbfrange <0000> <0002> <ffffffff> endbfrange endcmap",
        b"begincmap 1 beginbfrange <0000> <0002> [<0061>] endbfrange endcmap",
        b"begincmap 1 beginbfrange <0000> <0000> <0061> <0001> <0001> <0062> endbfrange endcmap",
        b"begincmap /Unadmitted usecmap endcmap",
        b"begincmap <00000000> <ffffffff> <0061> endbfrange endcmap",
        b"begincmap <00000000> <ffffffff> 0 endcidrange endcmap",
    ],
)
def test_cmap_range_expansion_and_parser_recovery_cannot_hide_cost(program: bytes) -> None:
    from tests.infra_tests.reporting.test_native_pdf_stream_bounds import encoded_pdf

    with pytest.raises(ValueError, match="CMap"):
        preflight_pdf_streams(encoded_pdf(program), deadline=time.monotonic() + 5)


def test_reused_cmap_is_charged_for_every_original_font_construction() -> None:
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, EncodedStreamObject, NameObject

    writer = PdfWriter()
    writer.add_blank_page(width=240, height=120)
    stream = EncodedStreamObject()
    stream[NameObject("/Filter")] = NameObject("/FlateDecode")
    stream._data = zlib.compress(b"begincmap 1 beginbfrange <0000> <03e7> <0061> endbfrange endcmap")
    reference = writer._add_object(stream)
    for _ in range(4):
        writer._add_object(
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                    NameObject("/ToUnicode"): reference,
                }
            )
        )
    output = BytesIO()
    writer.write(output)
    with pytest.raises(ValueError, match="CMap range expansion"):
        preflight_pdf_streams(output.getvalue(), deadline=time.monotonic() + 5, max_objects=3000)


def test_direct_font_resource_cannot_hide_uncached_repeated_map_construction() -> None:
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=240, height=120)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {
                    NameObject("/F1"): DictionaryObject(
                        {
                            NameObject("/Type"): NameObject("/Font"),
                            NameObject("/Subtype"): NameObject("/Type1"),
                            NameObject("/BaseFont"): NameObject("/Helvetica"),
                        }
                    )
                }
            )
        }
    )
    output = BytesIO()
    writer.write(output)
    with pytest.raises(ValueError, match="direct font resource"):
        preflight_pdf_streams(output.getvalue(), deadline=time.monotonic() + 5)
