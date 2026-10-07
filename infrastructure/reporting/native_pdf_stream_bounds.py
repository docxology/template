"""Conservative classic-PDF admission before unbounded native stream parsing."""

from __future__ import annotations

import re
import time
from io import BytesIO
from typing import Any, cast

from infrastructure.reporting.native_pdf_stream_decode import _bounded_stream_data


def preflight_pdf_streams(
    content: bytes, *, deadline: float, max_bytes: int = 64 * 1024 * 1024, max_objects: int = 2_000_000
) -> None:
    """Bound expansion and repeated page programs without changing input bytes.

    Only a complete classic xref is supported. Compressed objects/xrefs,
    incremental updates, encryption, Forms, Type3 fonts, patterns and CMap
    ranges remain unsupported. Every rejection precedes PDFminer page parsing.
    """
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdftypes import PDFObjRef, PDFStream, resolve1
    from pdfminer.psparser import PSBaseParser, PSKeyword, PSLiteral, PSEOF

    if not content or len(content) > max_bytes or not 0 < max_objects <= 4_000_000:
        raise ValueError("native PDF preparse exceeds its finite input budget")
    final = re.search(rb"startxref\s+(\d+)\s+%%EOF\s*$", content)
    if final is None:
        raise ValueError("native PDF preparse requires a complete classic xref")
    offset = int(final[1])
    if content[offset : offset + 4] != b"xref":
        raise ValueError("native PDF compressed xref/object streams require bounded support")
    cursor = offset + 4
    offsets: dict[int, tuple[int, int]] = {}
    entries = 0
    section_pattern = re.compile(rb"(\d+) (\d+)[ \t]*\r?\n")
    entry_pattern = re.compile(rb"(\d{10}) (\d{5}) ([nf])[ \t]*\r?\n")
    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError("native PDF preparse deadline exhausted")
        while cursor < len(content) and content[cursor] in b" \t\r\n":
            cursor += 1
        if content[cursor : cursor + 7] == b"trailer":
            cursor += 7
            break
        section = section_pattern.match(content, cursor)
        if section is None:
            raise ValueError("native PDF classic xref subsection is malformed")
        first, count = map(int, section.groups())
        entries += count
        if count < 1 or entries > min(max_objects, 100_000):
            raise ValueError("native PDF preparse xref object budget exhausted")
        cursor = section.end()
        for object_id in range(first, first + count):
            entry = entry_pattern.match(content, cursor)
            if entry is None:
                raise ValueError("native PDF classic xref entry is malformed")
            cursor = entry.end()
            if entry[3] == b"n":
                if object_id in offsets:
                    raise ValueError("native PDF repeated xref objects are unsupported")
                offsets[object_id] = (int(entry[1]), int(entry[2]))
    token_count = 0
    values: dict[int, Any] = {}

    class PrefixParser(PDFParser):
        def flush(self) -> None:
            if self.curstack:
                self.add_results(*self.pop(len(self.curstack)))

        def nexttoken(self) -> Any:
            nonlocal token_count
            token_count += 1
            if token_count > max_objects or len(self.context) > 64:
                raise ValueError("native PDF preparse token/depth budget exhausted")
            if time.monotonic() >= deadline:
                raise TimeoutError("native PDF preparse deadline exhausted")
            return super().nexttoken()

    class References:
        def getobj(self, object_id: int) -> Any:
            seen: set[int] = set()
            while True:
                if object_id in seen or len(seen) >= 64 or object_id not in values:
                    raise ValueError("native PDF reference is cyclic, deep or unadmitted")
                if time.monotonic() >= deadline:
                    raise TimeoutError("native PDF reference deadline exhausted")
                seen.add(object_id)
                value = values[object_id]
                if not isinstance(value, PDFObjRef):
                    return value
                object_id = value.objid

    references = References()
    trailer_parser = PrefixParser(BytesIO(content[cursor:]))
    trailer_parser.doc = cast(Any, references)
    trailer = trailer_parser.nextobject()[1]
    if not isinstance(trailer, dict) or any(key in trailer for key in ("Prev", "XRefStm", "Encrypt")):
        raise ValueError("native PDF incremental/encrypted/hybrid xrefs require bounded support")
    ordered = sorted((position, object_id, generation) for object_id, (position, generation) in offsets.items())
    streams = []
    for index, (position, object_id, generation) in enumerate(ordered):
        end = ordered[index + 1][0] if index + 1 < len(ordered) else offset
        if not 0 <= position < end <= offset:
            raise ValueError("native PDF classic object offsets overlap or escape source")
        body = content[position:end]
        header = re.match(rf"{object_id}\s+{generation}\s+obj\b".encode(), body)
        if header is None:
            raise ValueError("native PDF object identity differs from its classic xref")
        body = body[header.end() :]
        parser = PrefixParser(BytesIO(body))
        parser.doc = cast(Any, references)
        value = parser.nextobject()[1]
        values[object_id] = value
        next_position, next_token = parser.nexttoken()
        if isinstance(next_token, PSKeyword) and next_token.name == b"stream":
            if not isinstance(value, dict):
                raise ValueError("native PDF stream has no admitted dictionary")
            streams.append((object_id, value, body[next_position:]))
        elif not isinstance(next_token, PSKeyword) or next_token.name != b"endobj":
            raise ValueError("native PDF indirect object body is unsupported")
    pending = list(values.values())
    font_files = set()
    cmap_files = set()
    visits = 0
    while pending:
        value = pending.pop()
        visits += 1
        if visits > max_objects:
            raise ValueError("native PDF preparse dictionary budget exhausted")
        if isinstance(value, dict):
            subtype = resolve1(value.get("Subtype"))
            if isinstance(subtype, PSLiteral) and subtype.name in {"Type3", "Form", "PS"} or "PatternType" in value:
                raise ValueError("native PDF executable glyph/Form/pattern programs require bounded support")
            if "UseCMap" in value:
                raise ValueError("native PDF inherited CMaps require bounded support")
            if "ToUnicode" in value:
                target = value["ToUnicode"]
                if not isinstance(target, PDFObjRef):
                    raise ValueError("native PDF ToUnicode requires an exact indexed stream")
                cmap_files.add(target.objid)
            for key in ("FirstChar", "LastChar"):
                if key in value and (type(value[key]) is not int or not 0 <= value[key] <= 65535):
                    raise ValueError("native PDF font character range exceeds its finite budget")
            for key in ("W", "W2"):
                if key not in value:
                    continue
                widths = resolve1(value[key])
                if not isinstance(widths, list):
                    raise ValueError("native PDF CID widths require an explicit bounded array")
                index = 0
                while index < len(widths):
                    first = widths[index]
                    if type(first) is not int or not 0 <= first <= 65535 or index + 1 >= len(widths):
                        raise ValueError("native PDF CID width interval is malformed")
                    following = widths[index + 1]
                    if isinstance(following, list):
                        if len(following) > 65536 - first:
                            raise ValueError("native PDF CID width array exceeds its finite budget")
                        index += 2
                    else:
                        stride = 3 if key == "W" else 5
                        if (
                            type(following) is not int
                            or not first <= following <= 65535
                            or index + stride > len(widths)
                        ):
                            raise ValueError("native PDF CID width range exceeds its finite budget")
                        index += stride
            for key in ("FontFile", "FontFile2", "FontFile3"):
                target = value.get(key)
                if target is not None:
                    role = resolve1(value.get("Type"))
                    if not isinstance(role, PSLiteral) or role.name != "FontDescriptor":
                        raise ValueError("native PDF font bytes lack their exact descriptor role")
                    if not isinstance(target, PDFObjRef):
                        raise ValueError("native PDF font bytes require an exact indexed stream")
                    font_files.add(target.objid)
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    if font_files & cmap_files:
        raise ValueError("native PDF font and CMap stream roles overlap")
    total = 0
    estimates: dict[int, tuple[int, int]] = {}
    for object_id, attrs, tail in streams:
        if any(
            isinstance(resolve1(attrs.get(key)), PSLiteral) and resolve1(attrs[key]).name in {"ObjStm", "XRef", "Form"}
            for key in ("Type", "Subtype")
        ):
            raise ValueError("native PDF compressed objects/recursive Forms require bounded support")
        length = resolve1(attrs.get("Length"))
        marker = re.match(rb"stream[ \t]*(?:\r\n|\r|\n)", tail)
        if type(length) is not int or length < 0 or marker is None:
            raise ValueError("native PDF stream has no exact bounded length")
        end = marker.end() + length
        if end > len(tail) or re.fullmatch(rb"\s*endstream\s+endobj\s*", tail[end:]) is None:
            raise ValueError("native PDF stream length differs from its classic object boundary")
        decoded = _bounded_stream_data(
            PDFStream(attrs, tail[marker.end() : end]), min(32 * 1024 * 1024, max_bytes - total)
        )
        total += len(decoded)
        if object_id in font_files or any(
            isinstance(resolve1(attrs.get(key)), PSLiteral) and resolve1(attrs[key]).name in {"Image", "Metadata"}
            for key in ("Type", "Subtype")
        ):
            continue
        tokens = PSBaseParser(BytesIO(decoded))
        count = text_bytes = 0
        is_cmap = object_id in cmap_files or b"begincmap" in decoded
        while True:
            try:
                _, token = tokens.nexttoken()
            except PSEOF:
                break
            token_count += 1
            count += 1
            text_bytes += len(token) if isinstance(token, bytes) else 0
            if token_count > max_objects or text_bytes > max_objects:
                raise ValueError("native PDF content token/glyph budget exhausted before page parsing")
            if time.monotonic() >= deadline:
                raise TimeoutError("native PDF preparse deadline exhausted")
            if isinstance(token, PSKeyword) and token.name in {b"beginbfrange", b"begincidrange", b"usecmap"}:
                raise ValueError("native PDF CMap range expansion requires bounded support")
            if is_cmap and isinstance(token, bytes) and len(token) > 32:
                raise ValueError("native PDF CMap string expansion requires bounded support")
        estimates[object_id] = count, text_bytes
    root = resolve1(trailer.get("Root"))
    if not isinstance(root, dict):
        raise ValueError("native PDF has no admitted catalog")
    pending = [root.get("Pages")]
    seen_pages = set()
    page_count = program_tokens = program_text = 0
    while pending:
        if time.monotonic() >= deadline:
            raise TimeoutError("native PDF page tree deadline exhausted")
        node = resolve1(pending.pop())
        if not isinstance(node, dict) or id(node) in seen_pages:
            raise ValueError("native PDF page tree is cyclic or repeated")
        seen_pages.add(id(node))
        kind = resolve1(node.get("Type"))
        if not isinstance(kind, PSLiteral):
            raise ValueError("native PDF page tree has no declared type")
        if kind.name == "Pages":
            children = resolve1(node.get("Kids"))
            if not isinstance(children, list) or len(children) > 500 or len(seen_pages) > 1000:
                raise ValueError("native PDF page tree exceeds its finite budget")
            pending.extend(children)
        elif kind.name == "Page":
            page_count += 1
            programs = node.get("Contents", [])
            programs = programs if isinstance(programs, list) else [programs]
            for program in programs:
                if not isinstance(program, PDFObjRef) or program.objid not in estimates:
                    raise ValueError("native PDF page program is not an admitted indexed content stream")
                count, length = estimates[program.objid]
                program_tokens += count
                program_text += length
                if program_tokens > max_objects or program_text > max_objects or page_count > 500:
                    raise ValueError("native PDF repeated page program budget exhausted before page parsing")
        else:
            raise ValueError("native PDF page tree has an unsupported node")
    if not page_count:
        raise ValueError("native PDF has no bounded original pages")
    if not cmap_files.issubset(estimates):
        raise ValueError("native PDF CMap does not have an admitted text stream role")
    from pdfminer.pdfdocument import PDFDocument, PDFXRef

    document = PDFDocument(PDFParser(BytesIO(content)), fallback=False)
    if (
        len(document.xrefs) != 1
        or not isinstance(document.xrefs[0], PDFXRef)
        or document.xrefs[0].offsets
        != {key: (None, position, generation) for key, (position, generation) in offsets.items()}
    ):
        raise ValueError("native PDF native xref differs from bounded source admission")
