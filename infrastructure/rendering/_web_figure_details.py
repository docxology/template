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
    """Return an associated image tag and an escaped optional disclosure."""

    if record.long_description is None:
        return image_tag, ""
    identifier = _details_identifier(record)
    visible_label = html.escape(record.label.removeprefix("fig:").replace("-", " "))
    paragraphs = "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in record.long_description.split("\n\n"))
    disclosure = (
        f'<details id="{html.escape(identifier, quote=True)}" class="figure-long-description" '
        f'data-figure-label="{html.escape(record.label, quote=True)}">'
        f"<summary>Detailed description of figure {visible_label}</summary>{paragraphs}</details>"
    )
    return _set_aria_details(image_tag, identifier), disclosure


__all__ = ["apply_figure_long_description"]
