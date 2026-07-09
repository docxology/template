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
from infrastructure.rendering.slide_deck import DeckTheme, SlideBudget, filter_deck_for_budget, render_pdf

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
    config_path = project_root / "manuscript" / "config.yaml"
    config = cast(dict, yaml.safe_load(config_path.read_text(encoding="utf-8")))
    return cast(dict, config.get("deck", {}))


def _resolve_theme(deck_config: dict) -> DeckTheme:
    theme_config = deck_config.get("theme", {})
    return DeckTheme(**theme_config) if theme_config else DeckTheme()


def _try_import_render_pptx():
    """Return `render_pptx` if the opt-in `python-pptx` group is installed, else `None`.

    Importing `infrastructure.rendering.pptx_deck` itself never raises
    `ImportError` (that module catches the `pptx` import internally so
    `render_pptx` can raise a clear `RenderingError` at call time instead) —
    so availability must be checked via `is_pptx_available()`, not via a
    try/except around the module import, which would always succeed.
    """
    from infrastructure.rendering.pptx_deck import is_pptx_available, render_pptx

    return render_pptx if is_pptx_available() else None


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
    content_path = manuscript_dir / f"deck_content_{length}.yaml"
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


def render_all_decks(project_root: Path, repo_root: Path, logger: logging.Logger) -> list[Path]:
    """Render all three lengths. Raises `DeckAuditFailure`/`RenderingError` on any failure."""
    manuscript_dir = project_root / "manuscript"
    figures_dir = project_root / "output" / "figures"
    pdf_dir = project_root / "output" / "pdf"
    pptx_dir = project_root / "output" / "pptx"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pptx_dir.mkdir(parents=True, exist_ok=True)

    deck_config = load_deck_config(project_root)
    theme = _resolve_theme(deck_config)
    source_base_url = deck_config.get("source_base_url", "")
    tokens = build_deck_tokens(repo_root)

    render_pptx_fn = _try_import_render_pptx()
    if render_pptx_fn is None:
        logger.warning(
            "python-pptx not installed — skipping PPTX rendering. "
            "Install with `uv sync --group rendering-pptx` for all six artifacts."
        )

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
            )
        )

    expected = 6 if render_pptx_fn is not None else 3
    if len(written) != expected:
        raise RenderingError(f"Expected {expected} artifacts, wrote {len(written)}")

    return written


__all__ = [
    "DECK_LENGTHS",
    "DeckAuditFailure",
    "DiligenceAuditFailure",
    "load_deck_config",
    "render_one_length",
    "render_all_decks",
]
