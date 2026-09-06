"""Semantic frame composition over validated Pandoc slide blocks."""

from __future__ import annotations

import copy
from dataclasses import replace
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
    _is_identifier_only_block,
    _is_presentation_page_break,
    _prepare_code_block_for_frame,
    _split_prose_block_to_fit,
    _validate_body_width_geometry,
    _validate_header_geometry,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    AccessibleSlideComposition,
    AccessibleSlidePolicy,
    _Frame,
    density_error,
)
from infrastructure.rendering._slides_accessibility_figures import (
    FIGURE_SAFE_BODY_MAX_HEIGHT_PERCENT_16_9,
    FIGURE_SAFE_BODY_REFERENCE_UNITS_16_9,
    FigureAreaAllocation,
    shorten_figure_caption,
    validate_document_image_targets,
)
from infrastructure.rendering._slides_accessibility_limits import (
    read_bounded_pandoc_json,
    validate_accessible_ast_limits,
)
from infrastructure.rendering._slides_accessibility_tables import _excerpt_table
from infrastructure.rendering._slides_accessibility_raw_tex import (
    _raw_tex_is_nonvisible_declaration,
    _raw_tex_inline_reveal_fallback,
    _raw_tex_reveal_fallback,
    _validate_raw_tex_geometry,
)
from infrastructure.rendering._slides_accessibility_text_geometry import (
    _math_vertical_line_demand,
    _validate_math_geometry,
    _word_count,
)


_density_error = density_error


def _flush_prose_frames(
    frames: list[_Frame],
    title: dict[str, Any],
    pending: list[dict[str, Any]],
    auxiliary_prefix: list[dict[str, Any]],
    *,
    continuation: int,
) -> int:
    if not pending:
        return continuation
    frames.append(
        _Frame(
            title=title,
            blocks=tuple([*auxiliary_prefix, *pending]),
            kind="prose-slide",
            continuation=continuation,
        )
    )
    auxiliary_prefix.clear()
    pending.clear()
    return continuation + 1


def _is_nonvisible_auxiliary_block(block: dict[str, Any]) -> bool:
    """Return whether ``block`` must be retained without owning a frame."""

    return _is_identifier_only_block(block) or _raw_tex_is_nonvisible_declaration(block)


def _with_inline_writer_fallbacks(value: object) -> object:
    """Pair TeX reference inlines with HTML peers in one shallow-copy pass.

    Copying an entire remaining subtree at every ancestor made a deeply nested
    AST quadratic before the recursive projection even reached its leaf. The
    composition entry point already bounds depth and node count; each mapping
    now copies only its own non-content fields and reconstructs ``c`` once.
    """

    if isinstance(value, list):
        rendered: list[object] = []
        for item in value:
            updated = _with_inline_writer_fallbacks(item)
            rendered.append(updated)
            if isinstance(updated, dict):
                fallback = _raw_tex_inline_reveal_fallback(updated)
                if fallback is not None:
                    rendered.append(fallback)
        return rendered
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    if value.get("t") in {"RawBlock", "RawInline"}:
        return copy.deepcopy(value)
    updated = {
        key: (_with_inline_writer_fallbacks(item) if key == "c" else copy.deepcopy(item)) for key, item in value.items()
    }
    return updated


def _block_with_writer_fallbacks(block: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep TeX for Beamer and add HTML peers for Reveal."""

    updated = _with_inline_writer_fallbacks(block)
    if not isinstance(updated, dict):
        raise RenderingError("Accessible writer fallback projection received a malformed block")
    rendered = [updated]
    fallback = _raw_tex_reveal_fallback(block)
    if fallback is not None:
        rendered.append(fallback)
    return rendered


def _blocks_with_writer_fallbacks(blocks: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """Project every frame block through the dual-writer fallback boundary."""

    return [projected for block in blocks for projected in _block_with_writer_fallbacks(block)]


def _header_with_writer_fallbacks(header: dict[str, Any]) -> dict[str, Any]:
    """Project allowlisted TeX reference inlines inside a frame heading."""

    updated = _with_inline_writer_fallbacks(header)
    if not isinstance(updated, dict):
        raise RenderingError("Accessible writer fallback projection received a malformed header")
    return updated


def _compose_segment(
    header: dict[str, Any],
    blocks: list[dict[str, Any]],
    *,
    policy: AccessibleSlidePolicy,
    source: str,
    authorized_image_roots: tuple[Path, ...],
    figure_image_root: Path | None,
) -> tuple[list[_Frame], int]:
    frames: list[_Frame] = []
    pending: list[dict[str, Any]] = []
    auxiliary_prefix: list[dict[str, Any]] = []
    pending_words = 0
    pending_lines = 0
    continuation = 1
    excerpted_tables = 0
    heading = _header_text(header)
    _validate_header_geometry(header, policy=policy, source=source)

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
        if _is_nonvisible_auxiliary_block(block):
            retained = copy.deepcopy(block)
            if pending:
                pending.append(retained)
            else:
                auxiliary_prefix.append(retained)
            continue
        if block.get("t") == "HorizontalRule" or _is_presentation_page_break(block):
            continuation = _flush_prose_frames(
                frames,
                header,
                pending,
                auxiliary_prefix,
                continuation=continuation,
            )
            pending_words = 0
            pending_lines = 0
            continue

        _validate_math_geometry(block, source=source, heading=heading)
        _validate_raw_tex_geometry(block, source=source, heading=heading)
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
                        auxiliary_prefix,
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
            auxiliary_prefix,
            continuation=continuation,
        )
        pending_words = 0
        pending_lines = 0
        isolated_blocks: list[dict[str, Any]]
        if kind == "figure-led":
            maximum_lines = _frame_body_line_capacity(
                header,
                continuation,
                policy,
                base_body_lines=FIGURE_SAFE_BODY_REFERENCE_UNITS_16_9,
            )
            base_lines = max(
                1,
                math.floor(FIGURE_SAFE_BODY_REFERENCE_UNITS_16_9 * 20 / policy.body_font_pt),
            )
            # Max-fit within the title/footer-safe body. The configured
            # percentage remains a distinct minimum allocation contract; it
            # must never become this upper image bound. A wrapped title scales
            # the safe maximum and its corresponding allocation floor together.
            image_max_height_percent = max(
                1,
                math.floor(maximum_lines / base_lines * FIGURE_SAFE_BODY_MAX_HEIGHT_PERCENT_16_9),
            )
            isolated_blocks = [
                *auxiliary_prefix,
                shorten_figure_caption(
                    block,
                    policy,
                    allocation=FigureAreaAllocation(
                        minimum_percent=policy.min_figure_area_percent,
                        maximum_height_percent=image_max_height_percent,
                    ),
                    source=source,
                    heading=heading,
                    authorized_image_roots=authorized_image_roots,
                    figure_image_root=figure_image_root,
                ),
            ]
        elif kind == "table-led":
            table, excerpted = _excerpt_table(
                block,
                policy,
                header=header,
                continuation=continuation,
                source=source,
                heading=heading,
            )
            excerpted_tables += int(excerpted)
            isolated_blocks = [*auxiliary_prefix, table]
        elif kind == "code-led":
            maximum_lines = _frame_body_line_capacity(header, continuation, policy)
            isolated_blocks = [
                *auxiliary_prefix,
                _prepare_code_block_for_frame(
                    block,
                    policy=policy,
                    maximum_lines=maximum_lines,
                    source=source,
                    heading=heading,
                ),
            ]
        else:
            maximum_lines = _frame_body_line_capacity(header, continuation, policy)
            math_source, math_lines = _math_vertical_line_demand(block)
            if kind == "equation-led":
                _validate_body_width_geometry(
                    block,
                    policy=policy,
                    source=source,
                    heading=heading,
                    content_kind="equation",
                )
            elif kind == "evidence-slide":
                _validate_body_width_geometry(
                    block,
                    policy=policy,
                    source=source,
                    heading=heading,
                    content_kind="evidence",
                )
            if kind == "equation-led" and math_lines > maximum_lines:
                raise _density_error(
                    "slides.density.math-height",
                    "one vertically nested equation cannot fit the projection frame at the declared font floor",
                    source=source,
                    heading=heading,
                    math_source=math_source,
                    estimated_lines=math_lines,
                    maximum_lines=maximum_lines,
                )
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
            isolated_blocks = [*auxiliary_prefix, copy.deepcopy(block)]
        auxiliary_prefix.clear()
        frames.append(
            _Frame(
                title=header,
                blocks=tuple(isolated_blocks),
                kind=kind,
                continuation=continuation,
            )
        )
        continuation += 1

    _flush_prose_frames(frames, header, pending, auxiliary_prefix, continuation=continuation)
    if auxiliary_prefix:
        if not frames:
            raise _density_error(
                "slides.structure.title-only",
                "a title-only frame is not an explicit section divider",
                source=source,
                heading=heading,
            )
        frames[-1] = replace(frames[-1], blocks=(*frames[-1].blocks, *auxiliary_prefix))
    return frames, excerpted_tables


def compose_accessible_pandoc_document(
    document: dict[str, Any],
    *,
    policy: AccessibleSlidePolicy,
    source: str,
    authorized_image_roots: tuple[Path, ...] = (),
    figure_image_root: Path | None = None,
) -> AccessibleSlideComposition:
    """Compose one Pandoc JSON document into bounded semantic slide frames."""

    if not isinstance(document, dict) or not isinstance(document.get("blocks"), list):
        raise RenderingError(
            "Accessible slide composition requires a Pandoc JSON document",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-json"},
        )
    validate_accessible_ast_limits(document, source=source)
    # Validate the complete standalone-writer input, not only frame bodies.
    # Pandoc metadata and headings may themselves contain Math, raw TeX, or
    # Image nodes and are copied into the composed document. A document-wide
    # preflight prevents those sibling routes from bypassing body validation.
    metadata = document.get("meta")
    metadata_values = list(metadata.values()) if isinstance(metadata, dict) else []
    # Frame headers and retained body blocks are validated below after
    # presentation-only page-break nodes have been removed. Metadata bypasses
    # that segmentation path, so validate it explicitly before it is copied to
    # the standalone writer document.
    _validate_math_geometry(metadata_values, source=source, heading="Pandoc document metadata")
    _validate_raw_tex_geometry(metadata_values, source=source, heading="Pandoc document metadata")
    validate_document_image_targets(
        document,
        source=source,
        authorized_image_roots=authorized_image_roots,
        figure_image_root=figure_image_root,
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
        _validate_header_geometry(header, policy=policy, source=source)
        classes = {str(value) for value in (attributes[1] if len(attributes) > 1 else [])}
        next_level = _header_parts(segments[index + 1][0])[0] if index + 1 < len(segments) else None
        projected_blocks = [
            block
            for block in blocks
            if block.get("t") != "HorizontalRule"
            and not _is_presentation_page_break(block)
            and not _is_nonvisible_auxiliary_block(block)
        ]
        explicit_divider = (
            level == 1
            or "section-divider" in classes
            or (not projected_blocks and next_level is not None and next_level > level)
        )
        if not projected_blocks:
            if not explicit_divider:
                raise _density_error(
                    "slides.structure.title-only",
                    "a title-only frame is not an explicit section divider",
                    source=source,
                    heading=_header_text(header),
                )
            output_blocks.append(_header_with_writer_fallbacks(_header_with(header, level=1, section_divider=True)))
            output_blocks.extend(copy.deepcopy(block) for block in blocks if _is_nonvisible_auxiliary_block(block))
            section_dividers += 1
            frame_count += 1
            continue

        if level == 1:
            output_blocks.append(_header_with_writer_fallbacks(_header_with(header, level=1, section_divider=True)))
            section_dividers += 1
            frame_count += 1
            content_header = _header_with(header, level=2, continuation=2, frame_kind="section-overview")
            # The section header already owns the source identifier.  The
            # overview frame is a continuation and therefore intentionally has
            # no duplicate identifier.
            content_header["c"][2] = copy.deepcopy(_header_parts(header)[2])
        else:
            content_header = _header_with(header, level=2)

        frames, excerpted = _compose_segment(
            content_header,
            blocks,
            policy=policy,
            source=source,
            authorized_image_roots=authorized_image_roots,
            figure_image_root=figure_image_root,
        )
        excerpted_tables += excerpted
        for frame in frames:
            output_blocks.append(
                _header_with_writer_fallbacks(
                    _header_with(
                        frame.title,
                        level=2,
                        continuation=frame.continuation,
                        frame_kind=frame.kind,
                    )
                )
            )
            output_blocks.extend(_blocks_with_writer_fallbacks(frame.blocks))
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
    authorized_image_roots: tuple[Path, ...] = (),
    figure_image_root: Path | None = None,
) -> AccessibleSlideComposition:
    """Load a Pandoc JSON file and compose it through the accessible policy."""

    try:
        payload = json.loads(read_bounded_pandoc_json(path, source=source))
    except RecursionError as exc:
        raise RenderingError(
            "[slides.schema.pandoc-limits] Accessible Pandoc JSON exceeds the parser nesting limit",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-limits"},
        ) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderingError(
            f"Could not read Pandoc JSON for accessible slides: {exc}",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-json"},
        ) from exc
    return compose_accessible_pandoc_document(
        payload,
        policy=policy,
        source=source,
        authorized_image_roots=authorized_image_roots,
        figure_image_root=figure_image_root,
    )
