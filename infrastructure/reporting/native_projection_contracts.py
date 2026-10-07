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
    root: Path, scope: str, artifact: Any, reader: SnapshotReader
) -> tuple[ProjectionPage, ...]:
    """Reconstruct all selected pitch variants from source, never receipt DeckContent.

    Manuscript Beamer/reveal source projection remains explicit unsupported.
    Pure project helpers rebuild token values from current source configurations,
    generated public counts and original Root Git membership; the enclosing
    producer/reader must retain its existing frozen public-source/Root identity.
    """
    import importlib
    import sys
    import yaml
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
    from infrastructure.rendering.slide_deck import filter_deck_for_budget, SlideBudget

    if (
        scope not in PUBLIC_PROJECT_NAMES
        or scope != "templates/template_pitch_deck"
        or not artifact.id.startswith("pitch:")
    ):
        raise ProjectionSourceUnsupported(
            "manuscript archive/accessible slide projection is not independently compiled"
        )
    parts = artifact.id.split(":")
    if len(parts) != 3 or parts[1] not in {"short", "medium", "long"} or parts[2] not in {"pdf", "pptx"}:
        raise ValueError("pitch artifact is outside source-owned variant identities")
    project = root / "projects" / scope
    source_root = project / "src"
    for path in sorted(source_root.rglob("*.py")):
        reader.read(path.relative_to(root).as_posix())
    config_path = f"projects/{scope}/manuscript/config.yaml"
    config = yaml.safe_load(reader.read(config_path).content)
    deck_config = config.get("project_config", {}).get("deck")
    if not isinstance(deck_config, dict):
        raise ValueError("pitch source has no current project_config.deck")
    subject = str(deck_config.get("pitch_subject", "template_template"))
    if f"templates/{subject}" not in PUBLIC_PROJECT_NAMES:
        raise ValueError("pitch source subject is outside canonical public scope")
    reader.read(f"projects/templates/{subject}/manuscript/config.yaml")
    reader.read("docs/_generated/COUNTS.md")
    reader.read("infrastructure/project/public_scope.py")
    for path in sorted((root / "infrastructure").glob("*/__init__.py")):
        reader.read(path.relative_to(root).as_posix())
    previous_path = list(sys.path)
    try:
        sys.path.insert(0, str(source_root))
        loader = importlib.import_module("template_pitch_deck.content_loader")
        tokens_module = importlib.import_module("template_pitch_deck.deck_tokens")
        orchestration = importlib.import_module("template_pitch_deck.render_orchestration")
        standalone = importlib.import_module("template_pitch_deck.standalone_slides")
        for name, module in tuple(sys.modules.items()):
            if name == "template_pitch_deck" or name.startswith("template_pitch_deck."):
                location = getattr(module, "__file__", None)
                if location is None or not Path(location).resolve().is_relative_to(source_root):
                    raise ProjectionSourceUnsupported("project source helper was imported from a different source tree")
        tokens = tokens_module.build_deck_tokens(root, pitch_subject=subject)
        prefix = orchestration._subject_content_prefix(deck_config, subject)
        relative = f"projects/{scope}/manuscript/{prefix}_{parts[1]}.yaml"
        raw = yaml.safe_load(reader.read(relative).content)
        model = loader.build_deck_content(raw, tokens, figures_dir=project / "output/figures")
        budget = {"short": SlideBudget.SHORT, "medium": SlideBudget.MEDIUM, "long": SlideBudget.LONG}[parts[1]]
        model = filter_deck_for_budget(model, budget)
        source_base = str(deck_config.get("source_base_url", ""))
        model = standalone.attach_qr_urls(model, length=parts[1], pitch_subject=subject, source_base_url=source_base)
        expected_path = f"projects/{scope}/output/{parts[2]}/{subject}_pitch_{parts[1]}.{parts[2]}"
        if artifact.path != expected_path or artifact.format != parts[2]:
            raise ValueError("pitch artifact differs from its exact current source-owned path/format")
        pages = compile_projection_contract(model, source_base_url=source_base, reader=reader)
    finally:
        sys.path[:] = previous_path
    if not reader.unchanged():
        raise ValueError("pitch source/count/configuration inputs changed during independent reconstruction")
    return pages
