"""Bounded source-only Pandoc occurrence and scientific structure compilation."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compile_semantic_ast(sources: tuple[tuple[str, bytes], ...], ast_bytes: bytes) -> dict[str, Any]:
    """Retain every typed occurrence, including descendants of unsupported nodes.

    Notes are projected in the HTML writer's footer order. Each table cell and
    each note retains separate content and placement obligations. Raw or unknown
    constructs remain explicit blockers, with exact payload custody; their child
    text, math and assets are never discarded.
    """
    from infrastructure.reporting.native_format_content_contracts import (
        ContentBlock,
        MAX_BLOCKS,
        MAX_SOURCE_BYTES,
        MAX_TOKENS,
        text_tokens,
    )

    if (
        not sources
        or len({name for name, _ in sources}) != len(sources)
        or len(ast_bytes) > 32 * 1024 * 1024
        or sum(len(data) for _, data in sources) > MAX_SOURCE_BYTES
    ):
        raise ValueError("semantic source contract exceeds its finite input budget")
    document = json.loads(ast_bytes)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("blocks"), list)
        or not document.get("pandoc-api-version")
    ):
        raise ValueError("semantic source contract requires actual Pandoc JSON")
    result: dict[str, Any] = {
        key: []
        for key in ("blocks", "blockers", "maths", "images", "links", "citations", "tables", "footnotes", "occurrences")
    }
    note_queue: list[tuple[str, list[Any]]] = []

    def ident(path: str) -> str:
        return f"ast:{path}"

    def census(value: Any, path: str, depth: int = 0) -> None:
        if depth > 256:
            raise ValueError("semantic source nesting budget exceeded")
        if isinstance(value, dict):
            if "t" in value:
                result["occurrences"].append(
                    {
                        "source_id": ident(path),
                        "tag": value["t"],
                        "payload_sha256": hashlib.sha256(
                            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
                        ).hexdigest(),
                    }
                )
                if len(result["occurrences"]) > 100000:
                    raise ValueError("semantic source node budget exceeded")
            for key, child in value.items():
                if key != "t":
                    census(child, f"{path}/{key}", depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                census(child, f"{path}/{index}", depth + 1)

    census(document["blocks"], "blocks")
    metadata = dict(document.get("meta", {}))
    # Pandoc serializes command-line bibliography filenames into metadata. The
    # producer AST and its exact argv retain those bytes, while portable source
    # obligations bind bibliography contents instead of temporary filenames.
    if "bibliography" in metadata:
        bibliography_hashes = [hashlib.sha256(data).hexdigest() for name, data in sources if name.endswith(".bib")]
        if not bibliography_hashes:
            result["blockers"].append("source bibliography metadata lacks consumed bibliography bytes")
        metadata["bibliography"] = {
            "t": "MetaList",
            "c": [{"t": "MetaString", "c": f"source-sha256:{digest}"} for digest in bibliography_hashes],
        }
    census(metadata, "meta")

    def blocker(path: str, reason: str) -> None:
        result["blockers"].append(f"{ident(path)}: {reason}")

    def inline(nodes: list[Any], path: str, kind: str, destination: list[Any]) -> None:
        pending: list[str] = []
        segment = 0

        def flush() -> None:
            nonlocal segment
            tokens = text_tokens("".join(pending))
            if tokens:
                destination.append(ContentBlock(f"{ident(path)}:text:{segment}", kind, 0, tokens))
                segment += 1
            pending.clear()

        def visit(node: Any, current: str) -> None:
            if not isinstance(node, dict):
                blocker(current, "malformed inline requires separate source witness")
                return
            content: Any
            tag, content = node.get("t"), node.get("c")
            if tag == "Str" and isinstance(content, str):
                pending.append(content)
            elif tag in {"Space", "SoftBreak", "LineBreak"}:
                pending.append(" ")
            elif tag in {"Emph", "Strong", "Underline", "Strikeout", "SmallCaps", "Superscript", "Subscript"}:
                for index, child in enumerate(content):
                    visit(child, f"{current}/c/{index}")
            elif tag == "Code":
                pending.append(content[1])
            elif tag in {"Span", "Link", "Cite", "Quoted"}:
                children = content[1]
                if tag == "Cite":
                    flush()
                if tag == "Link":
                    result["links"].append((ident(current), content[2][0]))
                elif tag == "Cite":
                    result["citations"].append((ident(current), tuple(item["citationId"] for item in content[0])))
                elif tag == "Quoted":
                    pending.append("“" if content[0]["t"] == "DoubleQuote" else "‘")
                for index, child in enumerate(children):
                    visit(child, f"{current}/c/1/{index}")
                if tag == "Quoted":
                    pending.append("”" if content[0]["t"] == "DoubleQuote" else "’")
                if tag == "Cite":
                    flush()
            elif tag == "Math":
                flush()
                result["maths"].append((ident(current), content[1]))
            elif tag == "Image":
                flush()
                alt = "".join(
                    child.get("c", "") if child.get("t") == "Str" else " " if child.get("t") == "Space" else ""
                    for child in content[1]
                )
                if not alt or any(child.get("t") not in {"Str", "Space"} for child in content[1]):
                    blocker(current, "original rich/empty image alternative requires an independent writer alt model")
                    alt = ""
                result["images"].append((ident(current), content[2][0], alt))
            elif tag == "Note":
                flush()
                note_queue.append((ident(current), content))
            else:
                flush()
                blocker(current, f"unsupported inline {tag}")
                descendants(content, f"{current}/c", destination)

        for index, node in enumerate(nodes):
            visit(node, f"{path}/{index}")
        flush()

    def descendants(value: Any, path: str, destination: list[Any]) -> None:
        if isinstance(value, dict) and "t" in value:
            if value["t"] in {"Str", "Math", "Image", "Note", "Cite", "Link", "Code", "RawInline"}:
                inline([value], path, "body", destination)
            else:
                block(value, path, destination)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                descendants(child, f"{path}/{index}", destination)
        elif isinstance(value, dict):
            for key, child in value.items():
                descendants(child, f"{path}/{key}", destination)

    def table(content: Any, path: str, destination: list[Any]) -> None:
        from infrastructure.reporting.native_format_html_table_witness import source_attributes

        if not isinstance(content, list) or len(content) != 6:
            blocker(path, "unsupported legacy/malformed table structure")
            descendants(content, f"{path}/c", destination)
            return
        caption_first = len(destination)
        descendants(content[1], f"{path}/c/1", destination)
        caption_ids = [item.id for item in destination[caption_first:]]
        column_specs = []
        for column in content[2]:
            width = None if column[1]["t"] == "ColWidthDefault" else column[1].get("c")
            if width is not None and (type(width) not in {int, float} or not 0 < width <= 1):
                blocker(path, "unsupported column width declaration")
            column_specs.append({"alignment": column[0]["t"], "width": width, "payload": column})
        rows = []
        sections = [("head", content[3][1], f"{path}/c/3/1", len(content[2]))]
        for index, body in enumerate(content[4]):
            sections.extend(
                [
                    ("body-head", body[2], f"{path}/c/4/{index}/2", len(content[2])),
                    ("body", body[3], f"{path}/c/4/{index}/3", body[1]),
                ]
            )
        sections.append(("foot", content[5][1], f"{path}/c/5/1", 0))
        for section, source_rows, row_path, header_columns in sections:
            for row_index, row in enumerate(source_rows):
                cells = []
                source_column = 0
                for cell_index, cell in enumerate(row[1]):
                    cell_path = f"{row_path}/{row_index}/1/{cell_index}"
                    first = len(destination)
                    for child_index, child in enumerate(cell[4]):
                        block(child, f"{cell_path}/4/{child_index}", destination)
                    cells.append(
                        {
                            "source_id": ident(cell_path),
                            "attributes": source_attributes(cell[0]),
                            "alignment": cell[1]["t"],
                            "row_span": cell[2],
                            "col_span": cell[3],
                            "header": section in {"head", "body-head"} or source_column < header_columns,
                            "tokens": [token for item in destination[first:] for token in item.tokens],
                            "block_ids": [item.id for item in destination[first:]],
                        }
                    )
                    source_column += cell[3]
                rows.append(
                    {
                        "section": section,
                        "source_id": ident(f"{row_path}/{row_index}"),
                        "attributes": source_attributes(row[0]),
                        "cells": cells,
                    }
                )
        section_attributes = [{"native_section": "thead", "attributes": source_attributes(content[3][0])}]
        section_attributes.extend(
            {"native_section": "tbody", "attributes": source_attributes(body[0])} for body in content[4]
        )
        section_attributes.append({"native_section": "tfoot", "attributes": source_attributes(content[5][0])})
        result["tables"].append(
            {
                "source_id": ident(path),
                "columns": len(content[2]),
                "rows": rows,
                "attributes": source_attributes(content[0]),
                "column_specs": column_specs,
                "caption_block_ids": caption_ids,
                "section_attributes": section_attributes,
            }
        )

    def block(node: Any, path: str, destination: list[Any]) -> None:
        if not isinstance(node, dict):
            blocker(path, "malformed block requires separate source witness")
            return
        content: Any
        tag, content = node.get("t"), node.get("c")
        if tag in {"Para", "Plain"}:
            inline(content, f"{path}/c", "body", destination)
        elif tag == "Header":
            inline(content[2], f"{path}/c/2", f"heading:{content[0]}", destination)
        elif tag == "CodeBlock":
            destination.append(ContentBlock(f"{ident(path)}:code", "code", 0, text_tokens(content[1])))
        elif tag == "Div":
            descendants(content[1], f"{path}/c/1", destination)
        elif tag == "Table":
            table(content, path, destination)
        elif tag == "OrderedList":
            descendants(content[1], f"{path}/c/1", destination)
        elif tag == "DefinitionList":
            for index, (term, definitions) in enumerate(content):
                inline(term, f"{path}/c/{index}/0", "body", destination)
                descendants(definitions, f"{path}/c/{index}/1", destination)
        elif tag in {"BlockQuote", "BulletList", "Figure", "LineBlock"}:
            if tag == "LineBlock":
                for index, line in enumerate(content):
                    inline(line, f"{path}/c/{index}", "body", destination)
            else:
                descendants(content, f"{path}/c", destination)
        elif tag in {"HorizontalRule", "Null"}:
            pass
        else:
            blocker(path, f"unsupported block {tag}")
            descendants(content, f"{path}/c", destination)

    for index, item in enumerate(document["blocks"]):
        block(item, f"blocks/{index}", result["blocks"])
    # Writer options supplied by the authenticated parse command are not page
    # content. Other metadata retains a typed source obligation until its title,
    # byline, date or domain-specific placement has an independent witness.
    for key in document.get("meta", {}):
        if key not in {"link-citations", "bibliography", "references", "csl"}:
            blocker(f"meta/{key}", "independent metadata page placement unsupported")
    note_index = 0
    while note_index < len(note_queue):
        source_id, children = note_queue[note_index]
        note_blocks: list[Any] = []
        for index, item in enumerate(children):
            block(item, f"{source_id.removeprefix('ast:')}/c/{index}", note_blocks)
        result["footnotes"].append(
            {
                "source_id": source_id,
                "ordinal": note_index + 1,
                "blocks": [{"id": item.id, "kind": item.kind, "tokens": list(item.tokens)} for item in note_blocks],
            }
        )
        note_index += 1
    all_blocks = [*result["blocks"], *(b for n in result["footnotes"] for b in n["blocks"])]
    if (
        len(all_blocks) > MAX_BLOCKS
        or sum(len(b.tokens if isinstance(b, ContentBlock) else b["tokens"]) for b in all_blocks) > MAX_TOKENS
    ):
        raise ValueError("semantic source projection budget exceeded")
    if not all_blocks and not result["maths"] and not result["images"]:
        result["blockers"].append("semantic source contains no obligations")
    return result
