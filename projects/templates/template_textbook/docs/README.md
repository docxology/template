# `template_textbook` Documentation

A domain-neutral, modular, **fillable** scaffold for book-length technical
works. The book's structure is data-driven from a single
[`manuscript/config.yaml`](../manuscript/config.yaml); a tested Python backbone
under [`src/`](../src) scaffolds, validates, and illustrates the manuscript; and
thin orchestrator [`scripts/`](../scripts) wire everything into the repository's
reproducible pipeline.

If you are new here, read these in order.

## Guides

| Guide | Read it to learn |
| --- | --- |
| [`architecture.md`](architecture.md) | The two-layer + thin-orchestrator design as applied here: `config.yaml` as source of truth, the `src/textbook` engine, visualization + mermaid, and the data flow into the rendered book. |
| [`manuscript_guide.md`](manuscript_guide.md) | How the manuscript is laid out (parts → chapters → labs → questions), the per-chapter required-element contract, and how auto-numbering and cross-references work. |
| [`authoring_guide.md`](authoring_guide.md) | The end-to-end fill-the-stubs workflow, and how to grow the book to hundreds or thousands of pages while keeping the contract green. |
| [`visualization_guide.md`](visualization_guide.md) | How figures and Mermaid diagrams are generated deterministically, the `<part_id>_<stem>.png` filename contract, and how to add a real figure for a chapter. |
| [`testing_guide.md`](testing_guide.md) | The test suite, the no-mocks policy, the 90% coverage gate, the manuscript-integrity tests, and the `audit_textbook_quality.py` gate — with exact commands. |

## Source-of-truth files

These are the artifacts the guides keep pointing back to:

- [`manuscript/config.yaml`](../manuscript/config.yaml) — the book structure
  (parts, chapters, labs, question banks, appendices, layout, typography).
- [`src/textbook/`](../src/textbook) — the content engine
  (`constants`, `config`, `toc`, `content`, `models`).
- [`src/visualization/`](../src/visualization) and
  [`src/mermaid/`](../src/mermaid) — deterministic figure and diagram generators.
- [`scripts/`](../scripts) — thin orchestrators
  (`generate_figures.py`, `generate_diagrams.py`, `analysis.py`,
  `scaffold_chapter.py`, `audit_textbook_quality.py`).
- [`tests/`](../tests) — the full suite, including
  [`test_manuscript_integrity.py`](../tests/test_manuscript_integrity.py).

## Authoring contract in one screen

Every chapter carries a labelled H1 (`{#sec:<part>_<stem>}`), at least one
figure (`{#fig:...}`) with alt text, a metadata badge, a Study Blueprint,
Learning Objectives, a worked formalism (an equation `{#eq:...}` plus a
parameter table `{#tbl:...}`), an inline `` ```mermaid `` diagram, and
Summary / Key Terms / Further Reading / Practice sections. Cross-references use
pandoc-crossref syntax (`[@fig:..]`, `[@tbl:..]`, `[@eq:..]`, `[@sec:..]`) —
never hand-numbered. Citations `[@key]` must resolve in
[`references.bib`](../manuscript/references.bib); glossary links
`[**term**](#gl:<anchor>)` must resolve in
[`glossary.md`](../manuscript/glossary.md). The full contract and how to fill it
live in the [authoring guide](authoring_guide.md).

## Tooling

All commands use `uv` (never `pip`/`npm`). From inside the project directory,
tests run with `uv run --extra dev python -m pytest`; from the monorepo root, use
the repo-root form (`uv run python -m pytest
projects/templates/template_textbook/tests/ …`) shown in the
[`README.md`](../README.md) quick start. Figures and diagrams are produced by the
scripts, never by hand. See each guide for exact invocations.
