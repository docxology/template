"""Shared structural contract for the template textbook.

Everything that must agree across the manuscript, the figure generators, and the
tests lives here so there is exactly one place to change it:

* ``CITATION_KEYS``  — the keys defined in ``manuscript/references.bib``; chapter
  prose may only cite from this set (extend both together).
* ``GLOSSARY_ANCHORS`` — the ``{#gl:...}`` anchors defined in
  ``manuscript/glossary.md``; chapter prose may only link to these.
* ``REQUIRED_SECTION_HEADINGS`` / ``REQUIRED_TOKENS`` — the structural elements
  every chapter must contain. ``content.validate_chapter`` enforces them and
  ``content.scaffold_chapter`` always emits them, so a freshly scaffolded stub
  passes validation by construction.
* ``STUB_MARKERS`` — the markers authors search for to find what still needs
  writing. Counting them measures fill progress.
"""

from __future__ import annotations

# --- Bibliography -----------------------------------------------------------
# Placeholder keys. Replace with real references as the book is written; keep
# references.bib and this tuple in sync (test_manuscript_integrity checks it).
CITATION_KEYS: tuple[str, ...] = (
    "smith2020foundations",
    "doe2019methods",
    "lee2021systems",
    "garcia2022dynamics",
    "patel2018models",
    "nguyen2023synthesis",
    "kim2020data",
    "brown2017principles",
    "wilson2021analysis",
    "taylor2019theory",
)

# --- Glossary ---------------------------------------------------------------
GLOSSARY_ANCHORS: tuple[str, ...] = (
    "system",
    "model",
    "parameter",
    "variable",
    "equilibrium",
    "feedback",
    "gradient",
    "threshold",
    "network",
    "dynamics",
    "emergence",
    "regulation",
    "boundary",
    "state",
    "observable",
)

# --- Chapter structural contract -------------------------------------------
# H2 headings every chapter must carry (Pandoc auto-numbers; no manual numbers).
REQUIRED_SECTION_HEADINGS: tuple[str, ...] = (
    "Learning Objectives",
    "Summary",
    "Key Terms",
    "Further Reading",
    "Practice",
)

# Literal tokens every chapter must contain (pandoc-crossref + pedagogy markers).
REQUIRED_TOKENS: tuple[str, ...] = (
    "{#sec:",  # section label on the H1
    "{#fig:",  # at least one cross-referencable figure
    "{#tbl:",  # at least one cross-referencable table
    "{#eq:",  # at least one cross-referencable equation
    "```mermaid",  # at least one inline diagram
    "<!-- chapter-metadata-badge -->",  # difficulty/time badge
    "<!-- curriculum-scaffold-start -->",  # study blueprint block
)

# Markers that flag unwritten content. ``content.count_stub_markers`` finds them.
STUB_MARKERS: tuple[str, ...] = ("<!-- STUB", "TODO:", "TKTK")

__all__ = [
    "CITATION_KEYS",
    "GLOSSARY_ANCHORS",
    "REQUIRED_SECTION_HEADINGS",
    "REQUIRED_TOKENS",
    "STUB_MARKERS",
]
