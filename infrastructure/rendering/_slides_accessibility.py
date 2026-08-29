"""Semantic composition and accessibility post-processing for slide decks.

The default ``archive`` slide profile deliberately retains the historical
Pandoc/Beamer path.  The opt-in ``accessible`` profile uses Pandoc's JSON AST
as a format-neutral boundary: both Beamer and Reveal.js consume the same
semantically grouped frames, and no renderer has to guess where a Markdown
paragraph, list, table, equation, code block, or figure ends.

This module does not compute manuscript results or rewrite the canonical
reader.  It composes a presentation derivative and links dense captions and
complete tables back to the HTML manuscript.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import (
    enhance_accessibility,
    normalize_figure_paths,
    write_if_changed,
)


_WORD_RE = re.compile(r"[\w]+(?:[-'][\w]+)*", flags=re.UNICODE)
_SLIDE_OPEN_RE = re.compile(
    r"(?P<open><section\b(?P<attrs>[^>]*)>)(?P<spacing>\s*)"
    r"(?P<heading><h(?P<level>[1-6])\b(?P<heading_attrs>[^>]*)>.*?</h(?P=level)>)",
    flags=re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class AccessibleSlidePolicy:
    """Fail-closed density and typography policy for presentation derivatives."""

    max_prose_words: int = 80
    max_table_rows: int = 8
    min_figure_area_percent: int = 70
    title_font_pt: int = 28
    body_font_pt: int = 20
    figure_label_font_pt: int = 16
    reader_href: str = "../web/index.html"


@dataclass(frozen=True)
class AccessibleSlideComposition:
    """One deterministic AST composition result and its review counts."""

    document: dict[str, Any]
    frame_count: int
    section_divider_count: int
    excerpted_table_count: int
    figure_frame_count: int


@dataclass(frozen=True)
class _Frame:
    title: dict[str, Any]
    blocks: tuple[dict[str, Any], ...]
    kind: str
    continuation: int


def _density_error(
    code: str,
    message: str,
    *,
    source: str,
    heading: str,
    **context: object,
) -> RenderingError:
    """Return one actionable, stable accessible-slide density diagnostic."""

    return RenderingError(
        f"[{code}] {message}",
        context={"source": source, "heading": heading, "diagnostic_code": code, **context},
        suggestions=[
            "Add a semantic subheading or split the indivisible source block.",
            "Keep the complete material in the canonical HTML manuscript and present a bounded excerpt.",
        ],
    )


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
    if tag in {"Code", "Math"} and isinstance(content, list) and content:
        return str(content[-1])
    return _plain_text(content)


def _word_count(block: dict[str, Any]) -> int:
    """Count visible prose words without treating markup as content."""

    return len(_WORD_RE.findall(_plain_text(block)))


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
        rendered_inlines.extend(
            [
                {"t": "Space"},
                {"t": "Str", "c": f"(continued {continuation})"},
            ]
        )
    return {"t": "Header", "c": [level, [identifier, classes, key_values], rendered_inlines]}


def _generated_header(title: str) -> dict[str, Any]:
    words = title.split()
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(words):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return {"t": "Header", "c": [2, ["", ["generated-slide-title"], []], inlines]}


def _block_contains(block: object, target: str) -> bool:
    if isinstance(block, dict):
        if block.get("t") == target:
            return True
        return _block_contains(block.get("c"), target)
    if isinstance(block, list):
        return any(_block_contains(item, target) for item in block)
    return False


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
    if tag in {"Para", "Plain"} and _block_contains(block, "Math"):
        content = block.get("c")
        if isinstance(content, list) and all(
            isinstance(item, dict) and item.get("t") in {"Math", "Space", "SoftBreak", "LineBreak"} for item in content
        ):
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


def _allocate_figure_area(value: object, policy: AccessibleSlidePolicy) -> None:
    """Reserve figure area while retaining space for its accessible label.

    The surrounding ``Figure`` block is the measured allocation. Ten
    percentage points are reserved for the 16-point companion-reader label;
    the image occupies the remainder. This keeps the complete figure region at
    the configured floor without producing an overfull Beamer frame.
    """

    if isinstance(value, list):
        for item in value:
            _allocate_figure_area(item, policy)
        return
    if not isinstance(value, dict):
        return
    if value.get("t") == "Image":
        content = value.get("c")
        if not isinstance(content, list) or len(content) != 3 or not isinstance(content[0], list):
            raise RenderingError("Accessible slide composition received a malformed Pandoc Image")
        attributes = content[0]
        if len(attributes) != 3 or not isinstance(attributes[2], list):
            raise RenderingError("Accessible slide composition received malformed Pandoc Image attributes")
        key_values = [pair for pair in attributes[2] if not (isinstance(pair, list) and pair and pair[0] == "height")]
        image_height_percent = max(1, policy.min_figure_area_percent - 10)
        key_values.append(["height", f"{image_height_percent}%"])
        attributes[2] = key_values
    _allocate_figure_area(value.get("c"), policy)


def _shorten_figure_caption(block: dict[str, Any], policy: AccessibleSlidePolicy) -> dict[str, Any]:
    updated = copy.deepcopy(block)
    if updated.get("t") != "Figure":
        return updated
    content = updated.get("c")
    if not isinstance(content, list) or len(content) != 3:
        raise RenderingError("Accessible slide composition received a malformed Pandoc Figure")
    _allocate_figure_area(updated, policy)
    reader_link = _reader_link_block(policy, "caption, long description, and exact values")
    content[1] = [None, [{"t": "Plain", "c": reader_link["c"]}]]
    return updated


def _table_row_count(block: dict[str, Any]) -> int:
    content = block.get("c")
    if not isinstance(content, list) or len(content) < 5 or not isinstance(content[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table")
    total = 0
    for body in content[4]:
        if isinstance(body, list) and len(body) >= 4 and isinstance(body[3], list):
            total += len(body[3])
    return total


def _excerpt_table(block: dict[str, Any], policy: AccessibleSlidePolicy) -> tuple[dict[str, Any], bool]:
    """Keep at most the configured number of body rows across Pandoc table bodies."""

    updated = copy.deepcopy(block)
    content = updated.get("c")
    if not isinstance(content, list) or len(content) < 5 or not isinstance(content[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table")
    remaining = policy.max_table_rows
    excerpted = False
    for body in content[4]:
        if not isinstance(body, list) or len(body) < 4 or not isinstance(body[3], list):
            raise RenderingError("Accessible slide composition received a malformed Pandoc Table body")
        rows = body[3]
        keep = min(remaining, len(rows))
        if keep < len(rows):
            excerpted = True
        body[3] = rows[:keep]
        remaining -= keep
        if remaining < 0:  # Defensive; ``keep`` cannot make this negative.
            remaining = 0
    if _table_row_count(block) > policy.max_table_rows:
        excerpted = True
    # The full source caption belongs to the canonical reader.  Keeping a short
    # reader link prevents a multi-sentence caption from consuming a projected
    # frame while preserving the table identifier and cross-reference target.
    content[1] = [None, [{"t": "Plain", "c": _reader_link_block(policy, "table and caption")["c"]}]]
    return updated, excerpted


def _flush_prose_frames(
    frames: list[_Frame],
    title: dict[str, Any],
    pending: list[dict[str, Any]],
    *,
    continuation: int,
) -> int:
    if not pending:
        return continuation
    frames.append(_Frame(title=title, blocks=tuple(pending), kind="prose-slide", continuation=continuation))
    pending.clear()
    return continuation + 1


def _compose_segment(
    header: dict[str, Any],
    blocks: list[dict[str, Any]],
    *,
    policy: AccessibleSlidePolicy,
    source: str,
) -> tuple[list[_Frame], int]:
    frames: list[_Frame] = []
    pending: list[dict[str, Any]] = []
    pending_words = 0
    continuation = 1
    excerpted_tables = 0
    heading = _header_text(header)

    for block in blocks:
        if block.get("t") == "HorizontalRule":
            continuation = _flush_prose_frames(
                frames,
                header,
                pending,
                continuation=continuation,
            )
            pending_words = 0
            continue

        kind = _block_kind(block)
        words = _word_count(block)
        if kind == "prose-slide":
            if words > policy.max_prose_words:
                raise _density_error(
                    "slides.density.indivisible-prose",
                    f"one semantic prose block contains {words} words; the maximum is {policy.max_prose_words}",
                    source=source,
                    heading=heading,
                    observed_words=words,
                    maximum_words=policy.max_prose_words,
                )
            if pending and pending_words + words > policy.max_prose_words:
                continuation = _flush_prose_frames(
                    frames,
                    header,
                    pending,
                    continuation=continuation,
                )
                pending_words = 0
            pending.append(copy.deepcopy(block))
            pending_words += words
            continue

        continuation = _flush_prose_frames(
            frames,
            header,
            pending,
            continuation=continuation,
        )
        pending_words = 0
        isolated_blocks: list[dict[str, Any]]
        if kind == "figure-led":
            isolated_blocks = [_shorten_figure_caption(block, policy)]
        elif kind == "table-led":
            table, excerpted = _excerpt_table(block, policy)
            excerpted_tables += int(excerpted)
            isolated_blocks = [table]
        else:
            if words > policy.max_prose_words and kind == "evidence-slide":
                raise _density_error(
                    "slides.density.indivisible-evidence",
                    f"one evidence block contains {words} words; the maximum is {policy.max_prose_words}",
                    source=source,
                    heading=heading,
                    observed_words=words,
                    maximum_words=policy.max_prose_words,
                )
            isolated_blocks = [copy.deepcopy(block)]
        frames.append(
            _Frame(
                title=header,
                blocks=tuple(isolated_blocks),
                kind=kind,
                continuation=continuation,
            )
        )
        continuation += 1

    _flush_prose_frames(frames, header, pending, continuation=continuation)
    return frames, excerpted_tables


def compose_accessible_pandoc_document(
    document: dict[str, Any],
    *,
    policy: AccessibleSlidePolicy,
    source: str,
) -> AccessibleSlideComposition:
    """Compose one Pandoc JSON document into bounded semantic slide frames."""

    if not isinstance(document, dict) or not isinstance(document.get("blocks"), list):
        raise RenderingError(
            "Accessible slide composition requires a Pandoc JSON document",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-json"},
        )
    original_blocks = document["blocks"]
    segments: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    current_header: dict[str, Any] | None = None
    current_blocks: list[dict[str, Any]] = []

    def flush_segment() -> None:
        nonlocal current_header, current_blocks
        if current_header is None and not current_blocks:
            return
        segments.append((current_header or _generated_header("Overview"), current_blocks))
        current_header = None
        current_blocks = []

    for raw in original_blocks:
        if not isinstance(raw, dict) or not isinstance(raw.get("t"), str):
            raise RenderingError(
                "Accessible slide composition received a malformed Pandoc block",
                context={"source": source, "diagnostic_code": "slides.schema.pandoc-block"},
            )
        if raw.get("t") == "Header":
            flush_segment()
            current_header = raw
        else:
            current_blocks.append(raw)
    flush_segment()

    output_blocks: list[dict[str, Any]] = []
    frame_count = 0
    section_dividers = 0
    excerpted_tables = 0
    figure_frames = 0
    for index, (header, blocks) in enumerate(segments):
        level, attributes, _inlines = _header_parts(header)
        classes = {str(value) for value in (attributes[1] if len(attributes) > 1 else [])}
        next_level = _header_parts(segments[index + 1][0])[0] if index + 1 < len(segments) else None
        explicit_divider = (
            level == 1 or "section-divider" in classes or (not blocks and next_level is not None and next_level > level)
        )
        if not blocks:
            if not explicit_divider:
                raise _density_error(
                    "slides.structure.title-only",
                    "a title-only frame is not an explicit section divider",
                    source=source,
                    heading=_header_text(header),
                )
            output_blocks.append(_header_with(header, level=1, section_divider=True))
            section_dividers += 1
            frame_count += 1
            continue

        if level == 1:
            output_blocks.append(_header_with(header, level=1, section_divider=True))
            section_dividers += 1
            frame_count += 1
            content_header = _header_with(header, level=2, continuation=2, frame_kind="section-overview")
            # The section header already owns the source identifier.  The
            # overview frame is a continuation and therefore intentionally has
            # no duplicate identifier.
            content_header["c"][2] = copy.deepcopy(_header_parts(header)[2])
        else:
            content_header = _header_with(header, level=2)

        frames, excerpted = _compose_segment(content_header, blocks, policy=policy, source=source)
        excerpted_tables += excerpted
        for frame in frames:
            output_blocks.append(
                _header_with(
                    frame.title,
                    level=2,
                    continuation=frame.continuation,
                    frame_kind=frame.kind,
                )
            )
            output_blocks.extend(copy.deepcopy(frame.blocks))
            frame_count += 1
            figure_frames += int(frame.kind == "figure-led")

    updated = copy.deepcopy(document)
    updated["blocks"] = output_blocks
    return AccessibleSlideComposition(
        document=updated,
        frame_count=frame_count,
        section_divider_count=section_dividers,
        excerpted_table_count=excerpted_tables,
        figure_frame_count=figure_frames,
    )


def load_and_compose_pandoc_json(
    path: Path,
    *,
    policy: AccessibleSlidePolicy,
    source: str,
) -> AccessibleSlideComposition:
    """Load a Pandoc JSON file and compose it through the accessible policy."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderingError(
            f"Could not read Pandoc JSON for accessible slides: {exc}",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-json"},
        ) from exc
    return compose_accessible_pandoc_document(payload, policy=policy, source=source)


def _set_html_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        flags=re.IGNORECASE,
    )
    if pattern.search(tag):
        return pattern.sub(lambda _match: f'{name}="{escaped}"', tag, count=1)
    return tag[:-1].rstrip() + f' {name}="{escaped}">' if tag.endswith(">") else tag


def _reveal_semantics(content: str) -> str:
    """Name every Reveal slide from its first heading and add slide roles."""

    def replace(match: re.Match[str]) -> str:
        heading_tag = match.group("heading")
        identifier_match = re.search(
            r'(?<!\S)id\s*=\s*["\'](?P<id>[^"\']+)',
            match.group("heading_attrs"),
        )
        if identifier_match is None:
            heading_text = html.unescape(_TAG_RE.sub("", heading_tag)).strip()
            heading_id = "slide-heading-" + hashlib.sha256(heading_text.encode("utf-8")).hexdigest()[:12]
            updated_heading = _set_html_attribute(heading_tag, "id", heading_id)
        else:
            heading_id = identifier_match.group("id")
            updated_heading = heading_tag
        open_tag = _set_html_attribute(match.group("open"), "role", "group")
        open_tag = _set_html_attribute(open_tag, "aria-roledescription", "slide")
        open_tag = _set_html_attribute(open_tag, "aria-labelledby", heading_id)
        return f"{open_tag}{match.group('spacing')}{updated_heading}"

    updated = _SLIDE_OPEN_RE.sub(replace, content)
    unnamed_slide = re.search(
        r"<section\b(?=[^>]*(?<!\S)class\s*=\s*[\"'][^\"']*\bslide\b)[^>]*>"
        r"(?!\s*<h[1-6]\b)",
        updated,
        flags=re.IGNORECASE,
    )
    if unnamed_slide is not None:
        raise RenderingError(
            "[slides.structure.heading] Reveal slide has no semantic heading",
            context={"diagnostic_code": "slides.structure.heading"},
        )
    return updated


def _accessible_reveal_css(policy: AccessibleSlidePolicy) -> str:
    body_px = policy.body_font_pt * (4 / 3)
    title_px = policy.title_font_pt * (4 / 3)
    label_px = policy.figure_label_font_pt * (4 / 3)
    return f"""<style data-template-accessible-slides>
:root {{ --r-background-color: #ffffff; --r-main-color: #111111; --r-link-color: #004b87; }}
.reveal {{ color: #111111; background: #ffffff; font-size: {body_px:.2f}px; }}
.reveal .slides section {{ text-align: left; line-height: 1.35; }}
.reveal h1, .reveal h2, .reveal h3 {{ color: #111111; font-size: {title_px:.2f}px; line-height: 1.15; }}
.reveal a {{ color: #004b87; text-decoration: underline; text-decoration-thickness: 0.11em; }}
.reveal a:focus-visible, .reveal button:focus-visible {{ outline: 4px solid #b34d00; outline-offset: 4px; }}
.reveal table {{ display: block; max-width: 100%; overflow-x: auto; font-size: inherit; border-collapse: collapse; }}
.reveal th, .reveal td {{ border: 2px solid #404040; padding: 0.25em 0.4em; }}
.reveal section.figure-led figure {{
  min-height: {policy.min_figure_area_percent}vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.reveal section.figure-led img {{
  display: block;
  width: 100% !important;
  height: calc({policy.min_figure_area_percent}vh - 5.5rem) !important;
  max-height: calc({policy.min_figure_area_percent}vh - 5.5rem);
  max-width: 100%;
  object-fit: contain;
  margin-inline: auto;
}}
.reveal figcaption, .reveal .slide-reader-link {{ font-size: {label_px:.2f}px; line-height: 1.3; }}
.slide-reader-nav {{
  position: fixed;
  inset-inline-end: 0.75rem;
  inset-block-start: 0.5rem;
  z-index: 30;
  background: #ffffff;
  border: 2px solid #111111;
  padding: 0.3rem 0.55rem;
}}
.skip-link {{
  position: fixed;
  inset-inline-start: 0.5rem;
  inset-block-start: -8rem;
  z-index: 100;
  background: #ffffff;
  color: #111111;
  border: 3px solid #111111;
  padding: 0.5rem;
}}
.skip-link:focus {{ inset-block-start: 0.5rem; }}
.figure-long-description {{ font-size: {label_px:.2f}px; max-height: 35vh; overflow: auto; }}
@media (prefers-reduced-motion: reduce) {{ .reveal .slides section {{ transition: none !important; }} }}
@media (forced-colors: active) {{ .reveal th, .reveal td, .slide-reader-nav {{ border: 2px solid CanvasText; }} }}
</style>"""


def enhance_accessible_reveal(
    html_file: Path,
    *,
    policy: AccessibleSlidePolicy,
    registry_path: Path | None,
    language: str = "en",
) -> None:
    """Apply deterministic semantic, navigation, and visual-accessibility hooks."""

    # Reveal uses ``data-src`` for lazy loading while the shared publication
    # postprocessor intentionally matches ordinary HTML ``src`` attributes.
    # Accessible mode favors predictable native image semantics over lazy
    # loading and normalizes the attribute before applying the shared registry.
    initial = html_file.read_text(encoding="utf-8")
    initial = re.sub(r"(?<!\S)data-src\s*=", "src=", initial, flags=re.IGNORECASE)
    initial = normalize_figure_paths(initial)
    write_if_changed(html_file, initial)
    enhance_accessibility(html_file, language=language, registry_path=registry_path)
    content = html_file.read_text(encoding="utf-8")
    content = _reveal_semantics(content)
    if "data-template-accessible-slides" not in content:
        content = content.replace("</head>", _accessible_reveal_css(policy) + "\n</head>", 1)
    if '<nav class="slide-reader-nav"' not in content:
        reader_href = html.escape(policy.reader_href, quote=True)
        nav = (
            '<nav class="slide-reader-nav" aria-label="Presentation companion">'
            f'<a href="{reader_href}">Open canonical HTML manuscript</a></nav>'
        )
        content = re.sub(r"(<body\b[^>]*>)", rf"\1\n{nav}", content, count=1, flags=re.IGNORECASE)
    content = content.replace(
        '<div class="slides">',
        '<div class="slides" role="region" aria-label="Presentation slides">',
        1,
    )
    if not re.search(r"\bkeyboard\s*:\s*true\b", content):
        raise RenderingError(
            "[slides.accessibility.keyboard] Reveal.js keyboard navigation is not enabled",
            context={"source": str(html_file), "diagnostic_code": "slides.accessibility.keyboard"},
        )
    write_if_changed(html_file, content)


__all__ = [
    "AccessibleSlideComposition",
    "AccessibleSlidePolicy",
    "compose_accessible_pandoc_document",
    "enhance_accessible_reveal",
    "load_and_compose_pandoc_json",
]
