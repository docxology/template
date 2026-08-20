"""Render-all-decks orchestration logic, kept out of ``scripts/20_render_decks.py``
so that script stays a thin CLI wrapper (load config → call this → report).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import yaml

from content_loader import build_deck_content, load_deck_yaml
from deck_audit import audit_deck
from deck_tokens import build_deck_tokens
from diligence_audit import uncited_fact_slides
from standalone_slides import attach_qr_urls, write_standalone_slides

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.slide_deck import (
    DeckTheme,
    SlideBudget,
    filter_deck_for_budget,
    render_pdf,
    validate_deck_layout,
)

DECK_LENGTHS: tuple[str, ...] = ("short", "medium", "long")
_BUDGETS = {"short": SlideBudget.SHORT, "medium": SlideBudget.MEDIUM, "long": SlideBudget.LONG}


class DeckAuditFailure(RuntimeError):
    """Raised when a deck's content audit (token resolution or cliche lint) fails."""


class DiligenceAuditFailure(RuntimeError):
    """Raised when a fact-bearing slide lacks a `source` citation.

    Previously this check only ran via the separate `scripts/30_audit_diligence.py`
    — a deck could render successfully and still ship uncited. Wired in here
    (2026-07-09) so the render itself refuses to produce output for
    undiligenced content, matching this project's own "fail-closed, not
    fail-open" deck content.
    """


def load_deck_config(project_root: Path) -> dict:
    """Load canonical nested deck settings, with legacy root-key compatibility."""
    config_path = project_root / "manuscript" / "config.yaml"
    config = cast(dict, yaml.safe_load(config_path.read_text(encoding="utf-8")))
    project_config = config.get("project_config", {})
    if isinstance(project_config, dict) and isinstance(project_config.get("deck"), dict):
        return cast(dict, project_config["deck"])
    return cast(dict, config.get("deck", {}))


def _resolve_theme(deck_config: dict) -> DeckTheme:
    theme_config = deck_config.get("theme", {})
    return DeckTheme(**theme_config) if theme_config else DeckTheme()


def _try_import_render_pptx():
    """Return ``render_pptx`` when the project runtime dependency is available.

    Importing `infrastructure.rendering.pptx_deck` itself never raises
    `ImportError` (that module catches the `pptx` import internally so
    `render_pptx` can raise a clear `RenderingError` at call time instead) —
    so availability must be checked via `is_pptx_available()`, not via a
    try/except around the module import, which would always succeed.
    """
    from infrastructure.rendering.pptx_deck import is_pptx_available, render_pptx

    return render_pptx if is_pptx_available() else None


def _configured_formats(deck_config: dict) -> tuple[str, ...]:
    """Return the validated project-owned deck formats in declaration order."""
    raw_formats = deck_config.get("formats", ["pdf", "pptx"])
    if not isinstance(raw_formats, list) or not raw_formats or any(not isinstance(item, str) for item in raw_formats):
        raise RenderingError("deck.formats must be a non-empty list of format names")
    formats = tuple(dict.fromkeys(raw_formats))
    unsupported = sorted(set(formats) - {"pdf", "pptx"})
    if unsupported:
        raise RenderingError(f"Unsupported declared deck format(s): {', '.join(unsupported)}")
    if "pdf" not in formats:
        raise RenderingError("template_pitch_deck requires the declared pdf format")
    return formats


def _select_pptx_renderer(formats: tuple[str, ...], candidate):
    """Fail closed when configuration requires PPTX but its renderer is absent."""
    if "pptx" not in formats:
        return None
    if candidate is None:
        raise RenderingError(
            "deck.formats declares pptx, but python-pptx is unavailable in the project runtime; "
            "sync projects/templates/template_pitch_deck before running Stage 02"
        )
    return candidate


def render_one_length(
    length: str,
    *,
    project_root: Path,
    repo_root: Path,
    manuscript_dir: Path,
    figures_dir: Path,
    pdf_dir: Path,
    pptx_dir: Path,
    tokens: dict[str, str],
    theme: DeckTheme,
    source_base_url: str,
    render_pptx_fn,
    logger: logging.Logger,
    content_prefix: str = "deck_content",
) -> list[Path]:
    """Audit, resolve, budget-filter, and render one deck length. Returns written paths.

    Before rendering, writes one standalone Markdown page per slide
    (`standalone_slides.write_standalone_slides`) and attaches each slide's
    own deep-link URL (`attach_qr_urls`) so both renderers can draw a
    scannable QR code pointing at that exact slide's standalone page.

    Raises `DeckAuditFailure` on an unresolved token/cliche hit, or
    `DiligenceAuditFailure` on a fact-bearing slide with no `source` citation
    — both before any PDF/PPTX bytes are written.
    """
    content_path = manuscript_dir / f"{content_prefix}_{length}.yaml"
    raw = load_deck_yaml(content_path)

    result = audit_deck(length, raw, tokens)
    if not result.ok:
        raise DeckAuditFailure(f"[{length}] audit failed: {result.unresolved_error or result.cliche_hits}")

    uncited = uncited_fact_slides(raw, repo_root)
    if uncited:
        titles = ", ".join(row["title"] or f"slide {row['index']}" for row in uncited)
        raise DiligenceAuditFailure(
            f"[{length}] {len(uncited)} fact-bearing slide(s) with no source citation: {titles}"
        )

    resolved_deck = build_deck_content(raw, tokens, figures_dir=figures_dir)
    budgeted_deck = filter_deck_for_budget(resolved_deck, _BUDGETS[length])
    validate_deck_layout(budgeted_deck)
    pitch_subject = tokens["PITCH_SUBJECT_NAME"]

    standalone_paths = write_standalone_slides(
        budgeted_deck,
        length=length,
        pitch_subject=pitch_subject,
        project_root=project_root,
        source_base_url=source_base_url,
    )
    logger.info("[%s] wrote %d standalone slide page(s)", length, len(standalone_paths))
    deck_with_qr = attach_qr_urls(
        budgeted_deck, length=length, pitch_subject=pitch_subject, source_base_url=source_base_url
    )

    written: list[Path] = []
    pdf_path = pdf_dir / f"{pitch_subject}_pitch_{length}.pdf"
    render_pdf(deck_with_qr, pdf_path, theme=theme, source_base_url=source_base_url)
    logger.info("[%s] wrote PDF: %s (%d content slides)", length, pdf_path, len(deck_with_qr.slides))
    written.append(pdf_path)

    if render_pptx_fn is not None:
        pptx_path = pptx_dir / f"{pitch_subject}_pitch_{length}.pptx"
        render_pptx_fn(deck_with_qr, pptx_path, theme=theme, source_base_url=source_base_url)
        logger.info("[%s] wrote PPTX: %s", length, pptx_path)
        written.append(pptx_path)

    return written


def _subject_content_prefix(deck_config: dict, pitch_subject: str) -> str:
    """Resolve a configured subject to a safe local deck-content prefix."""
    subjects = deck_config.get("subjects", {})
    if isinstance(subjects, dict):
        subject_config = subjects.get(pitch_subject, {})
        if isinstance(subject_config, dict):
            prefix = subject_config.get("content_prefix", "deck_content")
            if isinstance(prefix, str) and prefix and "/" not in prefix and "\\" not in prefix:
                return prefix
    return "deck_content"


def _preflight_all_lengths(
    *,
    manuscript_dir: Path,
    repo_root: Path,
    tokens: dict[str, str],
    content_prefix: str,
    figures_dir: Path | None = None,
) -> None:
    """Audit and layout-check every length before generated output is touched."""
    for length in DECK_LENGTHS:
        raw = load_deck_yaml(manuscript_dir / f"{content_prefix}_{length}.yaml")
        result = audit_deck(length, raw, tokens)
        if not result.ok:
            raise DeckAuditFailure(f"[{length}] audit failed: {result.unresolved_error or result.cliche_hits}")
        uncited = uncited_fact_slides(raw, repo_root)
        if uncited:
            titles = ", ".join(row["title"] or f"slide {row['index']}" for row in uncited)
            raise DiligenceAuditFailure(
                f"[{length}] {len(uncited)} fact-bearing slide(s) with no source citation: {titles}"
            )
        resolved_deck = build_deck_content(raw, tokens, figures_dir=figures_dir)
        validate_deck_layout(filter_deck_for_budget(resolved_deck, _BUDGETS[length]))


def render_all_decks(
    project_root: Path,
    repo_root: Path,
    logger: logging.Logger,
    pitch_subject: str | None = None,
) -> list[Path]:
    """Render all three lengths. Raises `DeckAuditFailure`/`RenderingError` on any failure."""
    manuscript_dir = project_root / "manuscript"
    figures_dir = project_root / "output" / "figures"
    pdf_dir = project_root / "output" / "pdf"
    pptx_dir = project_root / "output" / "pptx"
    deck_config = load_deck_config(project_root)
    theme = _resolve_theme(deck_config)
    source_base_url = deck_config.get("source_base_url", "")
    selected_subject = pitch_subject or str(deck_config.get("pitch_subject", "template_template"))
    tokens = build_deck_tokens(repo_root, pitch_subject=selected_subject)
    content_prefix = _subject_content_prefix(deck_config, selected_subject)
    _preflight_all_lengths(
        manuscript_dir=manuscript_dir,
        repo_root=repo_root,
        tokens=tokens,
        content_prefix=content_prefix,
        figures_dir=figures_dir,
    )

    formats = _configured_formats(deck_config)
    render_pptx_fn = _select_pptx_renderer(formats, _try_import_render_pptx())
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pptx_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for length in DECK_LENGTHS:
        written.extend(
            render_one_length(
                length,
                project_root=project_root,
                repo_root=repo_root,
                manuscript_dir=manuscript_dir,
                figures_dir=figures_dir,
                pdf_dir=pdf_dir,
                pptx_dir=pptx_dir,
                tokens=tokens,
                theme=theme,
                source_base_url=source_base_url,
                render_pptx_fn=render_pptx_fn,
                logger=logger,
                content_prefix=content_prefix,
            )
        )

    expected = len(DECK_LENGTHS) * len(formats)
    if len(written) != expected:
        raise RenderingError(f"Expected {expected} artifacts, wrote {len(written)}")

    return written


__all__ = [
    "DECK_LENGTHS",
    "DeckAuditFailure",
    "DiligenceAuditFailure",
    "_configured_formats",
    "_preflight_all_lengths",
    "_select_pptx_renderer",
    "_subject_content_prefix",
    "load_deck_config",
    "render_one_length",
    "render_all_decks",
]
