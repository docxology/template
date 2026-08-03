"""Manuscript structure integrity: section labels are unique and every
``[@sec:...]`` cross-reference resolves to a declared ``{#sec:...}`` label.

The rendered PDF is checked for unresolved ``??`` at render time; this gate
catches label/ref drift at test time, before rendering, and is stable on a
clean checkout (no generated artifacts required).
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = PROJECT_ROOT / "manuscript"

SECTION_FILES = sorted(
    p for p in MANUSCRIPT.glob("*.md") if p.name not in {"preamble.md", "AGENTS.md", "README.md", "SYNTAX.md"}
)

H1_LABEL_RE = re.compile(r"^#\s+.+?\{#(sec:[A-Za-z0-9_\-]+)\}\s*$", re.MULTILINE)
SEC_REF_RE = re.compile(r"@(sec:[A-Za-z0-9_\-]+)")

EXPECTED_LABELS = {
    "sec:abstract",
    "sec:introduction",
    "sec:methodology",
    "sec:results",
    "sec:conclusion",
    "sec:pipeline_internals",
    "sec:reproducibility",
    "sec:references",
}


def test_section_files_present():
    names = {p.name for p in SECTION_FILES}
    assert {
        "00_abstract.md",
        "01_introduction.md",
        "02_methodology.md",
        "03_results.md",
        "04_conclusion.md",
        "05_pipeline_internals.md",
        "06_reproducibility.md",
        "99_references.md",
    } <= names, f"missing section files; got {sorted(names)}"


def test_section_labels_are_unique_and_present():
    labels: list[str] = []
    for path in SECTION_FILES:
        labels.extend(H1_LABEL_RE.findall(path.read_text(encoding="utf-8")))
    assert labels, "no {#sec:...} labels found in manuscript"
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    assert not duplicates, f"duplicate section labels: {duplicates}"
    assert set(labels) == EXPECTED_LABELS, f"label set drifted: {sorted(set(labels) ^ EXPECTED_LABELS)}"


def test_every_sec_reference_resolves():
    declared: set[str] = set()
    referenced: set[str] = set()
    for path in SECTION_FILES:
        text = path.read_text(encoding="utf-8")
        declared.update(H1_LABEL_RE.findall(text))
        referenced.update(SEC_REF_RE.findall(text))
    assert referenced, "no [@sec:...] references found — vacuous pass"
    dangling = sorted(referenced - declared)
    assert not dangling, f"unresolved section references: {dangling}"


def test_no_figure_references():
    """Figures are standalone diagnostics; the manuscript must not cite [@fig:...]."""
    for path in SECTION_FILES:
        text = path.read_text(encoding="utf-8")
        assert "@fig:" not in text, f"{path.name} references a figure label"
