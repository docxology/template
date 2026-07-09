"""Load ``manuscript/deck_content_*.yaml`` into a token-resolved ``DeckContent``.

This is the only place project code touches
``infrastructure.rendering.slide_deck`` objects directly — everything here is
content-domain (YAML parsing, token substitution), never layout/drawing code.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml

from infrastructure.rendering.slide_deck import DeckContent, Slide

from token_resolution import resolve_tokens


def load_deck_yaml(path: Path) -> dict:
    """Parse a ``deck_content_*.yaml`` file into a raw dict (no token resolution yet)."""
    return cast(dict, yaml.safe_load(path.read_text(encoding="utf-8")))


def raw_deck_texts(raw: dict) -> dict[str, str]:
    """Flatten every text field in a raw deck dict into ``{field_id: text}``.

    Used to run token-resolution and cliche-lint audits over the deck's full
    text surface without needing to fully build a `DeckContent` first.
    """
    texts: dict[str, str] = {"title": raw.get("title", ""), "subtitle": raw.get("subtitle", "")}
    for i, slide in enumerate(raw.get("slides", [])):
        texts[f"slide[{i}].title"] = slide.get("title", "")
        for j, bullet in enumerate(slide.get("bullets", [])):
            texts[f"slide[{i}].bullets[{j}]"] = bullet
        if slide.get("notes"):
            texts[f"slide[{i}].notes"] = slide["notes"]
        for field_name in ("stat_value", "stat_label", "quote_text", "quote_attribution"):
            if slide.get(field_name):
                texts[f"slide[{i}].{field_name}"] = slide[field_name]
    return texts


def build_deck_content(raw: dict, tokens: dict[str, str], figures_dir: Path | None = None) -> DeckContent:
    """Resolve tokens across a raw deck dict and return a `DeckContent`."""
    title = resolve_tokens(raw.get("title", ""), tokens)
    subtitle = resolve_tokens(raw.get("subtitle", ""), tokens)

    slides: list[Slide] = []
    for slide in raw.get("slides", []):
        slide_title = resolve_tokens(slide.get("title", ""), tokens)
        bullets = tuple(resolve_tokens(bullet, tokens) for bullet in slide.get("bullets", []))
        notes = resolve_tokens(slide.get("notes", ""), tokens) if slide.get("notes") else ""
        figure_name = slide.get("figure")
        figure_path = (figures_dir / figure_name) if (figures_dir and figure_name) else None
        stat_value = resolve_tokens(slide.get("stat_value", ""), tokens) if slide.get("stat_value") else ""
        stat_label = resolve_tokens(slide.get("stat_label", ""), tokens) if slide.get("stat_label") else ""
        quote_text = resolve_tokens(slide.get("quote_text", ""), tokens) if slide.get("quote_text") else ""
        quote_attribution = (
            resolve_tokens(slide.get("quote_attribution", ""), tokens) if slide.get("quote_attribution") else ""
        )
        slides.append(
            Slide(
                title=slide_title,
                bullets=bullets,
                kind=slide.get("kind", "content"),
                notes=notes,
                figure_path=figure_path,
                stat_value=stat_value,
                stat_label=stat_label,
                quote_text=quote_text,
                quote_attribution=quote_attribution,
                # Citation path, not templated prose — copied through verbatim so
                # a diligence audit can check coverage/deep-link every claim.
                source=slide.get("source", ""),
            )
        )

    return DeckContent(title=title, subtitle=subtitle, slides=tuple(slides), metadata=raw.get("metadata", {}))


__all__ = ["load_deck_yaml", "raw_deck_texts", "build_deck_content"]
