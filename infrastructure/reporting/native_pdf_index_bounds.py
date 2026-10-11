"""Admit exact classic or compressed PDF indexes before native decoding."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, cast

from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import PDFObjRef, PDFStream, resolve1
from pdfminer.psparser import PSEOF, PSKeyword, PSLiteral

from infrastructure.reporting.native_pdf_stream_decode import _bounded_stream_data


@dataclass
class IndexAdmission:
    deadline: float
    max_bytes: int
    max_objects: int
    values: dict[int, Any] = field(default_factory=dict)
    offsets: dict[int, tuple[int | None, int, int]] = field(default_factory=dict)
    streams: list[tuple[int, dict[str, Any], bytes]] = field(default_factory=list)
    decoded: dict[int, bytes] = field(default_factory=dict)
    trailer: dict[str, Any] = field(default_factory=dict)
    compressed: bool = False
    tokens: int = 0
    expanded_bytes: int = 0

    def tick(self, depth: int = 0) -> None:
        self.tokens += 1
        if self.tokens > self.max_objects or depth > 64:
            raise ValueError("native PDF preparse token/depth budget exhausted")
        if time.monotonic() >= self.deadline:
            raise TimeoutError("native PDF preparse deadline exhausted")

    def getobj(self, object_id: int) -> Any:
        seen: set[int] = set()
        while True:
            self.tick()
            if object_id in seen or len(seen) >= 64 or object_id not in self.values:
                raise ValueError("native PDF reference is cyclic, deep or unadmitted")
            seen.add(object_id)
            value = self.values[object_id]
            if not isinstance(value, PDFObjRef):
                return value
            object_id = value.objid

    def parser(self, content: bytes) -> PDFParser:
        admission = self

        class PrefixParser(PDFParser):
            def flush(self) -> None:
                if self.curstack:
                    self.add_results(*self.pop(len(self.curstack)))

            def nexttoken(self) -> Any:
                admission.tick(len(self.context))
                return super().nexttoken()

        parser = PrefixParser(BytesIO(content))
        parser.doc = cast(Any, self)
        return parser

    def stream_data(
        self, attrs: dict[str, Any], tail: bytes, *, direct: bool = False, limit: int = 32 * 1024 * 1024
    ) -> bytes:
        length = attrs.get("Length") if direct else resolve1(attrs.get("Length"))
        marker = re.match(rb"stream[ \t]*(?:\r\n|\r|\n)", tail)
        if type(length) is not int or length < 0 or marker is None:
            raise ValueError("native PDF stream has no exact bounded length")
        end = marker.end() + length
        if end > len(tail) or re.fullmatch(rb"\s*endstream\s+endobj\s*", tail[end:]) is None:
            raise ValueError("native PDF stream length differs from its indexed object boundary")
        stream = PDFStream(attrs, tail[marker.end() : end])
        if direct and any(
            name.name not in {"FlateDecode", "Fl", "ASCII85Decode", "A85", "ASCIIHexDecode", "AHx"}
            for name, _ in stream.get_filters()
        ):
            raise ValueError("native PDF index/object stream filter requires bounded support")
        decoded = _bounded_stream_data(stream, min(limit, self.max_bytes - self.expanded_bytes))
        self.expanded_bytes += len(decoded)
        return decoded

    def indirect(self, body: bytes, object_id: int, generation: int) -> tuple[Any, bytes | None]:
        header = re.match(rf"{object_id}\s+{generation}\s+obj\b".encode(), body)
        if header is None:
            raise ValueError("native PDF object identity differs from its indexed offset")
        body = body[header.end() :]
        parser = self.parser(body)
        value = parser.nextobject()[1]
        position, token = parser.nexttoken()
        if isinstance(token, PSKeyword) and token.name == b"stream" and isinstance(value, dict):
            return value, body[position:]
        if not isinstance(token, PSKeyword) or token.name != b"endobj" or body[position + 6 :].strip():
            raise ValueError("native PDF indirect object body is unsupported")
        return value, None


def _classic(admission: IndexAdmission, content: bytes, offset: int) -> int:
    cursor = offset + 4
    entries = 0
    seen = set()
    section_pattern = re.compile(rb"(\d+) (\d+)[ \t]*\r?\n")
    entry_pattern = re.compile(rb"(\d{10}) (\d{5}) ([nf])[ \t]*\r?\n")
    while True:
        admission.tick()
        while cursor < len(content) and content[cursor] in b" \t\r\n":
            cursor += 1
        if content[cursor : cursor + 7] == b"trailer":
            value = admission.parser(content[cursor + 7 :]).nextobject()[1]
            if not isinstance(value, dict):
                raise ValueError("native PDF classic trailer requires an exact dictionary")
            admission.trailer = value
            return offset
        section = section_pattern.match(content, cursor)
        if section is None:
            raise ValueError("native PDF classic xref subsection is malformed")
        first, count = map(int, section.groups())
        entries += count
        if first < 0 or count < 1 or entries > min(admission.max_objects, 100_000):
            raise ValueError("native PDF preparse xref object budget exhausted")
        cursor = section.end()
        for object_id in range(first, first + count):
            admission.tick()
            entry = entry_pattern.match(content, cursor)
            if entry is None or object_id in seen:
                raise ValueError("native PDF classic xref entry is malformed or repeated")
            seen.add(object_id)
            cursor = entry.end()
            if entry[3] == b"n":
                admission.offsets[object_id] = (None, int(entry[1]), int(entry[2]))


def _compressed(admission: IndexAdmission, content: bytes, offset: int, end: int) -> int:
    header = re.match(rb"(\d+)\s+(\d+)\s+obj\b", content[offset:end])
    if header is None:
        raise ValueError("native PDF compressed xref/object streams have no exact indexed identity")
    object_id, generation = map(int, header.groups())
    attrs, tail = admission.indirect(content[offset:end], object_id, generation)
    if (
        not isinstance(attrs, dict)
        or not isinstance(attrs.get("Type"), PSLiteral)
        or attrs["Type"].name != "XRef"
        or tail is None
    ):
        raise ValueError("native PDF compressed xref has no original XRef stream")
    if any(key in attrs for key in ("Prev", "XRefStm", "Encrypt")):
        raise ValueError("native PDF incremental/encrypted/hybrid xrefs require bounded support")
    size, widths = attrs.get("Size"), attrs.get("W")
    if type(size) is not int or not 1 <= size <= min(admission.max_objects, 100_000):
        raise ValueError("native PDF compressed xref size exceeds its finite budget")
    if (
        not isinstance(widths, list)
        or len(widths) != 3
        or any(type(item) is not int or not 0 <= item <= 8 for item in widths)
        or not sum(widths)
    ):
        raise ValueError("native PDF compressed xref field widths are malformed or unbounded")
    ranges = attrs.get("Index", [0, size])
    if not isinstance(ranges, list) or not ranges or len(ranges) % 2 or len(ranges) > 2 * size:
        raise ValueError("native PDF compressed xref ranges are malformed or unbounded")
    identifiers: list[int] = []
    for index in range(0, len(ranges), 2):
        first, count = ranges[index : index + 2]
        if type(first) is not int or type(count) is not int or not 0 <= first < size or not 0 < count <= size - first:
            raise ValueError("native PDF compressed xref range exceeds its exact Size")
        if identifiers and first <= identifiers[-1]:
            raise ValueError("native PDF compressed xref ranges overlap or are unordered")
        identifiers.extend(range(first, first + count))
    data = admission.stream_data(attrs, tail, direct=True, limit=len(identifiers) * sum(widths))
    if len(data) != len(identifiers) * sum(widths):
        raise ValueError("native PDF compressed xref bytes differ from its complete bounded index")
    cursor = 0
    for identifier in identifiers:
        admission.tick()
        fields = []
        for width, default in zip(widths, (1, 0, 0), strict=True):
            fields.append(int.from_bytes(data[cursor : cursor + width], "big") if width else default)
            cursor += width
        kind, location, detail = fields
        if kind == 1:
            if not 0 < identifier < size or detail > 65535 or not 0 <= location <= offset:
                raise ValueError("native PDF compressed xref physical position is unadmitted")
            admission.offsets[identifier] = (None, location, detail)
        elif kind == 2:
            if not 0 < identifier < size or not 0 < location < size or detail >= min(admission.max_objects, 100_000):
                raise ValueError("native PDF compressed object index exceeds its finite budget")
            admission.offsets[identifier] = (location, detail, 0)
        elif kind != 0:
            raise ValueError("native PDF compressed xref has an unsupported entry type")
    if admission.offsets.get(object_id) != (None, offset, generation):
        raise ValueError("native PDF compressed xref does not index its exact original self")
    admission.trailer = attrs
    admission.decoded[object_id] = data
    admission.compressed = True
    return end


def _objects(admission: IndexAdmission) -> None:
    for object_id, attrs, tail in admission.streams:
        kind = attrs.get("Type")
        if not isinstance(kind, PSLiteral) or kind.name != "ObjStm":
            continue
        count, first = attrs.get("N"), attrs.get("First")
        if (
            type(count) is not int
            or not 0 < count <= min(admission.max_objects, 100_000)
            or type(first) is not int
            or first < 0
        ):
            raise ValueError("native PDF object stream member/header budget exhausted")
        data = admission.stream_data(attrs, tail, direct=True)
        if (
            first > min(len(data), admission.max_objects)
            or re.fullmatch(rb"(?:\s*\d+\s+\d+\s*)+", data[:first]) is None
        ):
            raise ValueError("native PDF object stream has no exact bounded header")
        numbers = [int(item) for item in data[:first].split()]
        if len(numbers) != 2 * count:
            raise ValueError("native PDF object stream count differs from complete original members")
        seen = set()
        for index in range(count):
            admission.tick()
            member, position = numbers[2 * index : 2 * index + 2]
            end = numbers[2 * index + 3] if index + 1 < count else len(data) - first
            if (
                (index == 0 and position != 0)
                or member in seen
                or admission.offsets.get(member) != (object_id, index, 0)
                or not 0 <= position < end <= len(data) - first
            ):
                raise ValueError("native PDF compressed member identity/order/boundary disagrees with xref")
            seen.add(member)
            parser = admission.parser(data[first + position : first + end])
            value = parser.nextobject()[1]
            try:
                parser.nexttoken()
            except PSEOF:
                pass
            else:
                raise ValueError("native PDF compressed member contains extra original objects")
            admission.values[member] = value
        admission.decoded[object_id] = data
    if set(admission.values) != set(admission.offsets):
        raise ValueError("native PDF compressed xref has missing or unadmitted object stream members")


def admit_pdf_index(content: bytes, *, deadline: float, max_bytes: int, max_objects: int) -> IndexAdmission:
    admission = IndexAdmission(deadline, max_bytes, max_objects)
    final = re.search(rb"startxref\s+(\d+)\s+%%EOF\s*$", content)
    if final is None:
        raise ValueError("native PDF preparse requires a complete original xref")
    offset = int(final[1])
    if not 0 <= offset < final.start():
        raise ValueError("native PDF compressed xref/object streams require an exact source position")
    end = (
        _classic(admission, content, offset)
        if content[offset : offset + 4] == b"xref"
        else _compressed(admission, content, offset, final.start())
    )
    if not isinstance(admission.trailer, dict) or any(
        key in admission.trailer for key in ("Prev", "XRefStm", "Encrypt")
    ):
        raise ValueError("native PDF incremental/encrypted/hybrid xrefs require bounded support")
    ordered = sorted(
        (position, object_id, generation)
        for object_id, (stream_id, position, generation) in admission.offsets.items()
        if stream_id is None
    )
    for index, (position, object_id, generation) in enumerate(ordered):
        following = ordered[index + 1][0] if index + 1 < len(ordered) else end
        if not 0 <= position < following <= end:
            raise ValueError("native PDF indexed object offsets overlap or escape source")
        value, tail = admission.indirect(content[position:following], object_id, generation)
        admission.values[object_id] = value
        if tail is not None:
            admission.streams.append((object_id, value, tail))
    _objects(admission)
    return admission
