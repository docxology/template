"""Independent source occurrence and literal-text plans for scientific PDFs.

The actual original Pandoc parser and consumed hydration are admitted by the
enclosing worker. No candidate PDF/TeX, producer pass bit or reference equality
determines this source ledger. Unknown syntax remains an explicit obligation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import (
    ContentBlock,
    NativeContentContract,
    text_tokens,
)

SCHEMA = "template-native-pdf-semantic-source-plan-v1"
MAX_BYTES = 4 * 1024 * 1024
MAX_NODES = 100_000
MAX_TEXT_BLOCKS = 20_000
MAX_TOKENS = 250_000


def exact_figure_caption_alias(node: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str | int]] | None:
    """Recognize the actual modern Figure's one equal visible/alt AST pair.

    The alias is Source DATA. Every visible descendant still requires its own
    native caption witness and the image's pixels and complete source parity.
    """
    if node.get("t") != "Figure":
        return None
    value = node.get("c")
    if not isinstance(value, list) or len(value) != 3:
        return None
    caption, body = value[1], value[2]
    if (
        not isinstance(caption, list)
        or len(caption) != 2
        or caption[0] is not None
        or not isinstance(caption[1], list)
        or len(caption[1]) != 1
        or not isinstance(caption[1][0], dict)
        or caption[1][0].get("t") not in {"Plain", "Para"}
        or not isinstance(body, list)
        or len(body) != 1
        or not isinstance(body[0], dict)
        or body[0].get("t") not in {"Plain", "Para"}
        or not isinstance(body[0].get("c"), list)
        or len(body[0].get("c", [])) != 1
    ):
        return None
    image = body[0]["c"][0]
    if (
        not isinstance(image, dict)
        or image.get("t") != "Image"
        or not isinstance(image.get("c"), list)
        or len(image["c"]) != 3
        or not isinstance(caption[1][0].get("c"), list)
        or image["c"][1] != caption[1][0]["c"]
    ):
        return None
    return caption[1][0]["c"], ["c", 2, 0, "c", 0]


def strict_ast(content: bytes) -> dict[str, Any]:
    """Reject ambiguous JSON before interpreting any source occurrence."""
    if not content or len(content) > MAX_BYTES:
        raise ValueError("PDF semantic AST exceeds its finite byte budget")

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise ValueError("PDF semantic AST repeats a JSON field")
            result[key] = value
        return result

    document = json.loads(content, object_pairs_hook=pairs)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("blocks"), list)
        or not isinstance(document.get("pandoc-api-version"), list)
        or not document["pandoc-api-version"]
    ):
        raise ValueError("PDF semantic source requires original Pandoc JSON")
    return document


@dataclass(frozen=True)
class PDFSemanticPlan:
    """All source forms and their separately required independent witnesses."""

    artifact_id: str
    source_ast_sha256: str
    sources: tuple[tuple[str, str], ...]
    text: tuple[ContentBlock, ...]
    notes: tuple[ContentBlock, ...]
    occurrences: tuple[dict[str, Any], ...]
    tables: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...]
    literal_members: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA, **asdict(self)}

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def text_contract(self, *, notes: bool = False) -> NativeContentContract:
        """A scoped text witness; it does not grant scientific acceptance."""
        return NativeContentContract(self.artifact_id, self.sources, self.notes if notes else self.text, ())


def compile_pdf_semantic_plan(
    artifact_id: str,
    sources: tuple[tuple[str, bytes], ...],
    ast_bytes: bytes,
    *,
    citation_reference: dict[str, Any] | None = None,
) -> PDFSemanticPlan:
    """Preserve exact source identities, table grids and nested occurrences.

    Citation source display text is deliberately excluded: it is not the
    independently rendered natbib label. Math, citations, images, annotations,
    raw TeX, footnote placement and table geometry require native witnesses.
    """
    if not sources or sum(len(content) for _, content in sources) > MAX_BYTES:
        raise ValueError("PDF semantic original sources are empty or excessive")
    if len({path for path, _ in sources}) != len(sources):
        raise ValueError("PDF semantic source paths are ambiguous")
    document = strict_ast(ast_bytes)
    citation_labels = {}
    raw_citation_labels = {}
    if citation_reference is not None:
        from infrastructure.reporting.native_pdf_citations import CITATION_POLICY, CITATION_SCHEMA
        from infrastructure.reporting.native_format_pdf_raw_natbib import independent_raw_natbib_labels

        if citation_reference.get("schema_version") != CITATION_SCHEMA or citation_reference.get(
            "policy_digest"
        ) != canonical_digest(CITATION_POLICY):
            raise ValueError("PDF semantic citation labels require an independently admitted natbib reference")
        for row in citation_reference["occurrences"]:
            source = row["source"]
            if source["kind"] != "pandoc-cite":
                continue  # Raw original citation commands keep their raw-node witness.
            path = source["path"]
            if (
                path in citation_labels
                or not isinstance(row["native_text"], str)
                or not text_tokens(row["native_text"])
            ):
                raise ValueError("PDF semantic original citation labels are ambiguous")
            citation_labels[path] = row
        raw_citation_labels = independent_raw_natbib_labels(ast_bytes, citation_reference)
    text: list[ContentBlock] = []
    notes: list[ContentBlock] = []
    occurrences: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    blockers: list[str] = []
    literal_members: list[dict[str, Any]] = []
    if document.get("meta"):
        blockers.append("original PDF source AST metadata requires independent frontmatter/native admission")
    visited = 0
    figure_captions: list[tuple[tuple[str, ...], tuple[str, ...], str | None, list[str]]] = []

    def literal_alternative(nodes: list[dict[str, Any]]) -> tuple[str, ...] | None:
        """Image alternatives are source metadata, not a second visible caption."""
        parts = []
        for node in nodes:
            if node.get("t") == "Str" and isinstance(node.get("c"), str):
                parts.append(node["c"])
            elif node.get("t") in {"Space", "SoftBreak", "LineBreak"}:
                parts.append(" ")
            else:
                return None
        return text_tokens("".join(parts))

    def tick() -> None:
        nonlocal visited
        visited += 1
        if visited > MAX_NODES:
            raise ValueError("PDF semantic occurrence budget exceeded")

    def occurrence(node: dict[str, Any], path: str, context: str) -> None:
        content = json.dumps(node["c"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        occurrences.append(
            {
                "identity": path,
                "kind": node["t"],
                "context": context,
                "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "content": node["c"],
                "text_cursor": len(notes) if context == "footnote" else len(text),
            }
        )

    def inlines(values: Any, path: str, context: str, *, note: bool = False) -> list[str]:
        if not isinstance(values, list):
            raise ValueError("PDF semantic inline list is malformed")
        pending: list[str] = []
        members: list[str] = []
        literal_spans: list[tuple[str, str, int, int]] = []
        ids: list[str] = []
        chunk = 0

        def flush() -> None:
            nonlocal chunk
            raw = "".join(pending)
            tokens = text_tokens(raw)
            pending.clear()
            if tokens:
                identity = f"{path}/text/{chunk}"
                chunk += 1
                (notes if note else text).append(ContentBlock(identity, context, 0, tokens))
                spans = []
                for source_identity, kind, start, end in literal_spans:
                    before, selected, after = (
                        text_tokens(raw[:start]),
                        text_tokens(raw[start:end]),
                        text_tokens(raw[end:]),
                    )
                    # Only exact Source token partitions identify a subrole. A
                    # word merged across an inline boundary remains unsupported.
                    if selected and before + selected + after == tokens:
                        spans.append(
                            {
                                "identity": source_identity,
                                "kind": kind,
                                "token_span": [len(before), len(before) + len(selected)],
                            }
                        )
                literal_members.append(
                    {
                        "block_id": identity,
                        "context": context,
                        "ast_paths": list(members),
                        "occurrence_token_spans": spans,
                    }
                )
                ids.append(identity)
            members.clear()
            literal_spans.clear()

        def visit(node: Any, identity: str) -> None:
            tick()
            if not isinstance(node, dict) or not isinstance(node.get("t"), str):
                raise ValueError("PDF semantic inline node is malformed")
            tag = node["t"]
            value: Any = node.get("c")
            if tag == "Str":
                if not isinstance(value, str):
                    raise ValueError("PDF semantic literal text is malformed")
                pending.append(value)
                members.append(identity)
            elif tag in {"Space", "SoftBreak", "LineBreak"}:
                pending.append(" ")
                members.append(identity)
            elif tag in {"Emph", "Strong", "Underline", "Strikeout", "SmallCaps", "Superscript", "Subscript"}:
                for index, child in enumerate(value):
                    visit(child, f"{identity}/c/{index}")
                if tag in {"Superscript", "Subscript"}:
                    occurrence(node, identity, context)
            elif tag == "Code":
                start = len("".join(pending))
                pending.append(value[1])
                literal_spans.append((identity, tag, start, start + len(value[1])))
                members.append(identity)
                occurrence(node, identity, context)
            elif tag in {"Span", "Link"}:
                if tag == "Link":
                    occurrence(node, identity, context)
                start, initial_chunk = len("".join(pending)), chunk
                for index, child in enumerate(value[1]):
                    visit(child, f"{identity}/c/1/{index}")
                if tag == "Link" and chunk == initial_chunk:
                    literal_spans.append((identity, tag, start, len("".join(pending))))
            elif tag == "Quoted":
                quote = value[0]["t"]
                if quote not in {"DoubleQuote", "SingleQuote"}:
                    raise ValueError("PDF semantic quotation mode is malformed")
                pending.append("“" if quote == "DoubleQuote" else "‘")
                for index, child in enumerate(value[1]):
                    visit(child, f"{identity}/c/1/{index}")
                pending.append("”" if quote == "DoubleQuote" else "’")
            elif tag == "RawInline" and identity in raw_citation_labels:
                label = raw_citation_labels[identity]
                if label["source_node"] != node:
                    raise ValueError("raw natbib label does not identify its exact original source node")
                occurrence(node, identity, context)
                occurrences[-1]["raw_citation_reference_ids"] = list(label["reference_ids"])
                pending.append(label["native_text"])
                members.append(identity)
            elif tag in {"Math", "Cite", "Image", "RawInline"}:
                if tag == "Cite" and identity in citation_labels:
                    occurrence(node, identity, context)
                    citation_occurrence = occurrences[-1]
                    census(value, f"{identity}/c", context)
                    label = citation_labels[identity]
                    if label["source"]["original"] != node or tuple(label["keys"]) != tuple(
                        row["citationId"] for row in value[0]
                    ):
                        raise ValueError("PDF semantic citation interpretation differs from original AST occurrence")
                    pending.append(label["native_text"])
                    members.append(identity)
                    citation_occurrence["citation_reference_id"] = label["id"]
                    # Keep this label between its exact original prose neighbours.
                    # It is independently interpreted native text, never Cite.c[1].
                    return
                flush()
                occurrence(node, identity, context)
                if tag == "Cite":
                    census(value, f"{identity}/c", context)
                if tag == "Image":
                    alternative = literal_alternative(value[1])
                    if figure_captions and (identity == figure_captions[-1][2]):
                        # Modern Pandoc retains the same source caption in both
                        # Figure.caption and Image.alt. Account for the exact
                        # alias using the one independently matched visible
                        # caption; requiring it twice would invent source text.
                        occurrences[-1]["rendered_caption_text_ids"] = list(figure_captions[-1][1])
                        occurrences[-1]["rendered_caption_occurrence_ids"] = list(figure_captions[-1][3])
                        if identity == figure_captions[-1][2]:
                            occurrences[-1]["exact_caption_ast_alias"] = {
                                "visible": identity.removesuffix("/c/2/0/c/0") + "/c/1/1/0/c",
                                "alternative": identity + "/c/1",
                                "inline_ast_sha256": canonical_digest(value[1]),
                            }
                    elif not figure_captions and value[2][1].startswith("fig:"):
                        caption_ids = inlines(value[1], f"{identity}/c/1", "caption", note=note)
                        ids.extend(caption_ids)
                        occurrences[-1]["rendered_caption_text_ids"] = list(caption_ids)
                    elif alternative:
                        blockers.append(
                            f"{identity}: noncaption source image alternative requires native metadata witness"
                        )
                    elif alternative is None:
                        blockers.append(
                            f"{identity}: scientific image alternative requires independent caption/native witness"
                        )
                        census(value[1], f"{identity}/c/1", context)
            elif tag == "Note":
                flush()
                occurrence(node, identity, context)
                for index, child in enumerate(value):
                    block(child, f"{identity}/c/{index}", "footnote", note=True)
            else:
                flush()
                blockers.append(f"{identity}: unsupported source inline {tag}")
                census(value, f"{identity}/c", context)

        for index, node in enumerate(values):
            visit(node, f"{path}/{index}")
        flush()
        return ids

    def census(value: Any, path: str, context: str) -> None:
        """Unknown containers cannot hide nested scientific occurrences."""
        tick()
        if isinstance(value, dict):
            if value.get("t") in {"Math", "Cite", "Image", "RawInline", "RawBlock", "Table", "Note"}:
                occurrence(value, path, context)
            for key, child in value.items():
                census(child, f"{path}/{key}", context)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                census(child, f"{path}/{index}", context)

    def table(node: dict[str, Any], path: str, *, note: bool) -> None:
        value = node["c"]
        if not isinstance(value, list) or len(value) != 6:
            raise ValueError("PDF semantic table requires six-field Pandoc schema")
        _, caption, columns, head, bodies, foot = value
        if not isinstance(columns, list) or not columns:
            raise ValueError("PDF semantic table column declaration is empty")
        for index, column in enumerate(columns):
            if not isinstance(column, list) or len(column) != 2:
                raise ValueError("PDF semantic table column schema is malformed")
            if column[0].get("t") != "AlignDefault" or column[1].get("t") != "ColWidthDefault":
                blockers.append(
                    f"{path}/column/{index}: declared table alignment/width requires native structural witness"
                )
        if caption[0] is not None:
            inlines(caption[0], f"{path}/c/1/0", "caption", note=note)
        for index, child in enumerate(caption[1]):
            block(child, f"{path}/c/1/1/{index}", "caption", note=note)
        groups = [("head", head[1], f"{path}/c/3/1")]
        for index, body in enumerate(bodies):
            if not isinstance(body, list) or len(body) != 4:
                raise ValueError("PDF semantic table body schema is malformed")
            groups.extend((("body-head", body[2], f"{path}/c/4/{index}/2"), ("body", body[3], f"{path}/c/4/{index}/3")))
        groups.append(("foot", foot[1], f"{path}/c/5/1"))
        rows: list[dict[str, Any]] = []
        row_index = 0
        for group, group_rows, group_path in groups:
            for local_index, row in enumerate(group_rows):
                if not isinstance(row, list) or len(row) != 2 or not isinstance(row[1], list):
                    raise ValueError("PDF semantic table row is malformed")
                cells = []
                column = 0
                for cell_index, cell in enumerate(row[1]):
                    cell_path = f"{group_path}/{local_index}/1/{cell_index}"
                    if not isinstance(cell, list) or len(cell) != 5:
                        raise ValueError("PDF semantic table cell is malformed")
                    if any(type(span) is not int or span < 1 for span in cell[2:4]):
                        raise ValueError("PDF semantic table spans are invalid")
                    before = len(notes if note else text)
                    before_occurrences = len(occurrences)
                    for index, child in enumerate(cell[4]):
                        block(child, f"{cell_path}/4/{index}", f"table:{path}:{row_index}:{column}", note=note)
                    blocks = (notes if note else text)[before:]
                    cells.append(
                        {
                            "identity": cell_path,
                            "column": column,
                            "row_span": cell[2],
                            "column_span": cell[3],
                            "text_ids": [child.id for child in blocks],
                            "occurrence_ids": [child["identity"] for child in occurrences[before_occurrences:]],
                        }
                    )
                    column += cell[3]
                if column > len(columns):
                    raise ValueError("PDF semantic table cells exceed declared columns")
                rows.append({"row": row_index, "group": group, "cells": cells})
                row_index += 1
        tables.append({"identity": path, "columns": len(columns), "rows": rows})

    def block(node: Any, path: str, context: str = "body", *, note: bool = False) -> None:
        tick()
        if not isinstance(node, dict) or not isinstance(node.get("t"), str):
            raise ValueError("PDF semantic block is malformed")
        tag = node["t"]
        value: Any = node.get("c")
        if tag in {"Para", "Plain"}:
            inlines(value, f"{path}/c", context, note=note)
        elif tag == "Header":
            inlines(value[2], f"{path}/c/2", f"heading:{value[0]}", note=note)
        elif tag == "CodeBlock":
            tokens = text_tokens(value[1])
            if tokens:
                (notes if note else text).append(ContentBlock(path, "code", 0, tokens))
                literal_members.append(
                    {
                        "block_id": path,
                        "context": "footnote" if note else "code",
                        "ast_paths": [path],
                        "occurrence_token_spans": [
                            {"identity": path, "kind": "CodeBlock", "token_span": [0, len(tokens)]}
                        ],
                    }
                )
            occurrence(node, path, context)
        elif tag in {"Div", "BlockQuote", "BulletList", "OrderedList", "DefinitionList", "Figure"}:
            if tag == "Div":
                children = [(child, f"{path}/c/1/{index}") for index, child in enumerate(value[1])]
            elif tag == "BlockQuote":
                children = [(child, f"{path}/c/{index}") for index, child in enumerate(value)]
            elif tag == "Figure":
                children = [(child, f"{path}/c/2/{index}") for index, child in enumerate(value[2])]
                # Figure captions are independent from Image alternatives.
                before_caption = len(notes if note else text)
                before_caption_occurrences = len(occurrences)
                exact_alias = exact_figure_caption_alias(node)
                for index, child in enumerate(value[1][1]):
                    block(child, f"{path}/c/1/1/{index}", "caption", note=note)
                caption_blocks = (notes if note else text)[before_caption:]
                figure_captions.append(
                    (
                        tuple(token for item in caption_blocks for token in item.tokens),
                        tuple(item.id for item in caption_blocks),
                        path + "/" + "/".join(map(str, exact_alias[1])) if exact_alias is not None else None,
                        [
                            item["identity"]
                            for item in occurrences[before_caption_occurrences:]
                            if item["kind"] == "Math"
                        ],
                    )
                )
            else:
                children = []
                items = value[1] if tag == "OrderedList" else value
                for index, item in enumerate(items):
                    item_path = f"{path}/c/1/{index}" if tag == "OrderedList" else f"{path}/c/{index}"
                    if tag == "DefinitionList":
                        inlines(item[0], f"{item_path}/0", context, note=note)
                        for definition_index, definition in enumerate(item[1]):
                            children.extend(
                                (child, f"{item_path}/1/{definition_index}/{child_index}")
                                for child_index, child in enumerate(definition)
                            )
                    else:
                        children.extend((child, f"{item_path}/{child_index}") for child_index, child in enumerate(item))
            for child, child_path in children:
                block(child, child_path, context, note=note)
            if tag == "Figure":
                figure_captions.pop()
        elif tag == "Table":
            occurrence(node, path, context)
            table(node, path, note=note)
        elif tag == "RawBlock":
            occurrence(node, path, context)
            if path in raw_citation_labels:
                label = raw_citation_labels[path]
                if label["source_node"] != node:
                    raise ValueError("raw natbib label does not identify its exact original source node")
                occurrences[-1]["raw_citation_reference_ids"] = list(label["reference_ids"])
                (notes if note else text).append(
                    ContentBlock(path + "/text", "citation", 0, text_tokens(label["native_text"]))
                )
        elif tag == "HorizontalRule":
            occurrence({"t": tag, "c": []}, path, context)
        else:
            blockers.append(f"{path}: unsupported source block {tag}")
            census(value, f"{path}/c", context)
        if len(text) + len(notes) > MAX_TEXT_BLOCKS:
            raise ValueError("PDF semantic text block budget exceeded")

    for index, node in enumerate(document["blocks"]):
        block(node, f"blocks/{index}")
    if sum(len(item.tokens) for item in (*text, *notes)) > MAX_TOKENS:
        raise ValueError("PDF semantic literal token budget exceeded")
    return PDFSemanticPlan(
        artifact_id,
        hashlib.sha256(ast_bytes).hexdigest(),
        tuple((path, hashlib.sha256(content).hexdigest()) for path, content in sources),
        tuple(text),
        tuple(notes),
        tuple(occurrences),
        tuple(tables),
        tuple(blockers),
        tuple(literal_members),
    )
