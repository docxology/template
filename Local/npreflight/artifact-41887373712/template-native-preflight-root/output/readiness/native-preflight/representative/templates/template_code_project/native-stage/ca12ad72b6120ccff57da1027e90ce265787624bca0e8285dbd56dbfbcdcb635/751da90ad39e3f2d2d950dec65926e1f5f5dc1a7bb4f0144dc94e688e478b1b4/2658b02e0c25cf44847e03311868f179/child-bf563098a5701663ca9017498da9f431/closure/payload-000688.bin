"""Figure allocation and intrinsic-geometry contracts for accessible slides."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import AccessibleSlidePolicy, density_error
from infrastructure.rendering._slides_accessibility_image_io import (
    IntrinsicImageGeometry,
    inspect_intrinsic_image_geometry,
    validate_local_image_target,
)


# This is the maximum-fit envelope within the common 16:9 body after the
# accessible title, 25-point footer reservation, inline-image baseline depth,
# and frame keylines are accounted for. It is deliberately independent from
# the configurable minimum allocation: the floor reserves figure-led space;
# this ceiling lets the image use the largest safe box in that space.
FIGURE_SAFE_BODY_MAX_HEIGHT_PERCENT_16_9 = 80
FIGURE_SAFE_BODY_MAX_WIDTH_PERCENT = 98
# Reveal's default logical layout is 960 by 700 CSS pixels. Reveal scales that
# canvas to the physical viewport; sizing an image in ``vh`` inside the canvas
# would therefore apply the viewport scale twice at narrow reflow widths.
REVEAL_LOGICAL_SLIDE_HEIGHT_PX = 700
# Figure percentages were validated independently from regular prose leading:
# the one-line-title envelope has eight proportional reference units and a
# two-line title has six. Keep that measured scaling separate from the new
# seven-line regular-body capacity.
FIGURE_SAFE_BODY_REFERENCE_UNITS_16_9 = 8

_FIGURE_ALLOCATION_KEYS = frozenset(
    {
        "data-slide-figure-area-contract",
        "data-slide-figure-intrinsic-aspect",
        "data-slide-figure-intrinsic-height",
        "data-slide-figure-intrinsic-status",
        "data-slide-figure-intrinsic-width",
        "data-slide-figure-max-fit-height-percent",
        "data-slide-figure-min-allocation-percent",
        "style",
    }
)


@dataclass(frozen=True)
class FigureAreaAllocation:
    """Separate a figure-led frame's allocation floor from its max-fit bound."""

    minimum_percent: int
    maximum_height_percent: int

    @property
    def minimum_height_percent(self) -> float:
        """Return the floor within this title/footer-safe body allocation."""

        return self.maximum_height_percent * self.minimum_percent / 100


def _image_nodes(value: object) -> list[dict[str, Any]]:
    """Return image nodes in source order without descending into image alt text."""

    if isinstance(value, list):
        return [image for item in value for image in _image_nodes(item)]
    if not isinstance(value, dict):
        return []
    if value.get("t") == "Image":
        return [value]
    if "c" in value:
        return _image_nodes(value.get("c"))
    # The Pandoc document root and its metadata mapping are containers rather
    # than AST nodes and therefore do not have ``c``. Traverse their values so
    # writer-visible metadata images receive the same target confinement.
    return [image for item in value.values() for image in _image_nodes(item)]


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


def _image_target(image: dict[str, Any]) -> str:
    """Return the source target from one validated Pandoc image node."""

    content = image.get("c")
    if (
        not isinstance(content, list)
        or len(content) != 3
        or not isinstance(content[2], list)
        or not content[2]
        or not isinstance(content[2][0], str)
    ):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Image target")
    return content[2][0]


def validate_document_image_targets(
    value: object,
    *,
    source: str,
    authorized_image_roots: tuple[Path, ...],
    figure_image_root: Path | None = None,
) -> None:
    """Confine every Pandoc image target before either writer sees the AST."""

    for image in _image_nodes(value):
        validate_local_image_target(
            _image_target(image),
            source=source,
            heading="Pandoc document metadata and content",
            authorized_roots=authorized_image_roots,
            figure_root=figure_image_root,
        )


def _intrinsic_image_geometry(
    image: dict[str, Any],
    *,
    source: str,
    heading: str,
    authorized_image_roots: tuple[Path, ...],
    figure_image_root: Path | None,
) -> IntrinsicImageGeometry | None:
    """Validate bounded intrinsic raster geometry inside authorized roots."""

    return inspect_intrinsic_image_geometry(
        _image_target(image),
        source=source,
        heading=heading,
        authorized_roots=authorized_image_roots,
        figure_root=figure_image_root,
    )


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
            "slides.density.figure-area",
            "a multi-image row cannot satisfy the declared minimum figure allocation",
            source=source,
            heading=heading,
            image_count=len(images),
            authored_widths=widths,
            authored_total_width_percent=total_width,
            minimum_total_width_percent=min_figure_area_percent,
        )


def _allocation_style(allocation: FigureAreaAllocation) -> str:
    """Return only renderer-owned CSS variables for the area contract."""

    maximum_height = allocation.maximum_height_percent * REVEAL_LOGICAL_SLIDE_HEIGHT_PX / 100
    minimum_height = allocation.minimum_height_percent * REVEAL_LOGICAL_SLIDE_HEIGHT_PX / 100
    maximum_height_text = f"{maximum_height:.2f}".rstrip("0").rstrip(".")
    minimum_height_text = f"{minimum_height:.2f}".rstrip("0").rstrip(".")
    return (
        f"--template-figure-safe-max-height:{maximum_height_text}px;"
        f"--template-figure-min-allocation-height:{minimum_height_text}px"
    )


def _allocate_figure_area(
    value: object,
    allocation: FigureAreaAllocation,
    *,
    source: str,
    heading: str,
    authorized_image_roots: tuple[Path, ...],
    figure_image_root: Path | None,
) -> None:
    """Carry the allocation floor while independently maximizing image fit.

    The configured percentage is a floor on the isolated title/footer-safe
    figure allocation. It is not an image-height cap and does not describe
    literal ink coverage: an aspect-preserving portrait image may leave
    whitespace without yielding space to competing content.
    """

    images = _image_nodes(value)
    image_count = len(images)
    if not image_count:
        raise density_error(
            "slides.density.figure-area",
            "a figure-led frame has no image to receive the declared allocation",
            source=source,
            heading=heading,
        )

    for image in images:
        content = image.get("c")
        if not isinstance(content, list) or len(content) != 3 or not isinstance(content[0], list):
            raise RenderingError("Accessible slide composition received a malformed Pandoc Image")
        attributes = content[0]
        if len(attributes) != 3 or not isinstance(attributes[1], list) or not isinstance(attributes[2], list):
            raise RenderingError("Accessible slide composition received malformed Pandoc Image attributes")
        geometry = _intrinsic_image_geometry(
            image,
            source=source,
            heading=heading,
            authorized_image_roots=authorized_image_roots,
            figure_image_root=figure_image_root,
        )
        authored_width = next(
            (pair for pair in attributes[2] if isinstance(pair, list) and len(pair) == 2 and pair[0] == "width"),
            None,
        )
        authored_style = next(
            (
                str(pair[1])
                for pair in attributes[2]
                if isinstance(pair, list) and len(pair) == 2 and pair[0] == "style"
            ),
            "",
        )
        if authored_style.strip():
            raise density_error(
                "slides.density.figure-style",
                "authored image CSS cannot override the accessible projection allocation",
                source=source,
                heading=heading,
                figure_target=_image_target(image),
                authored_style=authored_style,
                remediation="remove the image style and use a validated percentage width for multi-image rows",
            )
        key_values = [
            pair
            for pair in attributes[2]
            if not (
                isinstance(pair, list)
                and pair
                and (
                    pair[0] in _FIGURE_ALLOCATION_KEYS
                    or pair[0] == "height"
                    or (pair[0] == "width" and image_count == 1)
                )
            )
        ]
        # A two-percent TeX safety inset avoids an overfull hbox caused by
        # figure-environment glue; it is a keyline, not competing content.
        if image_count == 1:
            key_values.append(["width", f"{FIGURE_SAFE_BODY_MAX_WIDTH_PERCENT}%"])
        elif authored_width is None:
            raise RenderingError("Accessible multi-image projection reached allocation without an explicit width")
        elif "accessible-multi-image-panel" not in attributes[1]:
            attributes[1].append("accessible-multi-image-panel")
        if "accessible-max-fit-image" not in attributes[1]:
            attributes[1].append("accessible-max-fit-image")
        key_values.extend(
            [
                ["height", f"{allocation.maximum_height_percent}%"],
                ["data-slide-figure-area-contract", "allocation-not-ink-coverage"],
                ["data-slide-figure-min-allocation-percent", str(allocation.minimum_percent)],
                ["data-slide-figure-max-fit-height-percent", str(allocation.maximum_height_percent)],
                ["data-slide-figure-intrinsic-status", "validated" if geometry is not None else "unresolved"],
                ["style", _allocation_style(allocation)],
            ]
        )
        if geometry is not None:
            key_values.extend(
                [
                    ["data-slide-figure-intrinsic-width", str(geometry.width)],
                    ["data-slide-figure-intrinsic-height", str(geometry.height)],
                    ["data-slide-figure-intrinsic-aspect", f"{geometry.aspect:.8g}"],
                ]
            )
        attributes[2] = key_values


def shorten_figure_caption(
    block: dict[str, Any],
    policy: AccessibleSlidePolicy,
    *,
    allocation: FigureAreaAllocation,
    source: str,
    heading: str,
    authorized_image_roots: tuple[Path, ...] = (),
    figure_image_root: Path | None = None,
) -> dict[str, Any]:
    """Prepare an isolated image frame while retaining full reader content."""

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
        _allocate_figure_area(
            updated,
            allocation,
            source=source,
            heading=heading,
            authorized_image_roots=authorized_image_roots,
            figure_image_root=figure_image_root,
        )
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
    _allocate_figure_area(
        content[2],
        allocation,
        source=source,
        heading=heading,
        authorized_image_roots=authorized_image_roots,
        figure_image_root=figure_image_root,
    )
    # The footer and Reveal navigation already link the canonical HTML reader.
    # Repeating its full caption inside the projected frame would consume the
    # reserved figure region; the reader retains caption, long description,
    # and exact-value fallback.
    content[1] = [None, []]
    return updated
