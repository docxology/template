"""Bounded indexed-PDF admission before unbounded native stream parsing."""

from __future__ import annotations

import time
from io import BytesIO


def preflight_pdf_streams(
    content: bytes, *, deadline: float, max_bytes: int = 64 * 1024 * 1024, max_objects: int = 2_000_000
) -> None:
    """Bound expansion and repeated page programs without changing input bytes.

    Complete classic and compressed indexes and bounded object/CMap streams
    are admitted. Incremental updates, encryption, Forms, Type3 fonts, patterns
    and inherited CMaps remain unsupported. Every rejection precedes PDFminer page parsing.
    """
    from pdfminer.pdfparser import PDFParser
    from infrastructure.reporting.native_pdf_index_bounds import admit_pdf_index
    from infrastructure.reporting.native_pdf_cmap_bounds import cmap_range_cost
    from pdfminer.pdftypes import PDFObjRef, resolve1
    from pdfminer.psparser import PSBaseParser, PSKeyword, PSLiteral, PSEOF

    if not content or len(content) > max_bytes or not 0 < max_objects <= 4_000_000:
        raise ValueError("native PDF preparse exceeds its finite input budget")
    admission = admit_pdf_index(content, deadline=deadline, max_bytes=max_bytes, max_objects=max_objects)
    values, trailer, streams = admission.values, admission.trailer, admission.streams
    pending = list(values.values())
    font_files = set()
    cmap_files = set()
    cmap_uses: dict[int, int] = {}
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
            if "Font" in value:
                fonts = resolve1(value["Font"])
                if not isinstance(fonts, dict) or any(not isinstance(spec, PDFObjRef) for spec in fonts.values()):
                    raise ValueError("native PDF direct font resource programs require bounded support")
            if "UseCMap" in value:
                raise ValueError("native PDF inherited CMaps require bounded support")
            if "ToUnicode" in value:
                target = value["ToUnicode"]
                if not isinstance(target, PDFObjRef):
                    raise ValueError("native PDF ToUnicode requires an exact indexed stream")
                cmap_files.add(target.objid)
                cmap_uses[target.objid] = cmap_uses.get(target.objid, 0) + 1
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
    estimates: dict[int, tuple[int, int]] = {}
    for object_id, attrs, tail in streams:
        kind = resolve1(attrs.get("Type"))
        if isinstance(kind, PSLiteral) and kind.name in {"ObjStm", "XRef"}:
            if object_id not in admission.decoded:
                raise ValueError("native PDF index/object stream lacks exact bounded admission")
            continue
        decoded = admission.stream_data(attrs, tail)
        if object_id in font_files or any(
            isinstance(resolve1(attrs.get(key)), PSLiteral) and resolve1(attrs[key]).name in {"Image", "Metadata"}
            for key in ("Type", "Subtype")
        ):
            continue
        tokens = PSBaseParser(BytesIO(decoded))
        count = text_bytes = 0
        is_cmap = object_id in cmap_files or b"begincmap" in decoded
        cmap_tokens = []
        while True:
            try:
                _, token = tokens.nexttoken()
            except PSEOF:
                break
            admission.tick()
            count += 1
            text_bytes += len(token) if isinstance(token, bytes) else 0
            if text_bytes > max_objects:
                raise ValueError("native PDF content token/glyph budget exhausted before page parsing")
            if time.monotonic() >= deadline:
                raise TimeoutError("native PDF preparse deadline exhausted")
            if (
                is_cmap
                or isinstance(token, PSKeyword)
                and token.name in {b"beginbfrange", b"begincidrange", b"usecmap"}
            ):
                cmap_tokens.append(token)
            if is_cmap and isinstance(token, bytes) and len(token) > 32:
                raise ValueError("native PDF CMap string expansion requires bounded support")
        mappings, expanded_text = cmap_range_cost(cmap_tokens, max_objects)
        copies = max(1, cmap_uses.get(object_id, 0))
        admission.tokens += mappings * copies + count * (copies - 1)
        if admission.tokens > max_objects or (text_bytes + expanded_text) * copies > max_objects:
            raise ValueError("native PDF CMap range expansion exceeds the original program budget")
        estimates[object_id] = count + mappings, text_bytes + expanded_text
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
    from pdfminer.pdfdocument import PDFDocument, PDFXRef, PDFXRefStream

    document = PDFDocument(PDFParser(BytesIO(content)), fallback=False)
    if len(document.xrefs) != 1 or type(document.xrefs[0]) is not (PDFXRefStream if admission.compressed else PDFXRef):
        raise ValueError("native PDF native xref differs from bounded source admission")
    xref = document.xrefs[0]
    if set(xref.get_objids()) != set(admission.offsets) or any(
        xref.get_pos(object_id) != position for object_id, position in admission.offsets.items()
    ):
        raise ValueError("native PDF native xref differs from bounded source admission")
