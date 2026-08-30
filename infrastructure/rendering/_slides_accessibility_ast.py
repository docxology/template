"""Pandoc-AST text, block, and figure geometry for accessible slides."""

from __future__ import annotations

import copy
import math
import re
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import (
    BASE_BODY_LINES_16_9,
    BODY_CHARACTERS_PER_LINE_20PT,
    BODY_LINES_PER_EXTRA_TITLE_LINE,
    CLAUSE_COORDINATORS,
    CONTINUATION_TITLE_TARGET_CHARS,
    CROSS_REFERENCE_LABELS,
    LIST_CHARACTERS_PER_LINE_20PT,
    SEMANTIC_BREAK_SUFFIXES,
    TITLE_CHARACTERS_PER_LINE_28PT,
    AccessibleSlidePolicy,
    density_error,
)


_WORD_RE = re.compile(r"[\w]+(?:[-'][\w]+)*", flags=re.UNICODE)
_PRESENTATION_PAGE_BREAK_RE = re.compile(r"^\\(?:clearpage|newpage|pagebreak)\s*$")
_EQUATION_LABEL_RE = re.compile(r"^\{#(?:eq|def|prop|lem|thm):[^{}]+\}$")
_SHELL_CODE_CLASSES = frozenset(
    {
        "bash",
        "console",
        "sh",
        "shell",
        "shell-session",
        "terminal",
        "zsh",
    }
)
_BASE_BODY_LINES_16_9 = BASE_BODY_LINES_16_9
_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_LIST_CHARACTERS_PER_LINE_20PT = LIST_CHARACTERS_PER_LINE_20PT
_TITLE_CHARACTERS_PER_LINE_28PT = TITLE_CHARACTERS_PER_LINE_28PT
_BODY_LINES_PER_EXTRA_TITLE_LINE = BODY_LINES_PER_EXTRA_TITLE_LINE
_CONTINUATION_TITLE_TARGET_CHARS = CONTINUATION_TITLE_TARGET_CHARS
_SEMANTIC_BREAK_SUFFIXES = SEMANTIC_BREAK_SUFFIXES
_CROSS_REFERENCE_LABELS = CROSS_REFERENCE_LABELS
_CLAUSE_COORDINATORS = CLAUSE_COORDINATORS
_density_error = density_error


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
        rendered: list[str] = []
        if isinstance(citations, list):
            for citation in citations:
                identifier = citation.get("citationId") if isinstance(citation, dict) else None
                namespace = identifier.partition(":")[0] if isinstance(identifier, str) else ""
                label = _CROSS_REFERENCE_LABELS.get(namespace)
                if label is not None and identifier:
                    # A per-section deck may not yet have the combined-PDF AUX
                    # map during its first pass.  The later cross-deck transform
                    # then renders the complete source identifier as a visible
                    # monospace fallback (for example,
                    # ``sec. sec:results-hierarchical``).  Size that known
                    # fallback here; treating it as an author-year citation can
                    # make a composition that passed preflight overflow Beamer.
                    rendered.append(f"{label} {identifier}")
                else:
                    # A stable author-year placeholder per bibliographic item
                    # is conservative without depending on a particular CSL
                    # style or exposing the usually longer source identifier.
                    rendered.append("(Author, 0000)")
        return " ".join(rendered or ["(Author, 0000)"])
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


def _inline_code_character_count(value: object) -> int:
    """Count visible monospace characters inside a Pandoc fragment."""

    if isinstance(value, list):
        return sum(_inline_code_character_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    content = value.get("c")
    if value.get("t") == "Code" and isinstance(content, list) and content:
        return len(str(content[-1]))
    return _inline_code_character_count(content)


def _cross_reference_identifier_character_count(value: object) -> int:
    """Count identifiers that a first-pass section deck renders monospace."""

    if isinstance(value, list):
        return sum(_cross_reference_identifier_character_count(item) for item in value)
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
                total += len(identifier)
        return total
    return _cross_reference_identifier_character_count(content)


def _estimated_visible_characters(value: object) -> int:
    """Return proportional-width units with a conservative monospace debit."""

    visible = _normalized_text_length(value)
    monospace_characters = _inline_code_character_count(value) + _cross_reference_identifier_character_count(value)
    # At the 20-point floor, the projected monospace face fits about 34
    # characters where the sans-serif body fits 43. Preserve inline code as an
    # atomic Pandoc node.  Apply the same debit to source-known cross-reference
    # identifiers because the first-pass section fallback also renders them in
    # monospace before a combined-PDF AUX map exists.
    monospace_extra = math.ceil(
        monospace_characters * (_BODY_CHARACTERS_PER_LINE_20PT / _LIST_CHARACTERS_PER_LINE_20PT - 1)
    )
    return visible + monospace_extra


def _compact_continuation_title(title: str, continuation: int) -> str:
    """Return a bounded visible title while retaining the full first-frame title."""

    suffix = f" (part {continuation})"
    visible_budget = max(12, _CONTINUATION_TITLE_TARGET_CHARS - len(suffix))
    compact = title
    punctuation_prefix = re.split(r":|\s+[—–]\s+", title, maxsplit=1)[0].strip()
    if punctuation_prefix != title and 12 <= len(punctuation_prefix) <= visible_budget:
        compact = punctuation_prefix
    elif len(title) > visible_budget:
        words: list[str] = []
        for word in title.split():
            candidate = " ".join([*words, word])
            if words and len(candidate) > visible_budget - 1:
                break
            words.append(word)
        compact = " ".join(words).rstrip(".,;:") + "…"
    if len(compact) > visible_budget:
        # A long identifier or URL may not contain a semantic word boundary.
        # Keep the visible title inside the same one-line contract even in that
        # case; the complete authored heading remains the frame's aria-label.
        compact = compact[: max(1, visible_budget - 1)].rstrip(".,;: ") + "…"
    return compact + suffix


def _text_inlines(text: str) -> list[dict[str, Any]]:
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(text.split()):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return inlines


def _continuation_title_text(header: dict[str, Any], continuation: int) -> str:
    title = _header_text(header)
    return title if continuation == 1 else _compact_continuation_title(title, continuation)


def _frame_body_line_capacity(
    header: dict[str, Any],
    continuation: int,
    policy: AccessibleSlidePolicy,
) -> int:
    """Estimate safe body lines after the fixed title and footer regions."""

    title_chars_per_line = max(
        1,
        math.floor(_TITLE_CHARACTERS_PER_LINE_28PT * 28 / policy.title_font_pt),
    )
    title_lines = max(
        1,
        math.ceil(_normalized_text_length(_continuation_title_text(header, continuation)) / title_chars_per_line),
    )
    body_lines = math.floor(_BASE_BODY_LINES_16_9 * 20 / policy.body_font_pt)
    return max(1, body_lines - (title_lines - 1) * _BODY_LINES_PER_EXTRA_TITLE_LINE)


def _estimated_block_lines(block: dict[str, Any], policy: AccessibleSlidePolicy) -> int:
    """Estimate wrapped body lines without splitting a semantic block."""

    tag = block.get("t")
    body_chars_per_line = max(
        1,
        math.floor(_BODY_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt),
    )
    if tag in {"BulletList", "OrderedList"}:
        raw_items = block.get("c")
        if tag == "OrderedList" and isinstance(raw_items, list) and len(raw_items) == 2:
            raw_items = raw_items[1]
        if not isinstance(raw_items, list):
            return 1
        list_chars_per_line = max(
            1,
            math.floor(_LIST_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt),
        )
        return sum(max(1, math.ceil(_estimated_visible_characters(item) / list_chars_per_line)) for item in raw_items)
    return max(1, math.ceil(_estimated_visible_characters(block) / body_chars_per_line))


def _code_block_parts(block: dict[str, Any]) -> tuple[list[Any], str, str]:
    """Return validated attributes, source text, and the primary language."""

    content = block.get("c")
    if block.get("t") != "CodeBlock" or not isinstance(content, list) or len(content) != 2:
        raise RenderingError("Accessible slide composition received a malformed Pandoc CodeBlock")
    attributes, source_text = content
    if (
        not isinstance(attributes, list)
        or len(attributes) != 3
        or not isinstance(attributes[1], list)
        or not isinstance(source_text, str)
    ):
        raise RenderingError("Accessible slide composition received a malformed Pandoc CodeBlock")
    classes = [str(value).casefold() for value in attributes[1]]
    language = next((value for value in classes if value), "plain")
    return attributes, source_text, language


def _shell_code_inlines(source_text: str) -> list[dict[str, Any]]:
    """Represent shell tokens as breakable inline code with visible spacing.

    Pandoc's fenced ``CodeBlock`` becomes a FancyVerb environment, whose
    physical lines cannot wrap.  Inline ``Code`` tokens keep monospace text
    while permitting line breaks at source whitespace; the existing Beamer
    ``breaktt`` pass adds character-level opportunities inside long paths.
    Logical source lines remain explicit ``LineBreak`` nodes.
    """

    inlines: list[dict[str, Any]] = []
    logical_lines = source_text.splitlines() or [""]
    for line_index, line in enumerate(logical_lines):
        if line_index:
            inlines.append({"t": "LineBreak"})
        for token in re.split(r"(\s+)", line.expandtabs(4)):
            if not token:
                continue
            if token.isspace():
                # A normal Pandoc Space provides the legal line-break point.
                # Preserve any additional source indentation in a short
                # monospace span; leading whitespace has no preceding point
                # at which TeX could break and therefore stays together.
                at_line_start = not inlines or inlines[-1].get("t") == "LineBreak"
                if not at_line_start:
                    inlines.append({"t": "Space"})
                    token = token[1:]
                if not token:
                    continue
            inlines.append({"t": "Code", "c": [["", ["accessible-shell-token"], []], token]})
    return inlines


def _prepare_code_block_for_frame(
    block: dict[str, Any],
    *,
    policy: AccessibleSlidePolicy,
    maximum_lines: int,
    source: str,
    heading: str,
) -> dict[str, Any]:
    """Preflight one atomic code block and safely reflow long shell commands.

    The accessible profile keeps code blocks atomic.  A long shell command is
    safe to wrap at whitespace and inside long path tokens, so it is converted
    to inline monospace tokens.  Other languages can be whitespace-sensitive;
    an over-wide physical line therefore fails closed with a stable diagnostic
    instead of being clipped or silently typeset below the font floor.
    """

    _attributes, source_text, language = _code_block_parts(block)
    code_chars_per_line = max(
        1,
        math.floor(_LIST_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt),
    )
    logical_lines = source_text.splitlines() or [""]
    expanded_lengths = [len(line.expandtabs(4)) for line in logical_lines]
    overwide_lines = [
        (index, length) for index, length in enumerate(expanded_lengths, start=1) if length > code_chars_per_line
    ]
    classes = {str(value).casefold() for value in block["c"][0][1] if isinstance(value, str)}
    is_shell = bool(classes & _SHELL_CODE_CLASSES)
    if overwide_lines and not is_shell:
        line_number, observed_characters = overwide_lines[0]
        raise _density_error(
            "slides.density.indivisible-code-line",
            "one whitespace-sensitive code line cannot fit the projection frame at the declared font floor",
            source=source,
            heading=heading,
            language=language,
            line_number=line_number,
            observed_characters=observed_characters,
            maximum_characters=code_chars_per_line,
        )

    estimated_lines = sum(max(1, math.ceil(max(1, length) / code_chars_per_line)) for length in expanded_lengths)
    if estimated_lines > maximum_lines:
        raise _density_error(
            "slides.density.indivisible-code",
            "one atomic code block cannot fit the projection frame at the declared font floor",
            source=source,
            heading=heading,
            language=language,
            source_line_count=len(logical_lines),
            estimated_lines=estimated_lines,
            maximum_lines=maximum_lines,
        )

    if not overwide_lines:
        return copy.deepcopy(block)
    return {"t": "Para", "c": _shell_code_inlines(source_text)}


def _trim_inline_spaces(inlines: list[Any]) -> list[Any]:
    """Drop boundary whitespace while preserving every semantic inline."""

    start = 0
    end = len(inlines)
    while (
        start < end
        and isinstance(inlines[start], dict)
        and inlines[start].get("t")
        in {
            "Space",
            "SoftBreak",
            "LineBreak",
        }
    ):
        start += 1
    while (
        end > start
        and isinstance(inlines[end - 1], dict)
        and inlines[end - 1].get("t")
        in {
            "Space",
            "SoftBreak",
            "LineBreak",
        }
    ):
        end -= 1
    return copy.deepcopy(inlines[start:end])


def _next_visible_str(inlines: list[Any], start: int) -> str | None:
    for inline in inlines[start:]:
        if not isinstance(inline, dict):
            continue
        if inline.get("t") in {"Space", "SoftBreak", "LineBreak"}:
            continue
        content = inline.get("c")
        if inline.get("t") == "Str" and isinstance(content, str):
            return content
        return None
    return None


def _is_semantic_inline_break(inlines: list[Any], index: int) -> bool:
    """Return whether an inline ends a sentence or strong written clause."""

    inline = inlines[index]
    if not isinstance(inline, dict) or inline.get("t") != "Str":
        return False
    content = inline.get("c")
    if not isinstance(content, str):
        return False
    stripped = content.rstrip()
    if stripped.endswith(_SEMANTIC_BREAK_SUFFIXES):
        return True
    # A comma is a written prosodic boundary and is therefore a permissible
    # last-resort split when a complete sentence cannot fit.  This never cuts
    # inside a Pandoc inline node.
    if stripped.endswith(","):
        return True
    return False


def _prose_block_slice(block: dict[str, Any], inlines: list[Any]) -> dict[str, Any]:
    updated = copy.deepcopy(block)
    updated["c"] = _trim_inline_spaces(inlines)
    return updated


def _split_prose_block_to_fit(
    block: dict[str, Any],
    *,
    policy: AccessibleSlidePolicy,
    maximum_lines: int,
    source: str,
    heading: str,
) -> list[dict[str, Any]]:
    """Split a paragraph only at sentence or strong-clause boundaries.

    Lists, code, equations, figures, and tables never enter this helper.  A
    paragraph with no safe written boundary fails closed instead of being cut
    by character count or rendered with smaller type.
    """

    words = _word_count(block)
    lines = _estimated_block_lines(block, policy)
    if words <= policy.max_prose_words and lines <= maximum_lines:
        return [copy.deepcopy(block)]
    tag = block.get("t")
    if tag not in {"Para", "Plain"} or not isinstance(block.get("c"), list):
        # Lists and raw theorem-like environments remain indivisible. Reject
        # an oversized one before TeX instead of splitting inside its semantic
        # structure or silently shrinking the profile's typography.
        requires_line_preflight = tag in {"BulletList", "OrderedList"}
        if words <= policy.max_prose_words and (not requires_line_preflight or lines <= maximum_lines):
            return [copy.deepcopy(block)]
        if tag in {"BulletList", "OrderedList"}:
            code = "slides.density.indivisible-list"
            noun = "list"
        elif tag == "RawBlock":
            code = "slides.density.indivisible-raw-block"
            noun = "raw theorem-like block"
        else:
            code = "slides.density.indivisible-prose"
            noun = "semantic prose block"
        raise _density_error(
            code,
            f"one {noun} cannot fit the projection frame without splitting inside its structure",
            source=source,
            heading=heading,
            block_type=str(tag),
            observed_words=words,
            maximum_words=policy.max_prose_words,
            estimated_lines=lines,
            maximum_lines=maximum_lines,
        )

    inlines = block["c"]
    segments: list[dict[str, Any]] = []
    start = 0
    while start < len(inlines):
        remainder = _prose_block_slice(block, inlines[start:])
        if (
            _word_count(remainder) <= policy.max_prose_words
            and _estimated_block_lines(remainder, policy) <= maximum_lines
        ):
            segments.append(remainder)
            break

        candidates: list[int] = []
        coordinator_candidates: list[int] = []
        for index in range(start, len(inlines)):
            written_boundary = _is_semantic_inline_break(inlines, index)
            next_word = _next_visible_str(inlines, index + 1)
            coordinator_boundary = (
                isinstance(inlines[index], dict)
                and inlines[index].get("t") == "Str"
                and next_word is not None
                and next_word.casefold().strip("'\"") in _CLAUSE_COORDINATORS
            )
            if not written_boundary and not coordinator_boundary:
                continue
            candidate = _prose_block_slice(block, inlines[start : index + 1])
            if (
                _word_count(candidate) <= policy.max_prose_words
                and _estimated_block_lines(candidate, policy) <= maximum_lines
            ):
                target = candidates if written_boundary else coordinator_candidates
                target.append(index + 1)
        usable_candidates = candidates or coordinator_candidates
        if not usable_candidates:
            raise _density_error(
                "slides.density.indivisible-prose",
                "one prose sentence or strong clause cannot fit the projection frame at the declared font floor",
                source=source,
                heading=heading,
                observed_words=_word_count(remainder),
                maximum_words=policy.max_prose_words,
                estimated_lines=_estimated_block_lines(remainder, policy),
                maximum_lines=maximum_lines,
                text_excerpt=" ".join(_plain_text(remainder).split())[:240],
            )
        cut = usable_candidates[-1]
        segments.append(_prose_block_slice(block, inlines[start:cut]))
        start = cut

    return [segment for segment in segments if segment.get("c")]


def _header_parts(block: dict[str, Any]) -> tuple[int, list[Any], list[dict[str, Any]]]:
    content = block.get("c")
    if block.get("t") != "Header" or not isinstance(content, list) or len(content) != 3:
        raise RenderingError("Accessible slide composition received a malformed Pandoc Header")
    level, attributes, inlines = content
    if not isinstance(level, int) or not isinstance(attributes, list) or not isinstance(inlines, list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Header")
    return level, attributes, inlines


def _header_text(block: dict[str, Any]) -> str:
    return " ".join(_plain_text(_header_parts(block)[2]).split()) or "Untitled slide"


def _header_with(
    source: dict[str, Any],
    *,
    level: int,
    continuation: int = 1,
    frame_kind: str | None = None,
    section_divider: bool = False,
) -> dict[str, Any]:
    """Return a frame-producing header without duplicating source identifiers."""

    _old_level, attributes, inlines = _header_parts(source)
    identifier = attributes[0] if continuation == 1 else ""
    classes = [str(value) for value in attributes[1]] if len(attributes) > 1 else []
    key_values = copy.deepcopy(attributes[2]) if len(attributes) > 2 else []
    if frame_kind and frame_kind not in classes:
        classes.append(frame_kind)
    if section_divider and "section-divider" not in classes:
        classes.append("section-divider")
    rendered_inlines = copy.deepcopy(inlines)
    if continuation > 1:
        full_title = " ".join(_plain_text(inlines).split()) or "Untitled slide"
        rendered_inlines = _text_inlines(_compact_continuation_title(full_title, continuation))
        key_values = [
            pair
            for pair in key_values
            if not (isinstance(pair, list) and pair and str(pair[0]).casefold() == "aria-label")
        ]
        key_values.append(["aria-label", f"{full_title}, part {continuation}"])
    return {"t": "Header", "c": [level, [identifier, classes, key_values], rendered_inlines]}


def _generated_header(title: str) -> dict[str, Any]:
    return {"t": "Header", "c": [2, ["", ["generated-slide-title"], []], _text_inlines(title)]}


def _block_contains(block: object, target: str) -> bool:
    if isinstance(block, dict):
        if block.get("t") == target:
            return True
        return _block_contains(block.get("c"), target)
    if isinstance(block, list):
        return any(_block_contains(item, target) for item in block)
    return False


def _is_presentation_page_break(block: dict[str, Any]) -> bool:
    """Return whether a raw pagination command has no slide content."""

    if block.get("t") != "RawBlock":
        return False
    content = block.get("c")
    return (
        isinstance(content, list)
        and len(content) == 2
        and str(content[0]).casefold() in {"latex", "tex"}
        and isinstance(content[1], str)
        and _PRESENTATION_PAGE_BREAK_RE.fullmatch(content[1].strip()) is not None
    )


def _is_display_equation_paragraph(block: dict[str, Any]) -> bool:
    """Recognize display math with an optional source-owned crossref suffix."""

    if block.get("t") not in {"Para", "Plain"} or not isinstance(block.get("c"), list):
        return False
    saw_display_math = False
    for inline in block["c"]:
        if not isinstance(inline, dict):
            return False
        tag = inline.get("t")
        if tag in {"Space", "SoftBreak", "LineBreak"}:
            continue
        if tag == "Math":
            content = inline.get("c")
            if (
                not isinstance(content, list)
                or len(content) != 2
                or not isinstance(content[0], dict)
                or content[0].get("t") != "DisplayMath"
            ):
                return False
            saw_display_math = True
            continue
        if tag == "Str" and isinstance(inline.get("c"), str) and _EQUATION_LABEL_RE.fullmatch(inline["c"]):
            continue
        return False
    return saw_display_math


def _block_kind(block: dict[str, Any]) -> str:
    tag = block.get("t")
    if tag == "Figure" or _block_contains(block, "Image"):
        return "figure-led"
    if tag == "Table":
        return "table-led"
    if tag in {"CodeBlock"}:
        return "code-led"
    if tag == "BlockQuote":
        return "evidence-slide"
    if tag == "Div":
        content = block.get("c")
        if isinstance(content, list) and content and isinstance(content[0], list):
            classes = content[0][1] if len(content[0]) > 1 else []
            if any(str(value) in {"evidence", "claim", "finding"} for value in classes):
                return "evidence-slide"
    if _is_display_equation_paragraph(block):
        return "equation-led"
    if tag == "RawBlock" and re.search(
        r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}|^\s*\$\$",
        _plain_text(block),
    ):
        return "equation-led"
    return "prose-slide"


def _reader_link_block(policy: AccessibleSlidePolicy, noun: str) -> dict[str, Any]:
    label = f"Open the canonical HTML manuscript for the complete {noun}."
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(label.split()):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return {
        "t": "Para",
        "c": [
            {
                "t": "Link",
                "c": [["", ["slide-reader-link"], []], inlines, [policy.reader_href, "Canonical HTML manuscript"]],
            }
        ],
    }


def _image_nodes(value: object) -> list[dict[str, Any]]:
    """Return image nodes in source order without descending into image alt text."""

    if isinstance(value, list):
        return [image for item in value for image in _image_nodes(item)]
    if not isinstance(value, dict):
        return []
    if value.get("t") == "Image":
        return [value]
    return _image_nodes(value.get("c"))


def _is_projection_image_only(value: object) -> bool:
    """Return whether a non-Figure block contains images but no visible peer content."""

    if isinstance(value, list):
        return all(_is_projection_image_only(item) for item in value)
    if not isinstance(value, dict):
        return not str(value).strip()
    tag = value.get("t")
    if tag == "Image":
        return True
    if tag in {"Space", "SoftBreak", "LineBreak"}:
        return True
    if tag in {"Para", "Plain"}:
        return _is_projection_image_only(value.get("c"))
    if tag in {"Link", "Span", "Div"}:
        content = value.get("c")
        return isinstance(content, list) and len(content) >= 2 and _is_projection_image_only(content[1])
    return False


def _image_width_percent(image: dict[str, Any]) -> float | None:
    """Return one explicit percentage width from a validated Pandoc Image."""

    content = image.get("c")
    if not isinstance(content, list) or len(content) != 3 or not isinstance(content[0], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Image")
    attributes = content[0]
    if len(attributes) != 3 or not isinstance(attributes[2], list):
        raise RenderingError("Accessible slide composition received malformed Pandoc Image attributes")
    for pair in attributes[2]:
        if not isinstance(pair, list) or len(pair) != 2 or pair[0] != "width":
            continue
        match = re.fullmatch(r"(?P<value>\d+(?:\.\d+)?)%", str(pair[1]).strip())
        if match is None:
            return None
        value = float(match.group("value"))
        return value if math.isfinite(value) and value > 0 else None
    return None


def _validate_projection_image_row(
    value: object,
    *,
    source: str,
    heading: str,
) -> None:
    """Require multi-panel figures to be one explicit, bounded image row."""

    images = _image_nodes(value)
    if len(images) <= 1:
        return
    row_block: object | None = None
    if isinstance(value, list) and len(value) == 1:
        row_block = value[0]
    elif isinstance(value, dict):
        row_block = value
    if (
        not isinstance(row_block, dict)
        or row_block.get("t") not in {"Para", "Plain"}
        or not _is_projection_image_only(row_block)
    ):
        raise density_error(
            "slides.density.multi-image-layout",
            "multiple images must form one explicit projection row",
            source=source,
            heading=heading,
            image_count=len(images),
        )
    widths = [_image_width_percent(image) for image in images]
    if any(width is None for width in widths) or sum(width for width in widths if width is not None) > 96:
        raise density_error(
            "slides.density.multi-image-layout",
            "a multi-image row requires explicit percentage widths totaling at most 96 percent",
            source=source,
            heading=heading,
            image_count=len(images),
            authored_widths=widths,
            maximum_total_width_percent=96,
        )


def _allocate_figure_area(value: object, image_height_percent: int) -> None:
    """Reserve figure area while retaining space for its accessible label.

    Accessible projection owns the full available frame width. The image
    envelope takes the configured share of the title-adjusted body; preserved
    aspect ratio may leave whitespace inside that envelope. Persistent frame
    navigation supplies the 16-point reader link, and the full caption remains
    in the linked HTML reader.
    """

    images = _image_nodes(value)
    image_count = len(images)
    if not image_count:
        raise RenderingError("Accessible figure frame does not contain a Pandoc Image")

    for image in images:
        content = image.get("c")
        if not isinstance(content, list) or len(content) != 3 or not isinstance(content[0], list):
            raise RenderingError("Accessible slide composition received a malformed Pandoc Image")
        attributes = content[0]
        if len(attributes) != 3 or not isinstance(attributes[2], list):
            raise RenderingError("Accessible slide composition received malformed Pandoc Image attributes")
        authored_width = next(
            (pair for pair in attributes[2] if isinstance(pair, list) and len(pair) == 2 and pair[0] == "width"),
            None,
        )
        key_values = [
            pair
            for pair in attributes[2]
            if not (
                isinstance(pair, list) and pair and (pair[0] == "height" or (pair[0] == "width" and image_count == 1))
            )
        ]
        # A two-percent TeX safety inset prevents a nominal full-width image
        # from acquiring an overfull hbox through figure-environment glue.
        # The projected figure region still owns the complete usable frame;
        # the inset is a keyline margin rather than space for other content.
        if image_count == 1:
            key_values.append(["width", "98%"])
        elif authored_width is None:
            raise RenderingError("Accessible multi-image projection reached allocation without an explicit width")
        key_values.append(["height", f"{image_height_percent}%"])
        attributes[2] = key_values


def _shorten_figure_caption(
    block: dict[str, Any],
    _policy: AccessibleSlidePolicy,
    *,
    image_height_percent: int,
    source: str,
    heading: str,
) -> dict[str, Any]:
    updated = copy.deepcopy(block)
    if updated.get("t") != "Figure":
        if not _is_projection_image_only(updated):
            raise density_error(
                "slides.density.mixed-image-frame",
                "an image and peer prose cannot share one accessible projection frame",
                source=source,
                heading=heading,
            )
        _validate_projection_image_row(updated, source=source, heading=heading)
        _allocate_figure_area(updated, image_height_percent)
        return updated
    content = updated.get("c")
    if not isinstance(content, list) or len(content) != 3:
        raise RenderingError("Accessible slide composition received a malformed Pandoc Figure")
    if not _is_projection_image_only(content[2]):
        raise density_error(
            "slides.density.mixed-image-frame",
            "an image and peer prose cannot share one accessible projection frame",
            source=source,
            heading=heading,
        )
    _validate_projection_image_row(content[2], source=source, heading=heading)
    _allocate_figure_area(content[2], image_height_percent)
    # The accessible Beamer footer and Reveal companion navigation already
    # link the canonical HTML reader at the required label floor. Repeating a
    # long caption-shaped link inside every figure would take space away from
    # the declared 70% figure region. Keep the projected caption empty; the
    # canonical reader retains the complete caption, long description, and
    # exact-value fallback through the source-owned figure registry.
    content[1] = [None, []]
    return updated
