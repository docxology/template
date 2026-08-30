"""Safe HTML association for source-owned figure long descriptions."""

from __future__ import annotations

import html
import re

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._figure_alt_registry import FigureAltRecord


def _attribute_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        flags=re.IGNORECASE | re.DOTALL,
    )


def _details_identifier(record: FigureAltRecord) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", record.label).strip("-") or "figure"
    return f"{slug}-long-description"


def _set_aria_details(image_tag: str, identifier: str) -> str:
    """Associate structured detail without repeating it in the image name."""

    escaped = html.escape(identifier, quote=True)
    pattern = _attribute_pattern("aria-details")
    if pattern.search(image_tag):
        return pattern.sub(lambda _match: f'aria-details="{escaped}"', image_tag, count=1)
    insert_at = image_tag.rfind("/>")
    if insert_at < 0:
        insert_at = image_tag.rfind(">")
    if insert_at < 0:  # Defensive: callers pass a matched ``img`` tag.
        raise RenderingError("Rendered registry figure has a malformed image tag")
    return image_tag[:insert_at].rstrip() + f' aria-details="{escaped}" ' + image_tag[insert_at:]


def apply_figure_long_description(
    image_tag: str,
    record: FigureAltRecord,
) -> tuple[str, str]:
    """Return an associated image tag and escaped non-visual companions."""

    if record.long_description is None and record.exact_value_fallback is None:
        return image_tag, ""
    visible_label = html.escape(record.label.removeprefix("fig:").replace("-", " "))
    companions: list[str] = []
    updated_image = image_tag
    if record.long_description is not None:
        identifier = _details_identifier(record)
        paragraphs = "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in record.long_description.split("\n\n"))
        companions.append(
            f'<details id="{html.escape(identifier, quote=True)}" '
            f'class="figure-long-description" '
            f'data-figure-label="{html.escape(record.label, quote=True)}">'
            f"<summary>Detailed description of figure {visible_label}</summary>"
            f"{paragraphs}</details>"
        )
        updated_image = _set_aria_details(updated_image, identifier)
    if record.exact_value_fallback is not None:
        if record.exact_value_href is None:  # Registry parsing owns this invariant.
            raise RenderingError(
                f"Figure exact-value fallback has no safe companion path: {record.label}",
            )
        companions.append(
            '<p class="figure-exact-values">'
            f'<a href="{html.escape(record.exact_value_href, quote=True)}">'
            f"Open exact values for figure {visible_label} "
            f"({html.escape(record.exact_value_fallback)})</a></p>"
        )
    return updated_image, "".join(companions)


__all__ = ["apply_figure_long_description"]
