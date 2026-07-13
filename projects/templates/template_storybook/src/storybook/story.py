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
    return StorybookSpec(
        title=_require_text(storybook, "title"),
        subtitle=_require_text(storybook, "subtitle"),
        output_pdf=output_pdf,
        page_width=_require_int(storybook, "page_width"),
        page_height=_require_int(storybook, "page_height"),
        characters=characters,
        pages=pages,
    )


def storybook_variables(spec: StorybookSpec) -> dict[str, Any]:
    """Generate manuscript variables from the storybook."""
    return {
        "title": spec.title,
        "subtitle": spec.subtitle,
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
            }
            for page in spec.pages
        ],
    }
