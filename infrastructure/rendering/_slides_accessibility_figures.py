"""Pandoc figure rows, projection allocation, and caption handling for accessible slides."""

from __future__ import annotations

import copy
import math
import re
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import AccessibleSlidePolicy, density_error


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


def _has_projection_hard_line_break(value: object) -> bool:
    """Return whether layout outside image alternative text forces a new row."""

    if isinstance(value, list):
        return any(_has_projection_hard_line_break(item) for item in value)
    if not isinstance(value, dict):
        return False
    if value.get("t") == "Image":
        return False
    if value.get("t") == "LineBreak":
        return True
    return _has_projection_hard_line_break(value.get("c"))


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
    min_figure_area_percent: int,
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
    if _has_projection_hard_line_break(row_block):
        raise density_error(
            "slides.density.multi-image-layout",
            "hard line breaks cannot turn multiple images into projection pseudo-rows",
            source=source,
            heading=heading,
            image_count=len(images),
        )
    widths = [_image_width_percent(image) for image in images]
    total_width = math.fsum(width for width in widths if width is not None)
    if any(width is None for width in widths) or total_width > 96:
        raise density_error(
            "slides.density.multi-image-layout",
            "a multi-image row requires explicit percentage widths totaling at most 96 percent",
            source=source,
            heading=heading,
            image_count=len(images),
            authored_widths=widths,
            maximum_total_width_percent=96,
        )
    if total_width < min_figure_area_percent:
        raise density_error(
            "slides.density.multi-image-layout",
            "a multi-image row must occupy the declared minimum usable figure width",
            source=source,
            heading=heading,
            image_count=len(images),
            authored_widths=widths,
            authored_total_width_percent=total_width,
            minimum_total_width_percent=min_figure_area_percent,
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
        if len(attributes) != 3 or not isinstance(attributes[1], list) or not isinstance(attributes[2], list):
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
        elif "accessible-multi-image-panel" not in attributes[1]:
            attributes[1].append("accessible-multi-image-panel")
        key_values.append(["height", f"{image_height_percent}%"])
        attributes[2] = key_values


def _shorten_figure_caption(
    block: dict[str, Any],
    policy: AccessibleSlidePolicy,
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
        _validate_projection_image_row(
            updated,
            source=source,
            heading=heading,
            min_figure_area_percent=policy.min_figure_area_percent,
        )
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
    _validate_projection_image_row(
        content[2],
        source=source,
        heading=heading,
        min_figure_area_percent=policy.min_figure_area_percent,
    )
    _allocate_figure_area(content[2], image_height_percent)
    # The accessible Beamer footer and Reveal companion navigation already
    # link the canonical HTML reader at the required label floor. Repeating a
    # long caption-shaped link inside every figure would take space away from
    # the declared 70% figure region. Keep the projected caption empty; the
    # canonical reader retains the complete caption, long description, and
    # exact-value fallback through the source-owned figure registry.
    content[1] = [None, []]
    return updated
