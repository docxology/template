"""Semantic frame composition over validated Pandoc slide blocks."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_ast import (
    _block_kind,
    _estimated_block_lines,
    _frame_body_line_capacity,
    _generated_header,
    _header_parts,
    _header_text,
    _header_with,
    _is_presentation_page_break,
    _shorten_figure_caption,
    _split_prose_block_to_fit,
    _word_count,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    BASE_BODY_LINES_16_9,
    AccessibleSlideComposition,
    AccessibleSlidePolicy,
    _Frame,
    density_error,
)
from infrastructure.rendering._slides_accessibility_tables import _excerpt_table


_BASE_BODY_LINES_16_9 = BASE_BODY_LINES_16_9
_density_error = density_error


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
    pending_lines = 0
    continuation = 1
    excerpted_tables = 0
    heading = _header_text(header)

    # A title that consumes three or more projected lines leaves at most four
    # body lines.  Preserve that full title as an explicit divider, then use
    # the bounded, fully aria-labelled continuation title for content frames.
    # This avoids either shrinking the title or forcing one clause into an
    # unsafely shallow first frame.
    if blocks and _frame_body_line_capacity(header, continuation, policy) <= 4:
        frames.append(
            _Frame(
                title=header,
                blocks=(),
                kind="section-divider",
                continuation=continuation,
            )
        )
        continuation += 1

    for block in blocks:
        if block.get("t") == "HorizontalRule" or _is_presentation_page_break(block):
            continuation = _flush_prose_frames(
                frames,
                header,
                pending,
                continuation=continuation,
            )
            pending_words = 0
            pending_lines = 0
            continue

        kind = _block_kind(block)
        words = _word_count(block)
        if kind == "prose-slide":
            queue = [copy.deepcopy(block)]
            while queue:
                maximum_lines = _frame_body_line_capacity(header, continuation, policy)
                current = queue.pop(0)
                split_blocks = _split_prose_block_to_fit(
                    current,
                    policy=policy,
                    maximum_lines=maximum_lines,
                    source=source,
                    heading=heading,
                )
                if len(split_blocks) > 1:
                    queue = split_blocks + queue
                    continue
                current = split_blocks[0]
                current_words = _word_count(current)
                current_lines = _estimated_block_lines(current, policy)
                combined_lines = pending_lines + (1 if pending else 0) + current_lines
                if pending and (
                    pending_words + current_words > policy.max_prose_words or combined_lines > maximum_lines
                ):
                    continuation = _flush_prose_frames(
                        frames,
                        header,
                        pending,
                        continuation=continuation,
                    )
                    pending_words = 0
                    pending_lines = 0
                    queue.insert(0, current)
                    continue
                pending.append(current)
                pending_words += current_words
                pending_lines = combined_lines
            continue

        continuation = _flush_prose_frames(
            frames,
            header,
            pending,
            continuation=continuation,
        )
        pending_words = 0
        pending_lines = 0
        isolated_blocks: list[dict[str, Any]]
        if kind == "figure-led":
            maximum_lines = _frame_body_line_capacity(header, continuation, policy)
            base_lines = max(1, math.floor(_BASE_BODY_LINES_16_9 * 20 / policy.body_font_pt))
            # Fifteen percentage points of the declared figure-led region are
            # reserved for the 16/19-point reader link and Beamer figure glue.
            # Scale the image against the title-adjusted usable body, never
            # against the global text height.
            image_height_percent = max(
                1,
                math.floor(maximum_lines / base_lines * (policy.min_figure_area_percent - 15)),
            )
            isolated_blocks = [
                _shorten_figure_caption(
                    block,
                    policy,
                    image_height_percent=image_height_percent,
                )
            ]
        elif kind == "table-led":
            table, excerpted = _excerpt_table(
                block,
                policy,
                header=header,
                continuation=continuation,
            )
            excerpted_tables += int(excerpted)
            isolated_blocks = [table]
        else:
            maximum_lines = _frame_body_line_capacity(header, continuation, policy)
            if kind == "evidence-slide" and (
                words > policy.max_prose_words or _estimated_block_lines(block, policy) > maximum_lines
            ):
                raise _density_error(
                    "slides.density.indivisible-evidence",
                    "one evidence block cannot fit the projection frame at the declared font floor",
                    source=source,
                    heading=heading,
                    observed_words=words,
                    maximum_words=policy.max_prose_words,
                    estimated_lines=_estimated_block_lines(block, policy),
                    maximum_lines=maximum_lines,
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
            section_dividers += int(frame.kind == "section-divider")
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
