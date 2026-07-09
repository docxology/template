"""Diligence audit: every slide that states a live-sourced fact must cite where it came from.

A slide "states a fact" here means its raw (pre-resolution) text references
one of the token families that `deck_tokens.build_deck_tokens` sources live
from the repository (`PITCH_SUBJECT_*`, `EXEMPLAR_*`). Any such slide must
carry a non-empty `source` field so a reviewer — or `render_pdf`'s
`source_base_url` deep-link — can click straight through to the file that
backs the claim, rather than trusting prose.
"""

from __future__ import annotations

from pathlib import Path

from token_resolution import find_tokens

FACT_TOKEN_PREFIXES: tuple[str, ...] = ("PITCH_SUBJECT_", "EXEMPLAR_", "SECOND_EXEMPLAR_", "INFRA_", "PITCH_DECK_")


def slide_text_blob(slide: dict) -> str:
    """Concatenate every prose field on a raw slide dict for token scanning."""
    parts = [slide.get("title", ""), *slide.get("bullets", [])]
    for field_name in ("stat_value", "stat_label", "quote_text", "quote_attribution"):
        if slide.get(field_name):
            parts.append(slide[field_name])
    return " ".join(parts)


def slide_cites_a_fact(slide: dict) -> bool:
    """Return whether this slide's raw text references a live-sourced fact token.

    ``title``-kind slides (deck opener/closer) are exempt even if they name
    the pitch subject via `{{PITCH_SUBJECT_TITLE}}` — a cover/closing slide
    is front/back matter, not a factual claim that needs a footnote.
    """
    if slide.get("kind") == "title":
        return False
    tokens = find_tokens(slide_text_blob(slide))
    return any(token.startswith(prefix) for token in tokens for prefix in FACT_TOKEN_PREFIXES)


def _citation_exists_on_disk(source: str, repo_root: Path | None) -> bool:
    """Whether ``source`` — an absolute URL, or a repo-relative path — resolves to something real.

    Absolute URLs (already checked reachable by nothing here — this project
    never fetches over the network) are trusted as-is. A repo-relative path
    is checked against the filesystem so a typo'd/renamed/deleted citation
    fails the gate the same way a missing citation does, rather than reading
    as "verified" while silently pointing at nothing (red-team finding,
    2026-07-09). When ``repo_root`` isn't provided (e.g. a caller auditing
    raw content in isolation, with no repo context), existence is not
    checked — only non-emptiness — matching the prior behavior.
    """
    if repo_root is None:
        return True
    if source.startswith("http://") or source.startswith("https://"):
        return True
    return (repo_root / source).exists()


def diligence_rows(raw: dict, repo_root: Path | None = None) -> list[dict]:
    """One row per slide: 1-based index, title, whether it needs a citation, whether it has one.

    1-based to match every other slide-numbering convention in this project
    (`standalone_slides.py`'s "Slide N of M" / `slide_NN.md`, the rendered
    deck's own page order) — a prior 0-based version here made error messages
    off by one from the file/heading a reviewer would actually go look at.
    """
    rows = []
    for i, slide in enumerate(raw.get("slides", []), start=1):
        needs = slide_cites_a_fact(slide)
        source = slide.get("source", "")
        has_citation = bool(source) and _citation_exists_on_disk(source, repo_root)
        rows.append(
            {
                "index": i,
                "title": slide.get("title", ""),
                "needs_citation": needs,
                "has_citation": has_citation,
            }
        )
    return rows


def uncited_fact_slides(raw: dict, repo_root: Path | None = None) -> list[dict]:
    """Rows for slides that reference a fact token but carry no valid `source` citation."""
    return [row for row in diligence_rows(raw, repo_root) if row["needs_citation"] and not row["has_citation"]]


__all__ = ["FACT_TOKEN_PREFIXES", "slide_text_blob", "slide_cites_a_fact", "diligence_rows", "uncited_fact_slides"]
