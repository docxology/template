from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml

from .characters import generate_cast
from .models import PageSpec, StorybookSpec


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _require_text(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _require_int(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _palette(record: Mapping[str, object]) -> tuple[str, str, str, str]:
    value = record.get("palette")
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("page.palette must contain exactly four colors")
    colors = [item for item in value if isinstance(item, str) and item.startswith("#")]
    if len(colors) != 4:
        raise ValueError("page.palette colors must be hex strings")
    return (colors[0], colors[1], colors[2], colors[3])


VALID_CAPTION_POSITIONS = frozenset({"top", "bottom"})
TRIM_SIZES: dict[str, tuple[int, int]] = {
    "portrait": (1275, 1650),
    "square": (900, 900),
    "widescreen": (1600, 900),
}


def _caption_position(record: Mapping[str, object]) -> str:
    value = record.get("caption_position", "bottom")
    if not isinstance(value, str) or value not in VALID_CAPTION_POSITIONS:
        raise ValueError(f"page.caption_position must be one of {sorted(VALID_CAPTION_POSITIONS)}")
    return value


def _page(record: Mapping[str, object]) -> PageSpec:
    overlay_box = record.get("overlay_box")
    if not isinstance(overlay_box, bool):
        raise ValueError("page.overlay_box must be true or false")
    return PageSpec(
        number=_require_int(record, "number"),
        slug=_require_text(record, "slug"),
        title=_require_text(record, "title"),
        scene=_require_text(record, "scene"),
        text=_require_text(record, "text"),
        overlay_box=overlay_box,
        palette=_palette(record),
        caption_position=_caption_position(record),
    )


def load_storybook(project_root: Path | str) -> StorybookSpec:
    """Load and parse the storybook configuration."""
    root = Path(project_root)
    story_path = root / "content" / "story.yaml"
    payload = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    data = _require_mapping(payload, "story.yaml")
    storybook = _require_mapping(data.get("storybook"), "storybook")

    character_records = data.get("characters")
    if not isinstance(character_records, list):
        raise ValueError("characters must be a list")
    characters = generate_cast(character_records)

    page_records = data.get("pages")
    if not isinstance(page_records, list):
        raise ValueError("pages must be a list")
    pages = tuple(_page(_require_mapping(item, "page")) for item in page_records)
    page_numbers = [page.number for page in pages]
    if page_numbers != list(range(len(pages))):
        raise ValueError("pages must be numbered contiguously from 0")

    output_pdf = Path(_require_text(storybook, "output_pdf"))
    page_width = _require_int(storybook, "page_width")
    page_height = _require_int(storybook, "page_height")
    trim_size = storybook.get("trim_size", "custom")
    if not isinstance(trim_size, str) or not trim_size.strip():
        raise ValueError("storybook.trim_size must be a non-empty string")
    trim_size = trim_size.strip().lower()
    if trim_size in TRIM_SIZES and (page_width, page_height) != TRIM_SIZES[trim_size]:
        raise ValueError(f"storybook page dimensions do not match trim_size={trim_size!r}")
    if page_width < 1 or page_height < 1:
        raise ValueError("storybook page dimensions must be positive")
    spec = StorybookSpec(
        title=_require_text(storybook, "title"),
        subtitle=_require_text(storybook, "subtitle"),
        output_pdf=output_pdf,
        page_width=page_width,
        page_height=page_height,
        characters=characters,
        pages=pages,
        trim_size=trim_size,
    )
    accessibility_issues = validate_accessibility_metadata(spec)
    if accessibility_issues:
        raise ValueError("storybook accessibility metadata failed: " + "; ".join(accessibility_issues))
    return spec


def validate_accessibility_metadata(spec: StorybookSpec) -> tuple[str, ...]:
    """Validate title/alt-text/caption metadata before rendering."""
    issues: list[str] = []
    if not spec.title.strip() or not spec.subtitle.strip():
        issues.append("title and subtitle must be non-empty")
    slugs: set[str] = set()
    for page in spec.pages:
        if page.slug in slugs:
            issues.append(f"duplicate page slug: {page.slug}")
        slugs.add(page.slug)
        if not page.title.strip() or not page.scene.strip() or not page.text.strip():
            issues.append(f"page {page.number} lacks title, scene, or text metadata")
        if page.caption_position not in VALID_CAPTION_POSITIONS:
            issues.append(f"page {page.slug} has an invalid caption position")
    return tuple(issues)


def storybook_variables(spec: StorybookSpec) -> dict[str, Any]:
    """Generate manuscript variables from the storybook."""
    return {
        "title": spec.title,
        "subtitle": spec.subtitle,
        "trim_size": spec.trim_size,
        "page_count": spec.page_count,
        "characters": [
            {
                "id": character.character_id,
                "name": character.name,
                "shape": character.shape,
                "family_shape": character.family_shape,
                "role": character.role,
            }
            for character in spec.characters
        ],
        "pages": [
            {
                "number": page.number,
                "slug": page.slug,
                "title": page.title,
                "scene": page.scene,
                "overlay_box": page.overlay_box,
                "caption_position": page.caption_position,
                "caption_zone": {"position": page.caption_position, "minimum_height": 120},
                "alt_text": (f"Full-page illustrated scene '{page.title}' ({page.scene}). Story text: {page.text}"),
            }
            for page in spec.pages
        ],
    }
