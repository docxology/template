"""Markdown reader: repo formalism conventions -> typed blocks.

A READER only — it never renders. It parses the repository's existing
Pandoc fenced-div conventions into typed blocks:

- ``::: {.definition #def:x}`` / ``.theorem`` / ``.lemma`` / ``.proposition``
  become ``FormalStatement`` blocks (``kind`` from the class name).
- ``::: {.claim #claim:y}`` becomes a ``Claim``; ``[@ev:e1]`` citations in
  its body become SUPPORTS edges (tier policy taken from ``tier=``
  attribute on the div).
- ``::: {.evidence #ev:e1 tier=strong}`` becomes an ``Evidence`` block.
- ``::: {.figure #fig:f}`` / ``.table`` / ``.dataset`` become the matching
  artifact blocks (``path=`` attribute).
- ``# Heading`` lines become ``Section`` blocks; subsequent div blocks are
  appended to the most recent section.

Anything else in the file is ignored. Malformed attribute lists raise
``ReaderError`` carrying a ``FORMAL.READER_PARSE`` diagnostic.
"""

from __future__ import annotations

import re

from infrastructure.formal_contracts.checker import Diagnostic
from infrastructure.formal_contracts.model import (
    Block,
    Claim,
    Dataset,
    DependencyEdge,
    EdgeKind,
    Evidence,
    EvidenceTier,
    Figure,
    FormalStatement,
    MatchPolicy,
    Section,
    Table,
)

_DIV_OPEN = re.compile(r"^:::\s*\{([^}]*)\}\s*$")
_DIV_CLOSE = ":::"
_CITE = re.compile(r"\[@([^\]]+)\]")
_ATTR = re.compile(r"(\.[\w-]+)|(?:#([\w:-]+))|(?:([\w-]+)=([\w./:-]+))")
_FORMAL_KINDS = {"definition", "theorem", "lemma", "proposition"}


class ReaderError(ValueError):
    """Raised when a fenced-div attribute list cannot be parsed."""

    def __init__(self, message: str, line_no: int) -> None:
        self.diagnostic = Diagnostic(code="FORMAL.READER_PARSE", message=message, block_id=None)
        super().__init__(f"line {line_no}: {message}")


def _parse_attrs(attr_text: str, line_no: int) -> tuple[list[str], dict[str, str]]:
    classes: list[str] = []
    attrs: dict[str, str] = {}
    for m in _ATTR.finditer(attr_text):
        if m.group(1):
            classes.append(m.group(1)[1:])
        elif m.group(2):
            attrs["id"] = m.group(2)
        else:
            attrs[m.group(3)] = m.group(4)
    if not classes:
        raise ReaderError(f"no class in div attributes: {attr_text!r}", line_no)
    return classes, attrs


def _make_block(kind: str, block_id: str, body: str, attrs: dict[str, str], line_no: int) -> Block:
    if kind == "claim":
        tier = EvidenceTier.__members__.get(attrs.get("tier", "WEAK").upper(), None)
        if attrs.get("tier") and tier is None:
            raise ReaderError(f"unknown tier {attrs['tier']!r}", line_no)
        edges = tuple(
            DependencyEdge(
                target_id=cite,
                kind=EdgeKind.SUPPORTS,
                policy=MatchPolicy(min_tier=tier or EvidenceTier.WEAK),
            )
            for cite in _CITE.findall(body)
        )
        return Claim(id=block_id, title=attrs.get("title", ""), statement=body.strip(), evidence=edges)
    if kind == "evidence":
        tier = EvidenceTier.__members__.get(attrs.get("tier", "WEAK").upper())
        if tier is None:
            raise ReaderError(f"unknown tier {attrs.get('tier', '')!r}", line_no)
        return Evidence(id=block_id, title=attrs.get("title", ""), tier=tier)
    if kind in _FORMAL_KINDS:
        refs = tuple(_CITE.findall(body))
        return FormalStatement(id=block_id, title=attrs.get("title", ""), kind=kind, resolves_to=refs)
    if kind in {"figure", "table", "dataset"}:
        cls = {"figure": Figure, "table": Table, "dataset": Dataset}[kind]
        kwargs: dict[str, str | int | None] = {"path": attrs.get("path", "")}
        if kind == "dataset" and "records" in attrs:
            kwargs["records"] = int(attrs["records"])
        block = cls(id=block_id, title=attrs.get("title", ""), **kwargs)
        assert isinstance(block, Block)
        return block
    raise ReaderError(f"unsupported div class {kind!r}", line_no)


def read_blocks_with_errors(
    text: str,
) -> tuple[tuple[Block, ...], tuple[Diagnostic, ...]]:
    """Tolerant variant of :func:`read_blocks` for round-tripping real
    manuscripts: per-div problems (unknown class, missing id, bad tier)
    are returned as ``FORMAL.READER_PARSE`` diagnostics and the affected
    div is skipped, instead of aborting the whole parse. Structural
    errors that leave the state machine ambiguous (an unclosed div) still
    raise ``ReaderError``."""
    blocks: list[Block] = []
    errors: list[Diagnostic] = []
    current_section: Section | None = None
    in_div = False
    div_kind = ""
    div_id = ""
    div_attrs: dict[str, str] = {}
    div_body: list[str] = []
    div_line = 0

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if in_div:
            if line == _DIV_CLOSE:
                if div_kind != "__skip__":
                    try:
                        blocks.append(_make_block(div_kind, div_id, "\n".join(div_body), div_attrs, div_line))
                    except ReaderError as exc:
                        errors.append(exc.diagnostic)
                in_div = False
                div_body = []
            else:
                div_body.append(raw)
            continue
        if line.startswith(":::"):
            if line == _DIV_CLOSE:
                continue  # stray close; ignore
            try:
                classes, attrs = _parse_attrs(line[3:], line_no)
                kind = classes[0]
                block_id = attrs.pop("id", classes[1] if len(classes) > 1 else "")
                if not block_id:
                    raise ReaderError("div has no id", line_no)
            except ReaderError as exc:
                errors.append(exc.diagnostic)
                in_div = True  # still consume the body until its close
                div_kind, div_id, div_attrs, div_body, div_line = (
                    "__skip__",
                    "",
                    {},
                    [],
                    line_no,
                )
                continue
            if kind == "section":
                current_section = Section(id=block_id, title=attrs.get("title", ""))
                blocks.append(current_section)
                continue
            in_div, div_kind, div_id, div_attrs, div_body, div_line = (
                True,
                kind,
                block_id,
                attrs,
                [],
                line_no,
            )
            continue
        if line.startswith("#") and not line.startswith("##"):
            current_section = Section(id=f"sec:{line.lstrip('#').strip().lower().replace(' ', '-')}")
            blocks.append(current_section)
            continue

    if in_div:
        raise ReaderError(f"unclosed div starting at line {div_line}", div_line)

    # Attach non-section blocks to the most recent section, in document order.
    attached: list[Block] = []
    children: dict[str, list[str]] = {}
    last_section: Section | None = None
    for block in blocks:
        attached.append(block)
        if isinstance(block, Section):
            last_section = block
            children.setdefault(block.id, [])
        elif last_section is not None:
            children[last_section.id].append(block.id)
    sections = {
        b.id: Section(id=b.id, title=b.title, children=tuple(children[b.id]))
        for b in attached
        if isinstance(b, Section)
    }
    return tuple(sections.get(b.id, b) for b in attached), tuple(errors)


def read_blocks(text: str) -> tuple[Block, ...]:
    """Parse markdown formalism divs and headings into typed blocks."""
    blocks: list[Block] = []
    current_section: Section | None = None
    in_div = False
    div_kind = ""
    div_id = ""
    div_attrs: dict[str, str] = {}
    div_body: list[str] = []
    div_line = 0

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if in_div:
            if line == _DIV_CLOSE:
                blocks.append(_make_block(div_kind, div_id, "\n".join(div_body), div_attrs, div_line))
                in_div = False
                div_body = []
            else:
                div_body.append(raw)
            continue
        if line.startswith(":::"):
            if line == _DIV_CLOSE:
                continue  # stray close; ignore
            classes, attrs = _parse_attrs(line[3:], line_no)
            kind = classes[0]
            block_id = attrs.pop("id", classes[1] if len(classes) > 1 else "")
            if not block_id:
                raise ReaderError("div has no id", line_no)
            if kind == "section":
                current_section = Section(id=block_id, title=attrs.get("title", ""))
                blocks.append(current_section)
                continue
            in_div, div_kind, div_id, div_attrs, div_body, div_line = (
                True,
                kind,
                block_id,
                attrs,
                [],
                line_no,
            )
            continue
        if line.startswith("#") and not line.startswith("##"):
            current_section = Section(id=f"sec:{line.lstrip('#').strip().lower().replace(' ', '-')}")
            blocks.append(current_section)
            continue

    if in_div:
        raise ReaderError(f"unclosed div starting at line {div_line}", div_line)

    # Attach non-section blocks to the most recent section, in document order.
    attached: list[Block] = []
    children: dict[str, list[str]] = {}
    last_section: Section | None = None
    for block in blocks:
        attached.append(block)
        if isinstance(block, Section):
            last_section = block
            children.setdefault(block.id, [])
        elif last_section is not None:
            children[last_section.id].append(block.id)
    sections = {
        b.id: Section(id=b.id, title=b.title, children=tuple(children[b.id]))
        for b in attached
        if isinstance(b, Section)
    }
    return tuple(sections.get(b.id, b) for b in attached)


__all__ = ["ReaderError", "read_blocks"]
