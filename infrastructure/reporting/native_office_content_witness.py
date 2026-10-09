"""Independent source-to-native-package witnesses for complete Office bodies.

This reader compares source obligations directly to native readback, rather
than using writer/reference equality as a source survival oracle. Native page
and control evidence are separate mandatory obligations.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any, cast

from defusedxml.ElementTree import fromstring

from infrastructure.reporting.native_office_math_semantics import office_math_expression, office_roman_source_segments
from infrastructure.reporting.native_office_raw_roles import office_raw_source_roles
from infrastructure.reporting.native_office_source_coverage import MAX_AST_BYTES, scientific_source_occurrences

MAX_PACKAGE_BYTES = 250 * 1024 * 1024
MAX_PIXELS = 60_000_000
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _document(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_AST_BYTES:
        raise ValueError("Office source/native AST exceeds finite byte budget")
    document = json.loads(data)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("blocks"), list)
        or not document.get("pandoc-api-version")
    ):
        raise ValueError("Office source/native witness requires a genuine complete document AST")
    return document


def _text(value: Any) -> str:
    if isinstance(value, dict):
        kind = value.get("t")
        if kind == "Str":
            return "" if value["c"] == "\u200b" else cast(str, value["c"])
        if kind in {"Space", "SoftBreak", "LineBreak"}:
            return " "
        if kind == "Code":
            return cast(str, value["c"][1])
        if kind == "CodeBlock":
            return " " + cast(str, value["c"][1]) + " "
        if kind in {"RawBlock", "RawInline"} and value["c"][0] == "openxml":
            raw = value["c"][1]
            # DOCX crossref emits some source-owned captions as actual Word
            # paragraphs. Parse text from those paragraphs; raw source roles
            # remain independently classified above.
            wrapped = f'<root xmlns:w="{W[1:-1]}">{raw}</root>'
            return " " + "".join(node.text or "" for node in fromstring(wrapped).iter(W + "t")) + " "
        if kind in {"RawBlock", "RawInline", "Math"}:
            return ""
        if kind == "Cite":
            return _text(value["c"][1])
        if kind == "Quoted":
            single = value["c"][0]["t"] == "SingleQuote"
            return ("‘" if single else "“") + _text(value["c"][1]) + ("’" if single else "”")
        if kind == "Image":
            # Visible Figure captions are separate nodes. Reader Image text
            # carries the alternative description and is checked separately.
            return ""
        result = _text(value.get("c", []))
        return " " + result + " " if kind in {"Para", "Plain", "Header"} else result
    if isinstance(value, list):
        return "".join(_text(child) for child in value)
    return ""


def _compact(text: str) -> str:
    # Native package paragraph separators and nonbreaking citation spaces are
    # equivalent whitespace; no digits, punctuation or words are normalized.
    return " ".join(text.split())


def _image_alternative(value: Any) -> str:
    if isinstance(value, dict) and value.get("t") == "Math":
        return cast(str, value["c"][1])
    if isinstance(value, dict) and value.get("t") == "Cite":
        return _image_alternative(value["c"][1])
    if isinstance(value, dict) and value.get("t") in {
        "Emph",
        "Strong",
        "Span",
        "SmallCaps",
        "Subscript",
        "Superscript",
    }:
        return _image_alternative(value["c"])
    if isinstance(value, list):
        return "".join(_image_alternative(child) for child in value)
    return _text(value)


def _tables(ast: bytes) -> tuple[dict[str, Any], ...]:
    tables = []
    for occurrence in scientific_source_occurrences(ast):
        if occurrence.kind != "Table":
            continue
        value = json.loads(occurrence.content_json)
        if not isinstance(value, list) or len(value) != 6:
            raise ValueError("Office table witness requires declared six-field table schema")
        _, caption, columns, head, bodies, foot = value
        group_rows = [head[1]]
        for body in bodies:
            group_rows.extend((body[2], body[3]))
        group_rows.append(foot[1])
        rows = []
        for group in group_rows:
            for row in group:
                cells = []
                for cell in row[1]:
                    if len(cell) != 5 or any(type(span) is not int or span < 1 for span in cell[2:4]):
                        raise ValueError("Office table witness has malformed cell spans")
                    cells.append({"row_span": cell[2], "column_span": cell[3], "text": _compact(_text(cell[4]))})
                rows.append(cells)
        # Captions can be represented by the native reader as an adjacent
        # paragraph. Their text remains in the complete prose witness below.
        tables.append({"columns": len(columns), "rows": rows, "caption": _compact(_text(caption))})
    return tuple(tables)


def _image_identity(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_PACKAGE_BYTES:
        raise ValueError("Office source/native image exceeds finite byte budget")
    from PIL import Image

    try:
        with Image.open(BytesIO(data)) as image:
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("Office source/native image exceeds finite pixel budget")
            image.load()
            rgba = image.convert("RGBA")
            return {
                "kind": "decoded-raster",
                "size": list(rgba.size),
                "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
            }
    except (OSError, SyntaxError):
        # Vector transformations require another explicit witness. Exact
        # source bytes are still accounted for and can survive unchanged.
        return {"kind": "exact-nonraster", "sha256": hashlib.sha256(data).hexdigest()}


def _archive(data: bytes) -> dict[str, bytes]:
    if len(data) > MAX_PACKAGE_BYTES:
        raise ValueError("Office package exceeds finite byte budget")
    with zipfile.ZipFile(BytesIO(data)) as archive:
        rows = archive.infolist()
        names = [row.filename for row in rows]
        if (
            len(rows) > 20_000
            or len(set(names)) != len(names)
            or sum(row.file_size for row in rows) > MAX_PACKAGE_BYTES
        ):
            raise ValueError("Office package exceeds finite unique archive budget")
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
            raise ValueError("Office package has unconfined archive member")
        return {row.filename: archive.read(row) for row in rows}


def _native_image(members: dict[str, bytes], target: str, kind: str) -> bytes:
    candidates = [target, "word/" + target]
    if kind == "epub":
        candidates.extend(
            name for name in members if name.endswith("/" + target) or name.endswith("/" + PurePosixPath(target).name)
        )
    existing = list(dict.fromkeys(name for name in candidates if name in members))
    if len(existing) != 1:
        raise ValueError("Office native image has no unique package member")
    return members[existing[0]]


def inspect_office_source_survival(
    source_ast: bytes,
    filtered_ast: bytes,
    native_ast: bytes,
    package: bytes,
    kind: str,
    figures: tuple[bytes, ...],
    metadata: dict[str, Any],
    cover: bytes | None = None,
) -> dict[str, Any]:
    """Account for every mathematical, citation, table, image and raw source role.

    Reader AST content is independent input produced by an actual package
    parser. Each emitted source occurrence is bound to its original content
    digest. Unknown canonicalizations and native omissions stay explicit.
    """
    if kind not in {"docx", "epub"}:
        raise ValueError("Office survival witness requires DOCX or EPUB")
    original, filtered, native = map(_document, (source_ast, filtered_ast, native_ast))
    members = _archive(package)
    occurrences = scientific_source_occurrences(source_ast)
    native_occurrences = scientific_source_occurrences(native_ast)
    roles = office_raw_source_roles(source_ast)
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    if "\\u200b" in source_ast.decode() or "\u200b" in source_ast.decode():
        blockers.append("source contains an explicit zero-width glyph requiring an independent source-role witness")
    witnesses: list[dict[str, Any]] = []
    declarations = []
    if kind == "docx":
        word_document = fromstring(members["word/document.xml"])
        declarations = [node.get(W + "name") for node in word_document.iter(W + "bookmarkStart")]
    else:
        declarations = [
            node.get("id")
            for name, data in members.items()
            if name.endswith(".xhtml")
            for node in fromstring(data).iter()
        ]

    def native_label(label):
        return "_" + hashlib.sha1(label.encode(), usedforsecurity=False).hexdigest()[1:] if kind == "docx" else label

    labels = Counter(row["label"] for row in roles if row.get("label"))

    def source_labels(value):
        if isinstance(value, dict):
            fields = value.get("c", [])
            kind = value.get("t")
            index = 1 if kind == "Header" else 0
            if (
                kind in {"Header", "Div", "Span", "CodeBlock", "Image", "Figure", "Table"}
                and isinstance(fields, list)
                and len(fields) > index
            ):
                attribute = fields[index]
                if (
                    isinstance(attribute, list)
                    and len(attribute) == 3
                    and isinstance(attribute[0], str)
                    and attribute[0]
                ):
                    labels[attribute[0]] += 1
            for child in value.values():
                source_labels(child)
        elif isinstance(value, list):
            for child in value:
                source_labels(child)

    source_labels(original["blocks"])
    equation_labels = {}

    def labeled_equations(value, location):
        if isinstance(value, dict):
            if value.get("t") in {"Para", "Plain"}:
                inlines = value["c"]
                display = [
                    (index, inline)
                    for index, inline in enumerate(inlines)
                    if inline.get("t") == "Math" and inline["c"][0]["t"] == "DisplayMath"
                ]
                marker = next(
                    (
                        inline["c"]
                        for inline in inlines
                        if inline.get("t") == "Str" and inline["c"].startswith("{#eq:") and inline["c"].endswith("}")
                    ),
                    None,
                )
                if len(display) == 1 and marker:
                    label = marker[2:-1]
                    labels[label] += 1
                    equation_labels[(*location, "c", display[0][0])] = label
            for key, child in value.items():
                labeled_equations(child, (*location, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                labeled_equations(child, (*location, index))

    labeled_equations(original["blocks"], ("blocks",))
    image_occurrences = [row for row in occurrences if row.kind == "Image"]
    caption_math = {}
    for image in image_occurrences:
        for row in occurrences:
            if row.kind != "Math" or row.location[: len(image.location)] != image.location:
                continue
            visible = next(
                (
                    candidate
                    for candidate in occurrences
                    if candidate.kind == "Math"
                    and candidate.content_sha256 == row.content_sha256
                    and candidate.location[:2] == image.location[:2]
                    and not any(
                        candidate.location[: len(other.location)] == other.location for other in image_occurrences
                    )
                ),
                None,
            )
            if visible is None:
                blockers.append(
                    f"source image-caption Math occurrence {row.ordinal} has no identical visible Figure caption"
                )
            else:
                caption_math[row.ordinal] = (visible.ordinal, image.ordinal)
    native_math = []

    def math_expression(value):
        return office_math_expression(value, omit_roman_style=kind == "docx")

    for row in native_occurrences:
        if row.kind == "Math":
            value = json.loads(row.content_json)
            try:
                native_math.append((row.ordinal, value[0]["t"], math_expression(value[1])))
            except ValueError as error:
                blockers.append(f"native Math occurrence {row.ordinal}: {error}")
    source_math = []
    for row in occurrences:
        if row.kind == "Math":
            value = json.loads(row.content_json)
            if row.ordinal in caption_math:
                visible_ordinal, image_ordinal = caption_math[row.ordinal]
                witnesses.append(
                    {
                        "source_occurrence": row.ordinal,
                        "content_sha256": row.content_sha256,
                        "kind": "ImageCaptionMath",
                        "visible_source_occurrence": visible_ordinal,
                        "source_image_occurrence": image_ordinal,
                    }
                )
            else:
                source_math.append(
                    (row.ordinal, row.content_sha256, value[0]["t"], value[1], equation_labels.get(row.location))
                )
    for raw_role in roles:
        if raw_role["kind"] == "equation":
            source_math.append(
                (
                    raw_role["source_occurrence"],
                    raw_role["content_sha256"],
                    "DisplayMath",
                    raw_role["expression"],
                    raw_role["label"],
                )
            )
    cursor = 0
    equation_number = 0
    for ordinal, digest, mode, expression, label in sorted(source_math):
        try:
            expected = math_expression(expression)
        except ValueError as error:
            blockers.append(f"source Math occurrence {ordinal}: {error}")
            continue
        if label:
            equation_number += 1
        suffix = math_expression(f"({equation_number})") if label else ()
        match = next(
            (
                index
                for index in range(cursor, len(native_math))
                if native_math[index][1] == mode and native_math[index][2] in (expected, (*expected, *suffix))
            ),
            None,
        )
        if match is None:
            findings.append({"code": "office.source.math", "source_occurrence": ordinal, "label": label})
        else:
            witnesses.append(
                {
                    "source_occurrence": ordinal,
                    "content_sha256": digest,
                    "kind": "Math",
                    "native_occurrence": native_math[match][0],
                    "expression_sha256": hashlib.sha256(repr(expected).encode()).hexdigest(),
                    "label": label,
                }
            )
            cursor = match + 1
    if len(source_math) != len(native_math):
        findings.append(
            {"code": "office.source.math_count", "expected": len(source_math), "observed": len(native_math)}
        )
    if kind == "docx":
        namespace = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
        math_nodes = tuple(fromstring(members["word/document.xml"]).iter(namespace + "oMath"))
        if len(math_nodes) != len(source_math):
            findings.append(
                {
                    "code": "office.source.math_style",
                    "expected_math_nodes": len(source_math),
                    "observed": len(math_nodes),
                }
            )
        for (ordinal, _, _, expression, _), node in zip(sorted(source_math), math_nodes):
            try:
                segments = Counter(office_roman_source_segments(expression))
            except ValueError as error:
                blockers.append(f"source upright Math occurrence {ordinal}: {error}")
                continue
            if not segments:
                continue
            upright = []
            for run in node.iter(namespace + "r"):
                style = run.find(namespace + "rPr/" + namespace + "sty")
                text = "".join(child.text or "" for child in run.iter(namespace + "t"))
                upright.append(text if style is not None and style.get(namespace + "val") == "p" else "\x00")
            plain = "".join(upright).replace("−", "-")
            plain = "".join(char for char in plain if not char.isspace())
            if any(plain.count(segment) < count for segment, count in segments.items()):
                findings.append(
                    {
                        "code": "office.source.math_style",
                        "source_occurrence": ordinal,
                        "upright_segments": dict(segments),
                    }
                )
            else:
                witnesses.append(
                    {
                        "source_occurrence": ordinal,
                        "kind": "UprightMath",
                        "segments": dict(segments),
                        "omml_sha256": hashlib.sha256(repr(upright).encode()).hexdigest(),
                    }
                )
    expected_text = _compact(_text(filtered["blocks"]))
    native_body = native["blocks"]
    if kind == "docx":
        import copy

        native_body = copy.deepcopy(native_body)
        expected_captions = iter(_tables(filtered_ast))

        def table_descriptions(value):
            if isinstance(value, list):
                previous = None
                for child in value:
                    if isinstance(child, dict) and child.get("t") == "Table":
                        expected_caption = next(expected_captions, {}).get("caption", "")
                        if expected_caption and previous is not None and _compact(_text(previous)) == expected_caption:
                            # DOCX readback includes the displayed caption
                            # paragraph and its structural table description.
                            # Math in the description is literal TeX, while
                            # the displayed paragraph retains actual OMML.
                            child["c"][1] = [None, []]
                    table_descriptions(child)
                    if isinstance(child, dict) and child.get("t") in {"Para", "Plain"}:
                        previous = child
                    elif isinstance(child, dict):
                        previous = None
            elif isinstance(value, dict):
                for child in value.values():
                    table_descriptions(child)

        table_descriptions(native_body)
    native_text = _compact(_text(native_body))
    if expected_text and expected_text not in native_text:
        findings.append(
            {
                "code": "office.source.complete_prose",
                "source_text_sha256": hashlib.sha256(expected_text.encode()).hexdigest(),
                "native_text_sha256": hashlib.sha256(native_text.encode()).hexdigest(),
            }
        )
    filtered_cites = [row for row in scientific_source_occurrences(filtered_ast) if row.kind == "Cite"]
    remaining = Counter(_compact(_text(json.loads(row.content_json)[1])) for row in filtered_cites)
    for rendered, count in remaining.items():
        if not rendered or native_text.count(rendered) < count:
            findings.append({"code": "office.source.citation_rendering", "text": rendered, "required_count": count})
    original_ids = [
        citation["citationId"]
        for row in occurrences
        if row.kind == "Cite"
        for citation in json.loads(row.content_json)[0]
    ]
    filtered_ids = [citation["citationId"] for row in filtered_cites for citation in json.loads(row.content_json)[0]]
    source_ids, retained_ids = Counter(original_ids), Counter(filtered_ids)
    if retained_ids - source_ids:
        blockers.append("filtered source introduced citation identifiers absent from original source")
    for label, count in (source_ids - retained_ids).items():
        if labels[label] != 1 or declarations.count(native_label(label)) != 1:
            findings.append(
                {
                    "code": "office.source.crossref_label",
                    "label": label,
                    "source_declarations": labels[label],
                    "native_declarations": declarations.count(native_label(label)),
                }
            )
        else:
            witnesses.append(
                {
                    "kind": "CrossrefTarget",
                    "label": label,
                    "reference_count": count,
                    "native_target": native_label(label),
                }
            )
    for row in occurrences:
        if row.kind == "Cite":
            witnesses.append(
                {
                    "source_occurrence": row.ordinal,
                    "content_sha256": row.content_sha256,
                    "kind": "Cite",
                    "citation_ids": [citation["citationId"] for citation in json.loads(row.content_json)[0]],
                }
            )
    try:
        expected_tables, observed_tables = _tables(filtered_ast), _tables(native_ast)
        expected_grid = [{key: row[key] for key in ("columns", "rows")} for row in expected_tables]
        observed_grid = [{key: row[key] for key in ("columns", "rows")} for row in observed_tables]
        if expected_grid != observed_grid:
            findings.append(
                {"code": "office.source.table_cells", "source_tables": expected_grid, "native_tables": observed_grid}
            )
    except (ValueError, TypeError, IndexError, KeyError) as error:
        blockers.append(f"source/native table witness: {error}")
    source_images = [row for row in occurrences if row.kind == "Image"]
    filtered_images = [row for row in scientific_source_occurrences(filtered_ast) if row.kind == "Image"]
    native_images = [row for row in native_occurrences if row.kind == "Image"]
    if kind == "epub" and cover is not None:
        container = fromstring(members["META-INF/container.xml"])
        rootfiles = [node.get("full-path") for node in container.iter() if node.tag.endswith("}rootfile")]
        if len(rootfiles) != 1 or rootfiles[0] not in members:
            raise ValueError("Office configured cover has no unique actual EPUB package")
        opf = fromstring(members[rootfiles[0]])
        cover_items = [
            node.get("href")
            for node in opf.iter()
            if node.tag.endswith("}item") and "cover-image" in node.get("properties", "").split()
        ]
        covered = []
        if len(cover_items) == 1:
            cover_path = str(PurePosixPath(rootfiles[0]).parent / cover_items[0])
            covered = [
                row
                for row in native_images
                if cover_path.endswith("/" + json.loads(row.content_json)[2][0].removeprefix("./"))
            ]
        if len(covered) != 1 or _image_identity(
            _native_image(members, json.loads(covered[0].content_json)[2][0], kind)
        ) != _image_identity(cover):
            findings.append({"code": "office.source.cover_readback"})
        else:
            witnesses.append(
                {"kind": "ConfiguredCover", "native_occurrence": covered[0].ordinal, "image": _image_identity(cover)}
            )
            native_images = [row for row in native_images if row != covered[0]]
    if not len(source_images) == len(filtered_images) == len(native_images) == len(figures):
        findings.append(
            {
                "code": "office.source.image_count",
                "source": len(source_images),
                "native": len(native_images),
                "assets": len(figures),
            }
        )
    for source, expected, observed, figure in zip(source_images, filtered_images, native_images, figures):
        value = json.loads(observed.content_json)
        expected_alternative = _compact(_image_alternative(json.loads(expected.content_json)[1]))
        native_alternative = _compact(_image_alternative(value[1]))
        if expected_alternative != native_alternative:
            findings.append(
                {
                    "code": "office.source.image_alternative",
                    "source_occurrence": source.ordinal,
                    "expected": expected_alternative,
                    "observed": native_alternative,
                }
            )
        try:
            expected_identity = _image_identity(figure)
            native_identity = _image_identity(_native_image(members, value[2][0], kind))
            if expected_identity != native_identity:
                findings.append({"code": "office.source.image_content", "source_occurrence": source.ordinal})
            else:
                witnesses.append(
                    {
                        "source_occurrence": source.ordinal,
                        "content_sha256": source.content_sha256,
                        "kind": "Image",
                        "native_occurrence": observed.ordinal,
                        "image": expected_identity,
                    }
                )
        except ValueError as error:
            blockers.append(f"source Image occurrence {source.ordinal}: {error}")
    page_breaks = sum(row.get("count", row.get("page_breaks", 0)) for row in roles)
    compact_groups = sum(row["kind"] == "compact-start" for row in roles)
    if kind == "docx":
        document_xml = fromstring(members["word/document.xml"])
        actual_breaks = sum(node.get(W + "type") == "page" for node in document_xml.iter(W + "br"))
        if actual_breaks != page_breaks:
            findings.append({"code": "office.source.page_breaks", "expected": page_breaks, "observed": actual_breaks})
        if compact_groups:
            styles = fromstring(members["word/styles.xml"])
            style = next(
                (node for node in styles.iter(W + "style") if node.get(W + "styleId") == "TemplateTransmission"), None
            )
            if (
                style is None
                or style.find(f"{W}rPr/{W}sz") is None
                or style.find(f"{W}rPr/{W}sz").get(W + "val") != "14"
                or style.find(f"{W}pPr/{W}keepNext") is None
                or style.find(f"{W}pPr/{W}keepLines") is None
                or style.find(f"{W}pPr/{W}spacing") is None
                or style.find(f"{W}pPr/{W}spacing").get(W + "before") != "0"
                or style.find(f"{W}pPr/{W}spacing").get(W + "after") != "0"
                or not any(node.get(W + "val") == "TemplateTransmission" for node in document_xml.iter(W + "pStyle"))
            ):
                findings.append({"code": "office.source.compact_bookends"})
            if any(name.startswith(("word/header", "word/footer")) and name.endswith(".xml") for name in members):
                findings.append({"code": "office.source.empty_bookend_page_style"})
        alternatives = [node.get("descr", "") for node in document_xml.iter() if node.tag.endswith("}docPr")]
    else:
        xhtml = [fromstring(data) for name, data in members.items() if name.endswith(".xhtml")]
        actual_breaks = sum(
            "template-office-pagebreak" in node.get("class", "").split()
            and "page-break-after: always" in node.get("style", "")
            for tree in xhtml
            for node in tree.iter()
        )
        if actual_breaks != page_breaks:
            findings.append({"code": "office.source.page_breaks", "expected": page_breaks, "observed": actual_breaks})
        actual_compact = sum(
            "template-transmission" in node.get("class", "").split()
            and "font-size: 70%" in node.get("style", "")
            and "page-break-inside: avoid" in node.get("style", "")
            for tree in xhtml
            for node in tree.iter()
        )
        if actual_compact != compact_groups:
            findings.append(
                {"code": "office.source.compact_bookends", "expected": compact_groups, "observed": actual_compact}
            )
        alternatives = [node.get("alt", "") for tree in xhtml for node in tree.iter() if node.tag.endswith("}img")]
    for raw_role in roles:
        if raw_role["kind"] == "unsupported":
            blockers.append(
                f"Raw source occurrence {raw_role['source_occurrence']} has unsupported content/layout role"
            )
        elif raw_role["kind"] == "image-alternative" and _compact(raw_role["text"]) not in map(_compact, alternatives):
            findings.append(
                {"code": "office.source.image_alternative", "source_occurrence": raw_role["source_occurrence"]}
            )
        elif raw_role["kind"] == "heading" and raw_role["text"] not in native_text:
            findings.append({"code": "office.source.raw_heading", "source_occurrence": raw_role["source_occurrence"]})
        if raw_role["kind"] in {"heading", "equation"} and raw_role.get("label"):
            label = raw_role["label"]
            if kind == "docx":
                # Pandoc DOCX uses a 40-character NCName derived from the
                # SHA1 label digest; this is an identifier, not authentication.
                digest = hashlib.sha1(label.encode(), usedforsecurity=False).hexdigest()
                bookmark = "_" + digest[1:]
                declarations = [node.get(W + "name") for node in document_xml.iter(W + "bookmarkStart")]
            else:
                bookmark = label
                declarations = [node.get("id") for tree in xhtml for node in tree.iter()]
            if declarations.count(bookmark) != 1:
                findings.append(
                    {"code": "office.source.label", "source_occurrence": raw_role["source_occurrence"], "label": label}
                )
    for key in ("title", "author", "lang"):
        if key not in metadata:
            continue
        expected_value = metadata[key]
        if isinstance(expected_value, list):
            expected_value = "; ".join(map(str, expected_value))
        native_key = "language" if kind == "epub" and key == "lang" else key
        observed_value = _text(native.get("meta", {}).get(native_key, {}))
        if kind == "docx" and key in {"title", "author"}:
            core = fromstring(members["docProps/core.xml"])
            property_name = "title" if key == "title" else "creator"
            observed_value = next(
                (
                    node.text or ""
                    for node in core.iter()
                    if node.tag == "{http://purl.org/dc/elements/1.1/}" + property_name
                ),
                "",
            )
        if not observed_value:
            meta = native.get("meta", {}).get(native_key, {})
            observed_value = meta.get("c", "") if meta.get("t") == "MetaString" else observed_value
        if _compact(str(expected_value)) != _compact(str(observed_value)):
            findings.append(
                {
                    "code": "office.source.frontmatter",
                    "field": key,
                    "expected": expected_value,
                    "observed": observed_value,
                }
            )
    source_tables = [row for row in occurrences if row.kind == "Table"]
    witnesses.extend(
        {"source_occurrence": row.ordinal, "content_sha256": row.content_sha256, "kind": "Table"}
        for row in source_tables
    )
    witnesses.extend(
        {
            "source_occurrence": row["source_occurrence"],
            "content_sha256": row["content_sha256"],
            "kind": "RawRole",
            "role": row["kind"],
        }
        for row in roles
        if row["kind"] != "unsupported"
    )
    # A finding invalidates corresponding witness claims; the row census is
    # still retained to make every missing obligation reviewable.
    return {
        "schema_version": "template-native-office-source-survival-v1",
        "source_ast_sha256": hashlib.sha256(source_ast).hexdigest(),
        "filtered_ast_sha256": hashlib.sha256(filtered_ast).hexdigest(),
        "native_ast_sha256": hashlib.sha256(native_ast).hexdigest(),
        "package_sha256": hashlib.sha256(package).hexdigest(),
        "status": "failed" if findings else "blocked" if blockers else "observed",
        "findings": findings,
        "blockers": blockers,
        "occurrences": [
            {"ordinal": row.ordinal, "kind": row.kind, "content_sha256": row.content_sha256} for row in occurrences
        ],
        "witnesses": witnesses,
        "raw_roles": list(roles),
        "source_math_count": len(source_math),
        "native_math_count": len(native_math),
        "prose_text_sha256": hashlib.sha256(expected_text.encode()).hexdigest(),
        "assurance": (
            "independent source/package survival; native ink, geometry and supervised controls remain mandatory"
        ),
    }
