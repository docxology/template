"""Visible-text, token, math, and vertical geometry for accessible slides."""

from __future__ import annotations

import math
import re
from typing import Any

from infrastructure.rendering._slides_accessibility_contracts import (
    BIBLIOGRAPHIC_CITATION_CHARACTERS,
    BODY_CHARACTERS_PER_LINE_20PT,
    CROSS_REFERENCE_LABELS,
    LIST_CHARACTERS_PER_LINE_20PT,
    TABLE_LIST_INDENT_WIDTH_UNITS,
    TABLE_TOKEN_SAFETY_CHARACTERS,
    density_error,
    proportional_text_width_units,
    tex_hyphen_segments,
    tex_math_vertical_line_demand,
    tex_math_width_units,
    unsupported_tex_math_commands,
)
from infrastructure.rendering.latex_texttt import long_texttt_source_is_breakable


_WORD_RE = re.compile(r"[\w]+(?:[-'][\w]+)*", flags=re.UNICODE)
_BIBLIOGRAPHIC_CITATION_PLACEHOLDER = "(Author, Coauthor, et al., 0000)"
assert len(_BIBLIOGRAPHIC_CITATION_PLACEHOLDER) == BIBLIOGRAPHIC_CITATION_CHARACTERS
_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_LIST_CHARACTERS_PER_LINE_20PT = LIST_CHARACTERS_PER_LINE_20PT
_CROSS_REFERENCE_LABELS = CROSS_REFERENCE_LABELS


def _plain_text(value: object) -> str:
    """Extract human-readable text from a Pandoc JSON fragment."""

    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(part for item in value if (part := _plain_text(item)))
    if not isinstance(value, dict):
        return ""
    tag = value.get("t")
    content = value.get("c")
    if tag in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    if tag == "Cite" and isinstance(content, list) and content:
        citations = content[0]
        resolved_content = _plain_text(content[1]) if len(content) >= 2 else ""
        records = (
            [citation for citation in citations if isinstance(citation, dict)] if isinstance(citations, list) else []
        )
        bibliographic_identifiers = [
            identifier
            for record in records
            if isinstance((identifier := record.get("citationId")), str)
            and _CROSS_REFERENCE_LABELS.get(identifier.partition(":")[0]) is None
        ]
        resolved_bibliography = bool(bibliographic_identifiers) and not any(
            f"@{identifier}" in resolved_content or f"{identifier}?" in resolved_content
            for identifier in bibliographic_identifiers
        )
        if resolved_bibliography and resolved_content:
            resolved_mixed_citation = resolved_content
            crossref_fallbacks: list[str] = []
            for record in records:
                identifier = record.get("citationId")
                namespace = identifier.partition(":")[0] if isinstance(identifier, str) else ""
                label = _CROSS_REFERENCE_LABELS.get(namespace)
                if label is not None and identifier:
                    replacement = f"{label} {identifier}"
                    unresolved_forms = (f"@{identifier}", f"{identifier}?")
                    replaced = False
                    for unresolved in unresolved_forms:
                        if unresolved in resolved_mixed_citation:
                            resolved_mixed_citation = resolved_mixed_citation.replace(
                                unresolved,
                                replacement,
                                1,
                            )
                            replaced = True
                            break
                    if not replaced and identifier not in resolved_mixed_citation:
                        crossref_fallbacks.append(replacement)
            return " ".join([resolved_mixed_citation, *crossref_fallbacks])
        rendered: list[str] = []
        for record in records:
            identifier = record.get("citationId")
            namespace = identifier.partition(":")[0] if isinstance(identifier, str) else ""
            label = _CROSS_REFERENCE_LABELS.get(namespace)
            if label is not None and identifier:
                core = f"{label} {identifier}"
            else:
                identifier_width = len(identifier) + 3 if isinstance(identifier, str) else 0
                core = "a" * max(BIBLIOGRAPHIC_CITATION_CHARACTERS, identifier_width)
            prefix = _plain_text(record.get("citationPrefix"))
            suffix = _plain_text(record.get("citationSuffix"))
            rendered.append(" ".join(part for part in (prefix, core, suffix) if part))
        return " ".join(rendered or [_BIBLIOGRAPHIC_CITATION_PLACEHOLDER])
    if tag == "Link" and isinstance(content, list) and len(content) >= 2:
        return _plain_text(content[1])
    if tag == "Note":
        return ""
    if tag in {"Code", "Math"} and isinstance(content, list) and content:
        return str(content[-1])
    return _plain_text(content)


def _word_count(block: dict[str, Any]) -> int:
    """Count visible prose words without treating markup as content."""

    return len(_WORD_RE.findall(_plain_text(block)))


def _normalized_text_length(value: object) -> int:
    """Return visible character length after collapsing source whitespace."""

    return len(" ".join(_plain_text(value).split()))


def _inline_code_extra_width_units(value: object) -> int:
    if isinstance(value, list):
        return sum(_inline_code_extra_width_units(item) for item in value)
    if not isinstance(value, dict):
        return 0
    content = value.get("c")
    if value.get("t") == "Code" and isinstance(content, list) and content:
        code = str(content[-1])
        monospace_width = math.ceil(len(code) * (_BODY_CHARACTERS_PER_LINE_20PT / _LIST_CHARACTERS_PER_LINE_20PT))
        return max(0, monospace_width - proportional_text_width_units(code))
    return _inline_code_extra_width_units(content)


def _ordinary_physical_tokens(text: str) -> list[tuple[str, int]]:
    # Python's ``str.split`` treats U+00A0 as whitespace, but Pandoc renders
    # that character as TeX ``~``: a non-breaking join with no legal line
    # boundary.  Split only on ASCII source whitespace so geometry preflight
    # prices the same physical token that Beamer must typeset.
    return [
        (segment, proportional_text_width_units(segment))
        for token in re.split(r"[ \t\r\n\f\v]+", text)
        if token
        for segment in tex_hyphen_segments(token)
    ]


def _inline_physical_tokens(value: object) -> list[tuple[str, int]]:
    """Return source-aligned indivisible token widths for projected prose."""

    if isinstance(value, str):
        return _ordinary_physical_tokens(value)
    if isinstance(value, list):
        return [token for item in value for token in _inline_physical_tokens(item)]
    if not isinstance(value, dict):
        return []
    tag = value.get("t")
    content = value.get("c")
    if tag in {"Space", "SoftBreak", "LineBreak", "Note"}:
        return []
    if tag == "Str" and isinstance(content, str):
        return _ordinary_physical_tokens(content)
    if tag == "Code" and isinstance(content, list) and content:
        code = str(content[-1])
        if not code:
            return []
        unbreakable_characters = 1 if long_texttt_source_is_breakable(code) else len(code)
        width = math.ceil(unbreakable_characters * (_BODY_CHARACTERS_PER_LINE_20PT / _LIST_CHARACTERS_PER_LINE_20PT))
        return [(code, width + TABLE_TOKEN_SAFETY_CHARACTERS)]
    if tag == "Math" and isinstance(content, list) and content:
        source = str(content[-1])
        # Supported aligned/substack constructions have explicit ``\\`` row
        # boundaries.  Beamer lays out the widest row, not the concatenation
        # of every row, so price those physical rows separately while the
        # vertical estimator accounts for their total height.
        rows = source.split("\\\\")
        return [(row, tex_math_width_units(row) + TABLE_TOKEN_SAFETY_CHARACTERS) for row in rows if row]
    if tag == "Cite":
        return _ordinary_physical_tokens(_plain_text(value))
    if tag in {"BulletList", "OrderedList", "DefinitionList"}:
        raw_items = content
        if tag == "OrderedList" and isinstance(content, list) and len(content) == 2:
            raw_items = content[1]
        if not isinstance(raw_items, list):
            return []
        tokens = [token for item in raw_items for token in _inline_physical_tokens(item)]
        return [(token, width + TABLE_LIST_INDENT_WIDTH_UNITS) for token, width in tokens]
    if tag in {"Link", "Image", "Quoted"} and isinstance(content, list) and len(content) >= 2:
        return _inline_physical_tokens(content[1])
    if tag in {"Div", "Span"} and isinstance(content, list) and len(content) >= 2:
        return _inline_physical_tokens(content[1])
    if tag in {"RawInline", "RawBlock"} and isinstance(content, list) and content:
        return _ordinary_physical_tokens(str(content[-1]))
    return _inline_physical_tokens(content)


def _widest_indivisible_inline_token(value: object) -> tuple[str, int]:
    return max(_inline_physical_tokens(value), key=lambda item: item[1], default=("", 0))


def _unsupported_math_geometry(value: object) -> tuple[str, tuple[str, ...]] | None:
    if isinstance(value, list):
        return next(
            (finding for item in value if (finding := _unsupported_math_geometry(item)) is not None),
            None,
        )
    if not isinstance(value, dict):
        return None
    content = value.get("c")
    if value.get("t") == "Math" and isinstance(content, list) and content:
        source = str(content[-1])
        unsupported = unsupported_tex_math_commands(source)
        return (source, unsupported) if unsupported else None
    return _unsupported_math_geometry(content)


def _math_vertical_line_demand(value: object) -> tuple[str, int]:
    if isinstance(value, list):
        return max(
            (_math_vertical_line_demand(item) for item in value),
            key=lambda item: item[1],
            default=("", 1),
        )
    if not isinstance(value, dict):
        return "", 1
    content = value.get("c")
    if value.get("t") == "Math" and isinstance(content, list) and content:
        source = str(content[-1])
        return source, tex_math_vertical_line_demand(source)
    return _math_vertical_line_demand(content)


def _validate_math_geometry(value: object, *, source: str, heading: str) -> None:
    unsupported_math = _unsupported_math_geometry(value)
    if unsupported_math is None:
        return
    math_source, unsupported_commands = unsupported_math
    raise density_error(
        "slides.density.unsupported-math-geometry",
        "inline TeX math uses control words without a declared accessible projection geometry",
        source=source,
        heading=heading,
        math_source=math_source,
        unsupported_commands=list(unsupported_commands),
    )


def _cross_reference_identifier_extra_width_units(value: object) -> int:
    if isinstance(value, list):
        return sum(_cross_reference_identifier_extra_width_units(item) for item in value)
    if not isinstance(value, dict):
        return 0
    content = value.get("c")
    if value.get("t") == "Cite" and isinstance(content, list) and content:
        citations = content[0]
        if not isinstance(citations, list):
            return 0
        total = 0
        for citation in citations:
            identifier = citation.get("citationId") if isinstance(citation, dict) else None
            namespace = identifier.partition(":")[0] if isinstance(identifier, str) else ""
            if identifier and namespace in _CROSS_REFERENCE_LABELS:
                monospace_width = math.ceil(
                    len(identifier) * (_BODY_CHARACTERS_PER_LINE_20PT / _LIST_CHARACTERS_PER_LINE_20PT)
                )
                total += max(0, monospace_width - proportional_text_width_units(identifier))
        return total
    return _cross_reference_identifier_extra_width_units(content)


def _estimated_visible_characters(value: object) -> int:
    """Return proportional-width units with a conservative monospace debit."""

    normalized_text = " ".join(_plain_text(value).split())
    visible_width = proportional_text_width_units(normalized_text)
    monospace_extra = _inline_code_extra_width_units(value) + _cross_reference_identifier_extra_width_units(value)
    return visible_width + monospace_extra


def _estimated_proportional_text_lines(value: object, capacity: int) -> int:
    """Pack proportional words into physical lines without pooling slack.

    A total-width ceiling can accept text whose individual words leave unusable
    fragments at several line ends. TeX cannot move that slack between lines,
    so accessible preflight follows the same next-word packing rule. Computing
    each candidate line as one string preserves fractional interword and
    wide-glyph widths instead of accumulating per-token integer ceilings.
    Monospace and cross-reference debits remain a conservative aggregate floor.
    """

    if capacity <= 0:
        return 1
    words = " ".join(_plain_text(value).split()).split()
    if not words:
        return 1
    lines = 1
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if not current or proportional_text_width_units(candidate) <= capacity:
            current.append(word)
            continue
        lines += 1
        current = [word]
        word_width = proportional_text_width_units(word)
        if word_width > capacity:
            # The physical-token guard emits the more specific fail-closed
            # diagnostic. Retain a conservative line debit in case a caller is
            # estimating before that guard runs.
            lines += math.ceil(word_width / capacity) - 1
            current = []
    aggregate_floor = math.ceil(_estimated_visible_characters(value) / capacity)
    return max(lines, aggregate_floor)


def _pandoc_node_count(value: object, target: str) -> int:
    if isinstance(value, list):
        return sum(_pandoc_node_count(item, target) for item in value)
    if not isinstance(value, dict):
        return 0
    return int(value.get("t") == target) + _pandoc_node_count(value.get("c"), target)


def _estimated_lines_with_hard_breaks(value: object, capacity: int) -> int:
    """Estimate wrapped lines while preserving semantic block boundaries."""

    if isinstance(value, list):
        return max(1, sum(_estimated_lines_with_hard_breaks(item, capacity) for item in value))
    if not isinstance(value, dict):
        return 1
    tag = value.get("t")
    content = value.get("c")
    if tag in {"BulletList", "OrderedList"}:
        raw_items = content
        if tag == "OrderedList" and isinstance(content, list) and len(content) == 2:
            raw_items = content[1]
        if not isinstance(raw_items, list):
            return 1
        lines = 0
        for item in raw_items:
            item_lines = _estimated_lines_with_hard_breaks(item, capacity)
            paragraph_count = (
                sum(isinstance(block, dict) and block.get("t") in {"Para", "Plain"} for block in item)
                if isinstance(item, list)
                else 0
            )
            # A loose list item's paragraph separation consumes one additional
            # calibrated line. Compact nested lists retain their existing fit.
            lines += item_lines + int(paragraph_count > 1)
        return max(1, lines)
    if tag == "BlockQuote":
        if not isinstance(content, list):
            return 1
        source_lines = max(
            1,
            sum(_estimated_lines_with_hard_breaks(item, capacity) for item in content),
        )
        return max(1, math.ceil(source_lines * 8 / 9))
    if tag == "Div":
        # Pandoc containers preserve their child block boundaries.  Flattening
        # ten one-line paragraphs into one wrapping string substantially
        # underprices the vertical space that Beamer assigns to the paragraph
        # breaks.  Count every child and one conservative inter-block line.
        if not isinstance(content, list) or len(content) < 2 or not isinstance(content[1], list):
            return 1
        child_blocks = content[1]
        child_lines = sum(_estimated_lines_with_hard_breaks(item, capacity) for item in child_blocks)
        return max(1, child_lines + max(0, len(child_blocks) - 1))
    if tag == "DefinitionList":
        if not isinstance(content, list):
            return 1
        # Multiple description items need one shared environment debit. A
        # single term shares its first projected line with its first definition.
        lines = int(len(content) > 1)
        for item in content:
            if not isinstance(item, list) or len(item) != 2:
                return lines + 1
            term, definitions = item
            term_lines = _estimated_proportional_text_lines({"t": "Plain", "c": term}, capacity)
            definition_lines = _estimated_lines_with_hard_breaks(definitions, capacity)
            lines += max(1, term_lines, definition_lines)
        return max(1, lines)
    if tag in {"Para", "Plain"} and isinstance(content, list):
        segments: list[list[Any]] = [[]]
        for inline in content:
            if isinstance(inline, dict) and inline.get("t") == "LineBreak":
                segments.append([])
            else:
                segments[-1].append(inline)
        direct_lines = sum(
            _estimated_proportional_text_lines({"t": tag, "c": segment}, capacity) for segment in segments
        )
        _math_source, math_lines = _math_vertical_line_demand(value)
        return max(direct_lines, _pandoc_node_count(value, "LineBreak") + 1, math_lines)
    base_lines = _estimated_proportional_text_lines(value, capacity)
    _math_source, math_lines = _math_vertical_line_demand(value)
    return max(base_lines, _pandoc_node_count(value, "LineBreak") + 1, math_lines)


def _block_contains(block: object, target: str) -> bool:
    """Return whether a Pandoc node tree contains ``target``."""

    if isinstance(block, list):
        return any(_block_contains(item, target) for item in block)
    if not isinstance(block, dict):
        return False
    return block.get("t") == target or _block_contains(block.get("c"), target)


__all__: list[str] = []
