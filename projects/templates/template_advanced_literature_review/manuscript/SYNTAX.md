# Manuscript Syntax

Pandoc citation and cross-reference syntax used by the manuscript sections in this
directory. Sections are rendered with `pandoc` + `pandoc-crossref`.

## Variable injection

Dynamic numbers are written as `{{UPPERCASE_TOKEN}}` and replaced at render time by
`src/manuscript/variables/` (driven by `scripts/05_inject_variables.py`). Every
token used in prose must be produced by the variables package, or the render fails —
never hand-type a computed number.

## Citations

- Cite with `[@key]`, where `key` is an entry in `references.bib`.
- Multiple: `[@key1; @key2]`.

## Cross-references (pandoc-crossref)

- Figures: label `{#fig:label}`, reference `[@fig:label]`.
- Tables: label `{#tbl:label}`, reference `[@tbl:label]`.
- Equations: label `{#eq:label}`, reference `[@eq:label]`.

## Section ordering

Files are concatenated in lexical order: `00_abstract.md`, `01_introduction.md`,
`02*_methods_*.md`, `03*_results_*.md`, `04*_*.md`, appendices, then
`99_references.md`. Keep the numeric prefixes when adding sections.
