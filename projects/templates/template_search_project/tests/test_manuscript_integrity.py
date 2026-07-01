"""Manuscript integrity regression tests.

These tests guard properties that survive across pipeline runs but are
easy to break when the manuscript is edited:

1. Every Pandoc-crossref reference (``[@sec:foo]``, ``[@fig:bar]``,
   ``[@tbl:baz]``, ``[@eq:quux]``, ``[@lst:zod]``) resolves to a matching
   ``{#sec:foo}`` / ``{#fig:bar}`` / etc. anchor in the manuscript tree.

2. The auto-composed deep-search outputs and the resolved manuscript
   never carry leftover LLM placeholder strings — those must only appear
   when the LLM actually emitted them.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
REPO_ROOT = PROJECT_ROOT.parents[2]

# Files that are documentation-of-syntax rather than rendered manuscript;
# scanning them for citation correctness produces noise (e.g. SYNTAX.md
# intentionally shows examples like `[@sec:methodology]` in code fences).
NON_RENDERED = {"AGENTS.md", "README.md", "preamble.md", "SYNTAX.md"}

# pandoc-crossref namespaces.
_CROSSREF_PREFIXES = ("sec:", "fig:", "tbl:", "eq:", "lst:")

# Strings that *must never* appear in archived deep-search outputs or in
# the rendered manuscript. They were the historic stub-output strings and
# the reason for the no-placeholder refactor.
FORBIDDEN_PLACEHOLDERS = (
    "(LLM unavailable",
    "(LLM init failed",
    "(LLM call failed",
    "_(LLM unavailable",
    "_(LLM init failed",
    "_(LLM call failed",
    "_LLM deep summary disabled",
    "LLM stage stubbed",
)


def _read_manuscript(name: str) -> str:
    return (PROJECT_ROOT / "manuscript" / name).read_text(encoding="utf-8")


def _all_manuscript_text() -> str:
    """Concatenate every renderable markdown source for cross-ref scanning."""
    chunks: list[str] = []
    for md in sorted((PROJECT_ROOT / "manuscript").glob("*.md")):
        if md.name in NON_RENDERED:
            continue
        chunks.append(md.read_text(encoding="utf-8"))
    return "\n\n".join(chunks)


def test_every_crossref_has_matching_anchor() -> None:
    """For every ``[@sec:X]`` / ``[@fig:Y]`` etc., a ``{#sec:X}`` /
    ``{#fig:Y}`` anchor must exist somewhere in the renderable manuscript.

    Catches the failure mode where a section is renamed (anchor moves)
    but a cross-reference still points at the old anchor — Pandoc would
    silently render that as ``[?]`` in the PDF.
    """
    text = _all_manuscript_text()
    refs = set(re.findall(r"\[@((?:sec|fig|tbl|eq|lst):[A-Za-z0-9_\-]+)\]", text))
    anchors = set(re.findall(r"\{#((?:sec|fig|tbl|eq|lst):[A-Za-z0-9_\-]+)\}", text))
    missing = sorted(refs - anchors)
    assert not missing, (
        f"Pandoc-crossref references with no matching {{#anchor}}: {missing}.\nAll anchors found: {sorted(anchors)}"
    )


def test_every_anchor_is_unique() -> None:
    """A single anchor used twice would make Pandoc-crossref ambiguous."""
    text = _all_manuscript_text()
    anchors = re.findall(r"\{#((?:sec|fig|tbl|eq|lst):[A-Za-z0-9_\-]+)\}", text)
    duplicates = sorted({a for a in anchors if anchors.count(a) > 1})
    assert not duplicates, f"Duplicate Pandoc-crossref anchors: {duplicates}"


def test_no_placeholder_strings_in_renderable_manuscript() -> None:
    """The historic stub strings must only appear in prose that
    documents the no-placeholder design (i.e. `05_pipeline_internals.md`
    and `07_deep_search.md` describe what is *not* written into the
    archive). Anywhere else, their presence is a regression."""
    allowed_files = {"05_pipeline_internals.md", "07_deep_search.md"}
    for md in sorted((PROJECT_ROOT / "manuscript").glob("*.md")):
        if md.name in NON_RENDERED or md.name in allowed_files:
            continue
        text = md.read_text(encoding="utf-8")
        for needle in FORBIDDEN_PLACEHOLDERS:
            assert needle not in text, (
                f"Forbidden placeholder string {needle!r} found in {md.name}; "
                f"the no-stub refactor disallows these in manuscript prose."
            )


def test_no_placeholder_strings_in_deep_search_outputs(tmp_path: Path) -> None:
    """End-to-end regression: a deep-search run with ``llm=None`` must
    never emit any of the historic placeholder strings into per-paper
    notes, papers.json, aggregate.json, or the composed S01."""
    iso = tmp_path / "iso"
    (iso / "manuscript").mkdir(parents=True)
    (iso / "data").mkdir()

    # Reuse the bundled corpus so the search returns real papers.
    bundled_corpus = PROJECT_ROOT / "data" / "corpus.json"
    (iso / "data" / "corpus.json").write_text(bundled_corpus.read_text(encoding="utf-8"), encoding="utf-8")

    (iso / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: 'X'\n"
        "search:\n  query: 'reproducible'\n  sources: [local]\n"
        "  local_corpus: 'data/corpus.json'\n"
        "deep_search:\n"
        "  enabled: false\n"
        "  keywords: ['reproducible']\n"
        "  max_results_per_keyword: 3\n"
        "  sources: [local]\n"
        "  fetch_abstracts: false\n"
        "  fetch_fulltext: false\n"
        "  llm_per_paper: false\n"
        "  output_dir: 'output/deep_search'\n"
        "  search_cache_dir: 'output/cache/search'\n"
        "  unified_bibtex_path: 'manuscript/references_deep.bib'\n",
        encoding="utf-8",
    )

    # Step 1: run the deep search with --no-llm so llm=None is forced.
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_deep_search.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
            "--enable",
            "--no-llm",
            "--corpus",
            str(iso / "data" / "corpus.json"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    # Step 2: compose S01 from those outputs.
    proc2 = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "s_compose_literature_review.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc2.returncode == 0, proc2.stderr

    # Step 3: scan every produced artefact for forbidden strings.
    scan_targets: list[Path] = []
    scan_targets.append(iso / "manuscript" / "S01_literature_review.md")
    for p in (iso / "output" / "deep_search").rglob("*.md"):
        scan_targets.append(p)
    for p in (iso / "output" / "deep_search").rglob("*.json"):
        scan_targets.append(p)

    assert scan_targets, "expected at least one deep-search artefact"

    for path in scan_targets:
        text = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN_PLACEHOLDERS:
            assert needle not in text, (
                f"Forbidden placeholder {needle!r} found in {path.relative_to(iso)}; "
                f"deep_search must skip cleanly when llm=None, not emit stubs."
            )

    # Sanity check: the composer's "no LLM contributions" message is
    # acceptable explanatory prose, NOT a fake LLM output.
    s01_text = (iso / "manuscript" / "S01_literature_review.md").read_text(encoding="utf-8")
    assert "Per-paper synthesis omitted" in s01_text
    assert "alice2020convexity" not in s01_text  # sanity: real keys, not test fixture


def test_every_inserted_figure_has_prose_crossref() -> None:
    """For every ``{#fig:X}`` anchor in a manuscript file, the SAME file
    must also contain at least one ``[@fig:X]`` cross-reference in prose.

    Catches the failure mode where a new figure is inserted with an
    anchor but no surrounding prose discusses it — Pandoc-crossref will
    happily emit "Figure 4." with no explanation in the rendered PDF.
    """
    for md in sorted((PROJECT_ROOT / "manuscript").glob("*.md")):
        if md.name in NON_RENDERED:
            continue
        text = md.read_text(encoding="utf-8")
        anchors = set(re.findall(r"\{#(fig:[A-Za-z0-9_\-]+)\}", text))
        # Strip the figure-insertion line itself from the prose pool so a
        # caption containing the same id is not mistaken for a cross-ref.
        prose = re.sub(r"!\[[^\]]*\][^\n]*\n", "", text)
        prose_refs = set(re.findall(r"\[@(fig:[A-Za-z0-9_\-]+)\]", prose))
        missing = sorted(anchors - prose_refs)
        assert not missing, f"{md.name}: figure anchor(s) without a prose [@fig:X] cross-ref: {missing}"


def test_every_disk_figure_is_inserted_in_manuscript() -> None:
    """Each PNG that the figure generator emits to ``output/figures/``
    must be inserted by at least one ``![...](.../filename.png)`` in
    the manuscript tree. Catches orphan figures.
    """
    fig_dir = PROJECT_ROOT / "output" / "figures"
    if not fig_dir.is_dir():
        import pytest as _pytest

        _pytest.skip("output/figures/ absent; run the analysis stage first")
    on_disk = sorted(p.name for p in fig_dir.glob("*.png"))
    if not on_disk:
        import pytest as _pytest

        _pytest.skip("no PNGs in output/figures/")
    inserted: set[str] = set()
    for md in sorted((PROJECT_ROOT / "manuscript").glob("*.md")):
        if md.name in NON_RENDERED:
            continue
        # Image regex tolerates `]` inside backtick spans (e.g.
        # `[year_min, year_max]` literal in the caption) by skipping
        # over balanced inline-code segments first.
        text = re.sub(r"`[^`\n]*`", "<CODE>", md.read_text(encoding="utf-8"))
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
            inserted.add(Path(m.group(1)).name)
    orphans = sorted(set(on_disk) - inserted)
    assert not orphans, (
        f"Figures generated to output/figures/ but never inserted in any "
        f"manuscript file: {orphans}. Either reference them with "
        f"![caption](../output/figures/{{name}}) or remove them from "
        f"src/figures.py."
    )


def test_every_figure_caption_is_substantive() -> None:
    """Every ``![caption](path)`` insertion must carry a caption with at
    least 30 characters of prose (not counting whitespace). Catches the
    failure mode where a figure ships with a one-word "Figure." caption.
    """
    short_captions: list[tuple[str, str]] = []
    for md in sorted((PROJECT_ROOT / "manuscript").glob("*.md")):
        if md.name in NON_RENDERED:
            continue
        text = re.sub(r"`[^`\n]*`", "<CODE>", md.read_text(encoding="utf-8"))
        for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+\.png)\)", text):
            caption = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(caption) < 30:
                short_captions.append((md.name, m.group(2), caption))
    assert not short_captions, f"Figures with under-substantive captions (<30 chars): {short_captions}"


def test_table_anchors_are_unique_and_referenced() -> None:
    """Every ``{#tbl:X}`` anchor must be unique and must have at least
    one ``[@tbl:X]`` cross-reference somewhere in the manuscript."""
    text = _all_manuscript_text()
    anchors = re.findall(r"\{#(tbl:[A-Za-z0-9_\-]+)\}", text)
    refs = set(re.findall(r"\[@(tbl:[A-Za-z0-9_\-]+)\]", text))
    duplicates = sorted({a for a in anchors if anchors.count(a) > 1})
    assert not duplicates, f"Duplicate table anchors: {duplicates}"
    orphans = sorted(set(anchors) - refs)
    assert not orphans, (
        f"Table anchor(s) with no [@tbl:X] cross-ref anywhere in the "
        f"manuscript: {orphans}. Either reference the table or remove "
        f"the anchor."
    )


_HARDCODE_PATTERNS: tuple[tuple[str, str], ...] = (
    # (regex, human-readable rule)
    (r"§\s*\d", "literal `§N` — use `[@sec:X]` so renumbering is automatic"),
    (r"\bsec\.\s*\d", "literal `sec. N` — use `[@sec:X]`"),
    (r"\bSection\s+\d", "literal `Section N` — use `[@sec:X]`"),
    (r"\bfig\.\s*\d", "literal `fig. N` — use `[@fig:X]`"),
    (r"\bFigure\s+\d", "literal `Figure N` — use `[@fig:X]` (Pandoc-crossref renders 'Figure N' for you)"),
    (r"\bEquation\s+\d", "literal `Equation N` — use `[@eq:X]`"),
    (r"\bstage\s+0\d", "literal `stage 0N` — use a semantic name for the pipeline stage"),
    (r"\bStage\s+0\d", "literal `Stage 0N` — use a semantic name for the pipeline stage"),
)


def _project_documentation_files() -> list[Path]:
    """Every documentation file across the project — manuscript prose,
    docs/, READMEs, and AGENTS.md guides — that should be free of
    hard-coded numerical references. Excludes SYNTAX.md (documents the
    convention by example), output/, .venv/, .pytest_cache/."""
    candidates: list[Path] = []
    for md in sorted((PROJECT_ROOT / "manuscript").glob("*.md")):
        if md.name in NON_RENDERED:
            continue
        candidates.append(md)
    candidates.append(PROJECT_ROOT / "README.md")
    candidates.append(PROJECT_ROOT / "AGENTS.md")
    candidates.append(PROJECT_ROOT / "scripts" / "README.md")
    candidates.append(PROJECT_ROOT / "scripts" / "AGENTS.md")
    candidates.append(PROJECT_ROOT / "manuscript" / "AGENTS.md")
    candidates.append(PROJECT_ROOT / "src" / "README.md")
    candidates.append(PROJECT_ROOT / "src" / "AGENTS.md")
    candidates.append(PROJECT_ROOT / "tests" / "README.md")
    candidates.append(PROJECT_ROOT / "tests" / "AGENTS.md")
    docs_dir = PROJECT_ROOT / "docs"
    if docs_dir.is_dir():
        for doc in sorted(docs_dir.rglob("*.md")):
            candidates.append(doc)
    return [p for p in candidates if p.is_file()]


def test_no_hardcoded_numeric_references() -> None:
    """Ban hard-coded numerical section / figure / equation / stage
    references in renderable manuscript prose AND in the project's
    documentation surface (README, AGENTS, docs/). Pandoc-crossref
    renders `[@sec:methodology]` as `sec. 3`, so a literal `sec. 3`
    typed by hand becomes stale the moment the section ordering
    changes; the same drift hazard applies to docs that hand-reference
    the pipeline-DAG ordering ("Stage 02") or specific section numbers.

    This test is the policy enforcement for that rule across the whole
    project.
    """
    failures: list[tuple[str, int, str, str]] = []
    for md in _project_documentation_files():
        if md.name == "SYNTAX.md":
            continue
        for line_no, raw_line in enumerate(md.read_text(encoding="utf-8").splitlines(), start=1):
            # Skip lines that are clearly fenced code, inline code, or
            # the literal `Table N: caption` that Pandoc-crossref
            # auto-generates from a `: caption {#tbl:X}` block. Also
            # skip image-insertion lines (captions reasonably mention
            # numerical values like bin width or score buckets).
            stripped = raw_line.strip()
            if stripped.startswith("```") or stripped.startswith("    "):
                continue
            if stripped.startswith("![") or stripped.startswith("|"):
                continue
            # Strip inline-code spans so `Table 4: Stochastic gradient
            # descent (SGD) parameter settings…` inside a bib-row
            # citation in the supplemental literature review (which
            # is the *paper's own title*, not a cross-reference) is
            # ignored.
            line = re.sub(r"`[^`\n]*`", "<CODE>", raw_line)
            # Strip any pandoc-crossref token so [@sec:X] / [@fig:X]
            # don't trip the regex via their following text.
            line = re.sub(r"\[@(?:sec|fig|tbl|eq|lst):[A-Za-z0-9_\-]+\]", "<XREF>", line)
            for pattern, rule in _HARDCODE_PATTERNS:
                if re.search(pattern, line):
                    failures.append((md.name, line_no, rule, raw_line.strip()))
    assert not failures, "Hard-coded numerical references found — replace with Pandoc-crossref:\n" + "\n".join(
        f"  {name}:{ln}  [{rule}]\n    {text}" for name, ln, rule, text in failures
    )


def test_run_summary_records_real_llm_used_flag() -> None:
    """The pipeline writes ``run_summary.json`` with a real ``llm_used``
    boolean. After the no-stub refactor it must reflect whether an LLM
    actually emitted text — not merely whether the user requested LLM.
    The bundled config disables LLM, so a fresh run must record False."""
    summary_path = PROJECT_ROOT / "output" / "run_summary.json"
    if not summary_path.exists():
        # The pipeline may not have been run in this checkout; skip rather
        # than assert against a stale file.
        import pytest as _pytest

        _pytest.skip("output/run_summary.json absent; run the pipeline first")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    # Bundled config has llm.enabled: false → llm_used must be False.
    assert summary.get("llm_used") is False, (
        f"Bundled config disables LLM; llm_used should be False but is "
        f"{summary.get('llm_used')!r}. Was the pipeline run with LLM enabled?"
    )
