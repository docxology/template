#!/usr/bin/env python3
"""Compose the deep-search outputs into a supplemental literature-review section.

Reads:
  output/deep_search/aggregate.json
  output/deep_search/aggregate_report.md
  output/deep_search/<keyword_slug>/reading_report.md
  output/deep_search/<keyword_slug>/per_paper/*.md
  manuscript/references_deep.bib

Writes:
  manuscript/S01_literature_review.md
    A supplemental section (filename prefix ``S01_`` follows the Pandoc
    supplemental convention used across this template). Pandoc orders
    main sections (``01_*`` … ``99_references.md``) ahead of supplemental
    sections (``S01_*`` … ``S99_*``), so the auto-composed literature
    review renders at the back of the PDF as an appendix.

    The section is fully traceable and citable:
      - lists each keyword's coverage and per-source breakdown
      - tabulates every paper with citation key + DOI/URL + year
      - inlines the LLM-generated CONTRIBUTION + SIGNIFICANCE paragraphs
        per paper (if present)
      - cross-references manuscript/references_deep.bib so the combined-PDF
        pipeline (Pandoc ``--natbib`` + BibTeX) resolves every [@key]

  output/manuscript/S01_literature_review.md  (only when that directory
    already exists — defensive parity write so a stale resolver copy
    never references citation keys absent from the regenerated
    ``references_deep.bib``).

  output/deep_search/composition_summary.json
    Machine-readable summary of what was composed.

Execution order: this script must run **before**
``z_generate_manuscript_variables.py`` (which copies
``manuscript/`` → ``output/manuscript/``). The filename prefix ``s_``
keeps it sorted after ``run_*`` and before ``y_*``/``z_*`` in
``scripts/02_run_analysis.py`` lexicographic discovery.

Exit codes:
  0   composed successfully (or skipped cleanly when deep_search disabled)
  1   composition failed
  2   no deep-search outputs to compose (graceful skip)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))

from infrastructure.core.logging.utils import get_logger
from infrastructure.reference.citation import parse_bibfile

from src.config import load_project_config
from src.dotenv import load_dotenv

load_dotenv(_project_root / ".env")
logger = get_logger(__name__)


_SECTION_RE = re.compile(r"^## (Contribution|Significance for [^\n]+)$", re.MULTILINE)


def _extract_section(note_md: str, section_name: str) -> str | None:
    """Pull a specific ``## Section`` body out of a per-paper note."""
    if not note_md:
        return None
    pattern = re.compile(
        rf"^## {re.escape(section_name)}.*?$(.+?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(note_md)
    if m:
        return m.group(1).strip()
    return None


def _extract_significance(note_md: str) -> str | None:
    """Find the ``## Significance for <keyword>`` body."""
    if not note_md:
        return None
    pattern = re.compile(
        r"^## Significance for [^\n]+$(.+?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(note_md)
    if m:
        return m.group(1).strip()
    return None


def _safe_id(paper_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", paper_id)


def _format_locator(paper: dict) -> str:
    """Render the DOI / URL column without tripping the markdown
    ``LINK_BAD_TEXT`` validator.

    The validator (`infrastructure.validation.content.markdown_validator`)
    flags any link whose label contains ``/`` or starts with ``http`` as
    non-informative. DOIs naturally contain ``/`` so we keep the DOI as
    plain text and render the clickable target with a slash-free label.
    """
    doi = paper.get("doi")
    url = paper.get("url")
    if doi:
        return f"DOI {doi} ([open](https://doi.org/{doi}))"
    if url:
        return f"[external link]({url})"
    return "—"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        default=str(_project_root / "manuscript" / "config.yaml"),
    )
    parser.add_argument(
        "--project-root",
        default=str(_project_root),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output markdown path (defaults to manuscript/S01_literature_review.md).",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)
    deep_dir = (project_root / config.deep_search.output_dir).resolve()

    aggregate_json = deep_dir / "aggregate.json"
    if not aggregate_json.exists():
        logger.info(
            "No deep-search outputs at %s — skipping literature-review composition.",
            aggregate_json,
        )
        return 2

    payload = json.loads(aggregate_json.read_text(encoding="utf-8"))
    keywords: list[str] = list(payload.get("keywords") or [])
    unique_papers: list[dict] = list(payload.get("unique_papers") or [])
    citation_keys: dict[str, str] = dict(payload.get("citation_keys") or {})

    # Validate every cited key exists in the unified BibTeX file.
    bib_path = (project_root / config.deep_search.unified_bibtex_path).resolve()
    bib_keys: set[str] = set()
    if bib_path.exists():
        bib_db = parse_bibfile(bib_path)
        bib_keys = set(bib_db.keys())
    missing_keys = sorted(
        key for key in citation_keys.values() if key and key not in bib_keys
    )
    if missing_keys:
        logger.warning(
            "%d citation key(s) absent from %s: %s",
            len(missing_keys),
            bib_path,
            ", ".join(missing_keys[:10]),
        )

    # Gather per-paper notes by paper id.
    per_paper_notes: dict[str, str] = {}
    for kw in keywords:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", kw.strip().lower()).strip("_") or "keyword"
        note_dir = deep_dir / slug / "per_paper"
        if not note_dir.exists():
            continue
        for paper in unique_papers:
            note_path = note_dir / (_safe_id(paper["id"]) + ".md")
            if note_path.exists() and paper["id"] not in per_paper_notes:
                per_paper_notes[paper["id"]] = note_path.read_text(encoding="utf-8")

    # Compose the literature-review section.
    out_path = Path(args.output) if args.output else (
        project_root / "manuscript" / "S01_literature_review.md"
    )

    lines: list[str] = []
    # Pandoc-friendly supplemental break: forces a new page and opens a
    # clearly labelled appendix section in the rendered PDF.
    lines.append("\\newpage")
    lines.append("")
    lines.append(
        "# Supplemental S1 — Literature Review (auto-composed from deep search) "
        "{#sec:supplemental_s1}"
    )
    lines.append("")
    lines.append(
        "_Composed by `scripts/s_compose_literature_review.py` from the most "
        "recent deep-search run. Edit the script, not this file — manual edits "
        "will be overwritten on the next pipeline run._"
    )
    lines.append("")
    lines.append(
        f"This review covers **{len(keywords)} keyword(s)**, "
        f"**{len(unique_papers)} unique paper(s)** "
        f"(retrieved at up to {config.deep_search.max_results_per_keyword} per "
        f"keyword from {', '.join(config.deep_search.sources)}). All references "
        f"are stored in `{config.deep_search.unified_bibtex_path}` and resolved "
        f"by the combined-PDF pipeline (Pandoc `--natbib` + BibTeX over "
        f"all `manuscript/*.bib` files)."
    )
    lines.append("")

    # Per-keyword tables
    for kw in keywords:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", kw.strip().lower()).strip("_") or "keyword"
        kw_dir = deep_dir / slug
        kw_papers_path = kw_dir / "papers.json"
        if not kw_papers_path.exists():
            continue
        kw_data = json.loads(kw_papers_path.read_text(encoding="utf-8"))
        kw_papers = list(kw_data.get("papers") or [])

        lines.append(f"## {kw}")
        lines.append("")
        per_source = ", ".join(
            f"{src}={count}" for src, count in (kw_data.get("per_source_counts") or {}).items()
        ) or "—"
        errors = ", ".join((kw_data.get("errors") or {}).keys()) or "none"
        lines.append(
            f"_Papers retrieved:_ **{len(kw_papers)}** · "
            f"_per-source contributions:_ {per_source} · "
            f"_backend errors:_ {errors}"
        )
        lines.append("")

        lines.append("| Cite | Title | Year | DOI / URL |")
        lines.append("|---|---|---:|---|")
        for paper in kw_papers:
            key = citation_keys.get(paper["id"], paper["id"])
            title = (paper.get("title") or "(untitled)").replace("|", "\\|")
            year = paper.get("year") or "n.d."
            locator = _format_locator(paper)
            # `[@key]` (no backticks) renders as a Pandoc citation, e.g.
            # "[Smith, 2024]", which keeps the column narrow regardless of
            # how long the underlying citation key is.
            lines.append(f"| [@{key}] | {title} | {year} | {locator} |")
        lines.append("")

    # Per-paper synthesis paragraphs. Skip the entire section when no LLM
    # ran for any paper (every per-paper note would be a placeholder), so
    # the rendered PDF doesn't ship 30 identical "(no contribution)" stubs.
    notes_with_contribution = [
        paper for paper in unique_papers
        if (note := per_paper_notes.get(paper["id"]))
        and _extract_section(note, "Contribution") is not None
    ]
    if notes_with_contribution:
        lines.append("## Per-paper synthesis")
        lines.append("")
        for paper in notes_with_contribution:
            key = citation_keys.get(paper["id"], paper["id"])
            note = per_paper_notes[paper["id"]]
            contribution = _extract_section(note, "Contribution") or ""
            significance = _extract_significance(note) or ""
            lines.append(f"### [@{key}] — {paper['title']}")
            lines.append("")
            if paper.get("authors"):
                lines.append(", ".join(paper["authors"]))
                lines.append("")
            lines.append("**Contribution.** " + contribution.replace("\n\n", " "))
            lines.append("")
            if significance:
                lines.append("**Significance.** " + significance.replace("\n\n", " "))
                lines.append("")
    elif per_paper_notes:
        # Notes exist but no Contribution sections — explain why instead
        # of rendering 30 identical placeholder rows.
        lines.append(
            "_Per-paper synthesis omitted — no LLM Contribution paragraphs "
            "are present in the deep-search outputs (set `deep_search.llm_per_paper: "
            "true` and ensure Ollama is reachable to populate this section)._"
        )
        lines.append("")

    # Composition stats footer
    lines.append("---")
    lines.append("")
    lines.append(
        f"_Composition summary: {len(keywords)} keywords · "
        f"{len(unique_papers)} unique papers · "
        f"{len(per_paper_notes)} per-paper notes integrated · "
        f"{len(bib_keys)} BibTeX entries · "
        f"{len(missing_keys)} key(s) missing from bib._"
    )
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composed_text = "\n".join(lines).rstrip() + "\n"
    out_path.write_text(composed_text, encoding="utf-8")

    # Defensive parity write. ``z_generate_manuscript_variables.py``
    # normally runs *after* this script and copies ``manuscript/`` →
    # ``output/manuscript/`` so the freshly composed S01 reaches the
    # render stage. If a previous run already populated
    # ``output/manuscript/`` (e.g. when the user reran only this
    # script), mirror the new text there too so the combined-PDF
    # validator never sees a stale copy referencing citation keys that
    # were dropped in the latest ``references_deep.bib``.
    resolved_dir = project_root / "output" / "manuscript"
    if resolved_dir.is_dir():
        resolved_dir.joinpath(out_path.name).write_text(
            composed_text, encoding="utf-8"
        )

    summary = {
        "output_path": str(out_path),
        "keywords": keywords,
        "unique_papers": len(unique_papers),
        "per_paper_notes_integrated": len(per_paper_notes),
        "bibtex_path": str(bib_path),
        "bibtex_keys": len(bib_keys),
        "missing_citation_keys": missing_keys,
    }
    summary_path = deep_dir / "composition_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(str(out_path))
    print(str(summary_path))
    logger.info(
        "Composed literature review: %d papers across %d keyword(s) → %s",
        len(unique_papers),
        len(keywords),
        out_path,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
