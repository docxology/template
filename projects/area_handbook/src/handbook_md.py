"""Deterministic Markdown fragments for handbook preview and reports."""

from __future__ import annotations

from .corpus_stats import evidence_counts_by_theme, themes_without_evidence
from .models import AreaCorpus, EvidenceItem, SynthesisResult


def _bullet_evidence(items: tuple[EvidenceItem, ...], max_items: int = 12) -> str:
    lines: list[str] = []
    for e in items[:max_items]:
        lines.append(
            f"- ({e.weight:.2f}) {e.statement} — *{e.source_label}*, reviewed {e.reviewed_at}"
        )
    if len(items) > max_items:
        lines.append(f"- … and {len(items) - max_items} more items")
    return "\n".join(lines) if lines else "- *(No evidence mapped yet.)*"


def build_executive_summary_md(synth: SynthesisResult) -> str:
    """Short bullet list for abstract or dashboard."""
    c = synth.corpus
    gap_str = ", ".join(synth.gaps) if synth.gaps else "none"
    unused = themes_without_evidence(c)
    unused_str = ", ".join(unused) if unused else "none"
    lines = [
        f"- **Area:** {c.area_label} (`{c.area_id}`), corpus v{c.version}",
        f"- **Handbook sections:** {len(synth.sections)}",
        f"- **Evidence items:** {len(c.evidence)}",
        f"- **Coverage threshold:** {synth.gap_threshold:.2f} (sections below this score are gaps)",
        f"- **Gap sections:** {gap_str}",
        f"- **Themes with no evidence rows:** {unused_str}",
    ]
    return "\n".join(lines)


def render_section_markdown(section_id: str, synth: SynthesisResult) -> str:
    """Markdown body for one section from synthesis rollups."""
    sec = next((s for s in synth.sections if s.section_id == section_id), None)
    if sec is None:
        return f"## Unknown section `{section_id}`\n"
    ev = synth.evidence_by_section.get(section_id, ())
    score = synth.scores.get(section_id, 0.0)
    gap_note = " *(below coverage target)*" if section_id in synth.gaps else ""
    body = [
        f"## {sec.title}",
        "",
        f"**Coverage score:** {score:.2f}{gap_note}",
        "",
        "### Evidence",
        "",
        _bullet_evidence(ev),
        "",
    ]
    return "\n".join(body)


def build_full_handbook_body(synth: SynthesisResult) -> str:
    """Concatenate all section bodies in outline order."""
    parts = [
        build_executive_summary_md(synth),
        "",
        build_gap_report_md(synth),
        "",
        build_evidence_by_theme_table_md(synth.corpus),
        "",
    ]
    for sec in synth.sections:
        parts.append(render_section_markdown(sec.section_id, synth))
        parts.append("")
    return "\n".join(parts).strip() + "\n"


def build_glossary_md(corpus: AreaCorpus) -> str:
    """Theme table for appendix or SYNTAX companion."""
    lines = ["## Theme glossary", ""]
    lines.append("| Theme | Label | Description |")
    lines.append("|-------|-------|-------------|")
    for t in corpus.themes:
        desc = t.description.replace("|", "\\|")
        lines.append(f"| `{t.id}` | {t.label} | {desc} |")
    lines.append("")
    return "\n".join(lines)


def build_gap_report_md(synth: SynthesisResult) -> str:
    """Markdown section listing gap sections and their scores."""
    lines = [
        "## Gap report",
        "",
        f"Threshold: **{synth.gap_threshold:.2f}** (strictly below = gap).",
        "",
    ]
    if not synth.gaps:
        lines.append("*No gap sections for this corpus at the current threshold.*")
        lines.append("")
        return "\n".join(lines)
    lines.append("| Section | Score |")
    lines.append("|---------|-------|")
    for sid in sorted(synth.gaps):
        sc = synth.scores.get(sid, 0.0)
        lines.append(f"| `{sid}` | {sc:.2f} |")
    lines.append("")
    return "\n".join(lines)


def build_evidence_by_theme_table_md(corpus: AreaCorpus) -> str:
    """Markdown table of evidence row counts per theme."""
    counts = evidence_counts_by_theme(corpus)
    lines = [
        "## Evidence volume by theme",
        "",
        "| Theme | Evidence rows |",
        "|-------|---------------|",
    ]
    for tid in sorted(counts.keys()):
        lines.append(f"| `{tid}` | {counts[tid]} |")
    for t in corpus.themes:
        if t.id not in counts:
            lines.append(f"| `{t.id}` | 0 |")
    lines.append("")
    return "\n".join(lines)


def build_toc_md(synth: SynthesisResult) -> str:
    """Handbook outline as a bullet TOC with section ids."""
    lines = ["## Handbook outline", ""]
    for sec in synth.sections:
        indent = "  " * max(0, sec.depth - 1)
        lines.append(f"{indent}- `{sec.section_id}` — {sec.title}")
    lines.append("")
    return "\n".join(lines)
