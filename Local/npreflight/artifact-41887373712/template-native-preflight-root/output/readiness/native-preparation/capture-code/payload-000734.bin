"""Ordered deck obligations compiled from a source-reconstructed deck model."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.rendering.slide_deck import DeckContent, source_url, plan_content_slide_layout
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@dataclass(frozen=True)
class ProjectionFigure:
    """Exact source pixels plus independently source-derived destination geometry."""

    path: str
    content: bytes
    box_pt: tuple[float, float, float, float]


@dataclass(frozen=True)
class ProjectionPage:
    """Every visible occurrence and source target on one projected page."""

    texts: tuple[tuple[str, str, float], ...]
    citation: str
    qr_target: str
    figure: bool
    figure_projection: ProjectionFigure | None = None
    size_pt: tuple[float, float] = (720.0, 405.0)


def compile_projection_contract(
    deck: DeckContent, *, source_base_url: str = "", reader: SnapshotReader | None = None
) -> tuple[ProjectionPage, ...]:
    """Caller must independently rebuild deck from frozen source, never receipt text.

    Minimum sizes are projection policy, independently enforced on native glyphs.
    Figure presence remains an explicit visual fidelity obligation.
    """
    if not deck.slides:
        raise ValueError("projection contract requires a nonempty deck")
    pages = []
    if deck.slides[0].kind != "title":
        pages.append(ProjectionPage((("title", deck.title, 14.0), ("subtitle", deck.subtitle, 16.0)), "", "", False))
    for slide in deck.slides:
        texts = [("title", slide.title, 14.0)]
        if slide.kind == "title" and deck.subtitle:
            texts.append(("subtitle", deck.subtitle, 16.0))
        texts.extend(("body", "• " + text, 18.0) for text in slide.bullets)
        for role, text, floor in (
            ("stat", slide.stat_value, 22.0),
            ("label", slide.stat_label, 16.0),
            ("quote", slide.quote_text, 18.0),
            ("attribution", slide.quote_attribution, 16.0),
            ("citation", "Source: " + slide.source if slide.source else "", 9.0),
        ):
            if text:
                texts.append((role, text, floor))
        projection = None
        if slide.figure_path is not None and reader is not None:
            from PIL import Image

            figure_path = Path(slide.figure_path)
            if not figure_path.is_absolute():
                figure_path = reader.root / figure_path
            snapshot = reader.read(figure_path.relative_to(reader.root).as_posix())
            with Image.open(BytesIO(snapshot.content)) as image:
                width, height = image.size
            if slide.kind == "diagram":
                # Source-owned 16:9 footer-safe image box; do not read the
                # actual PDF/PPTX geometry to manufacture the expectation.
                max_width, max_height = 640.8, 268.92
                scale = min(max_width / width, max_height / height)
                fitted_width, fitted_height = width * scale, height * scale
                left = 39.6 + (max_width - fitted_width) / 2
                bottom = 64.08 + (max_height - fitted_height) / 2
            else:
                layout = plan_content_slide_layout(slide)
                if layout.figure_height_pt is None or layout.figure_y_pt is None:
                    raise ValueError("source figure has no projection box")
                scale = min(640.8 / width, layout.figure_height_pt / height)
                fitted_width, fitted_height = width * scale, height * scale
                left = 39.6 + (640.8 - fitted_width) / 2
                bottom = layout.figure_y_pt + (layout.figure_height_pt - fitted_height) / 2
            top = 405 - bottom - fitted_height
            projection = ProjectionFigure(
                snapshot.relative, snapshot.content, (left, top, left + fitted_width, top + fitted_height)
            )
        pages.append(
            ProjectionPage(
                tuple(texts),
                source_url(slide.source, source_base_url) or "",
                slide.qr_url,
                slide.figure_path is not None,
                projection,
            )
        )
    return tuple(pages)


def projection_contract_record(pages: tuple[ProjectionPage, ...]) -> dict[str, Any]:
    """Canonical policy identity for strict independent reader comparison."""
    rows = [
        {
            "texts": [list(text) for text in page.texts],
            "citation": page.citation,
            "qr_target": page.qr_target,
            "figure": page.figure,
            "size_pt": list(page.size_pt),
            "figure_projection": None
            if page.figure_projection is None
            else {
                "path": page.figure_projection.path,
                "sha256": hashlib.sha256(page.figure_projection.content).hexdigest(),
                "box_pt": list(page.figure_projection.box_pt),
            },
        }
        for page in pages
    ]
    payload = {"schema_version": "template-native-projection-source-v1", "pages": rows}
    return {**payload, "digest": canonical_digest(payload)}


class ProjectionSourceUnsupported(ValueError):
    """A source-owned projected edition has no complete independent projection yet."""


def compile_scope_projection_contract(
    root: Path,
    scope: str,
    artifact: Any,
    reader: SnapshotReader,
    *,
    tracked_paths: tuple[str, ...],
    deadline: float,
) -> tuple[ProjectionPage, ...]:
    """Use admitted original Root membership and SDK-owned source compilation.

    Generic manuscript projections have complete occurrence/reference contracts
    and must enter observe_manuscript_projection before this literal Pitch path.
    Source DATA is never executable project/provider code or an import root.
    """
    from infrastructure.reporting.native_pitch_source import compile_pitch_source_contract

    if scope != "templates/template_pitch_deck" or not artifact.id.startswith("pitch:"):
        raise ProjectionSourceUnsupported("manuscript slides require their source-aware occurrence/reference adapter")
    return compile_pitch_source_contract(
        root,
        scope,
        artifact,
        reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
