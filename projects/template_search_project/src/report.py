"""Assemble the final reading-report markdown from search + synthesis."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from infrastructure.search.literature import Paper, SearchResult

from .synthesis import SynthesisResult


def _format_paper_summary(paper: Paper, citation_key: str) -> str:
    authors = ", ".join(paper.authors) if paper.authors else "Unknown authors"
    locator = f"https://doi.org/{paper.doi}" if paper.doi else (paper.url or "(no link)")
    abstract_line = (paper.abstract or "(no abstract)").strip().splitlines()[0][:240]
    return (
        f"- **[{citation_key}]** *{paper.title}* — {authors} ({paper.year or 'n.d.'})  \n"
        f"  {locator}  \n"
        f"  > {abstract_line}"
    )


def write_reading_report(
    output_path: Path | str,
    *,
    search_result: SearchResult,
    citation_keys: Mapping[str, str],
    per_paper: Iterable[SynthesisResult] = (),
    corpus_synthesis: SynthesisResult | None = None,
    title: str | None = None,
) -> Path:
    """Write a markdown reading report and return its path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# {title or 'Literature Reading Report'}")
    lines.append("")
    lines.append(
        f"_Topic:_ **{search_result.query.text}** · "
        f"_results:_ {len(search_result.papers)} · "
        f"_max-results:_ {search_result.query.max_results}"
    )
    if search_result.query.year_min or search_result.query.year_max:
        ymin = search_result.query.year_min or "—"
        ymax = search_result.query.year_max or "—"
        lines.append(f"_Year filter:_ {ymin} to {ymax}")
    if search_result.errors:
        lines.append("")
        lines.append("> ⚠️ Partial coverage. The following backends reported errors:")
        for source, msg in search_result.errors.items():
            lines.append(f"> - `{source}`: {msg}")
    lines.append("")

    lines.append("## Summary by Source")
    lines.append("")
    if search_result.per_source_counts:
        lines.append("| Source | Papers |")
        lines.append("|---|---:|")
        for source, count in search_result.per_source_counts.items():
            lines.append(f"| `{source}` | {count} |")
    else:
        lines.append("_(no source counts recorded)_")
    lines.append("")

    lines.append("## Papers")
    lines.append("")
    for paper in search_result.papers:
        key = citation_keys.get(paper.id, paper.id)
        lines.append(_format_paper_summary(paper, key))
    lines.append("")

    if corpus_synthesis is not None:
        lines.append("## Cross-Corpus Synthesis")
        lines.append("")
        lines.append(corpus_synthesis.text.strip())
        lines.append("")

    per_paper_list = list(per_paper)
    if per_paper_list:
        lines.append("## Per-Paper Notes")
        lines.append("")
        for entry in per_paper_list:
            key = citation_keys.get(entry.paper_id or "", entry.paper_id or "?")
            lines.append(f"### [{key}]")
            lines.append("")
            lines.append(entry.text.strip())
            lines.append("")

    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out
