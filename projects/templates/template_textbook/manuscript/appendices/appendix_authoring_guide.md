# Appendix A — Authoring Guide: Filling the Stubs {#sec:appendix_authoring_guide}

<!-- chapter-metadata-badge -->
> Reference appendix · For authors and contributors · Read this first.

This is the most important file in the template. It explains how to turn the
empty scaffold into a finished book by **filling stubs** and **growing**
structure from a single source of truth. Read it once end-to-end, then keep it
open while you work.

## The Big Idea: One Source of Truth

The book is **data-driven from [`config.yaml`](../config.yaml)**. The list of
parts, chapters, labs, question banks, and reference appendices lives there and
nowhere else. The Python engine in `src/textbook/` reads that file and the
scaffolding scripts in `scripts/` materialise the matching markdown files. You
never hand-number a chapter, figure, equation, or section — pandoc-crossref does
that at render time from the labels you write.

The flow is always the same:

```text
edit config.yaml  ->  scaffold_chapter.py  ->  fill <!-- STUB --> blocks
      ->  add figures / glossary terms / references  ->  audit + tests
```

## Step 1 — Decide the Structure in `config.yaml`

Open [`config.yaml`](../config.yaml). To add or rename a chapter, edit the
`parts:` tree (each chapter has a `stem` and a `title`); to add a lab or
question bank, add an entry under `appendices.labs` / `appendices.questions`
for the matching part. The stem drives every downstream name:

- chapter file → `manuscript/<part>/<NN>_<stem>.md`, label `{#sec:<part>_<stem>}`
- lab file → `manuscript/labs/<part>/lab_<stem>.md`, label `{#sec:lab_<part>_<stem>}`
- question bank → `manuscript/questions/<part>/q_<stem>.md`, label `{#sec:q_<part>_<stem>}`

Keep stems short, lowercase, and `snake_case`. Do not invent a numbering scheme;
the table of contents and labels are derived in `src/textbook/toc.py`.

## Step 2 — Materialise the Stubs

Run the scaffolder. It only **creates files that are missing**, so it is safe to
re-run after every config change:

```bash
uv run python scripts/scaffold_chapter.py
```

This writes a chapter (or lab, or question bank) pre-populated with every
required structural element as `<!-- STUB -->` markers. Your job is to replace
the stubs with real prose, never to delete the structure.

## Step 3 — Fill the Content Contract

Every chapter must carry these elements (enforced by `validate_chapter` in
`src/textbook/content.py` and by the integrity tests). Fill each, keep the
markers' surrounding structure:

- a labelled H1: `# Title {#sec:<part>_<stem>}`
- a metadata badge line: `<!-- chapter-metadata-badge -->`
- a Study Blueprint: `<!-- curriculum-scaffold-start -->`
- **Learning Objectives**
- one figure with alt text and a crossref label `{#fig:...}`
- a worked formalism: an equation `{#eq:...}` plus a parameter table `{#tbl:...}`
- an inline ` ```mermaid ` diagram
- **Summary**, **Key Terms**, **Further Reading**, **Practice** sections

Cross-reference syntax is pandoc-crossref: `[@fig:..]`, `[@tbl:..]`, `[@eq:..]`,
`[@sec:..]`. Stub markers the audit counts are `<!-- STUB -->`, `TODO:`, and
`TKTK` — drive these to zero as the chapter matures.

## Step 4 — Add a Figure

Figures are deterministic matplotlib output. Each chapter expects a placeholder
named `<part_id>_<stem>.png`. To make it real, add or edit a function in
[`src/visualization/plots.py`](../../src/visualization/plots.py) (the four worked
figures show the pattern), then regenerate:

```bash
uv run python scripts/generate_figures.py
```

For diagrams, edit `src/mermaid/diagram_specs.yaml` and run
`scripts/generate_diagrams.py` (PNG, or `.mmd` fallback). Reference the figure in
prose with `[@fig:<part>_<stem>]` and give it alt text.

## Step 5 — Add a Glossary Term

Glossary anchors are a **closed contract**. To add a term you must update **both**:

1. `GLOSSARY_ANCHORS` in [`src/textbook/constants.py`](../../src/textbook/constants.py)
2. the matching entry in [`glossary.md`](../glossary.md)

Link a term in prose as `[**term**](#gl:<anchor>)`. The current anchors are
`system, model, parameter, variable, equilibrium, feedback, gradient, threshold,
network, dynamics, emergence, regulation, boundary, state, observable`.

## Step 6 — Add a Reference

Citations are `[@key]` and must resolve in [`references.bib`](../references.bib).
Add a BibTeX entry, then cite it. Keep `CITATION_KEYS` in `constants.py` in sync
if you add a key that the structural contract should track.

## Step 7 — Audit and Test

Two gates decide whether the book is healthy:

```bash
# Quality gate: counts stubs, checks the content contract per file
uv run python scripts/audit_textbook_quality.py

# Full test suite (engine + manuscript integrity)
uv run --extra dev python -m pytest
```

`tests/test_manuscript_integrity.py` verifies that every chapter satisfies the
content contract, that labels are unique, that citations resolve, and that
glossary links point at real anchors. Green tests with remaining stubs mean the
**structure** is correct but the **content** is unfinished — that is the normal
state of a freshly scaffolded chapter.

## Growing the Book

To add a whole new chapter end-to-end:

1. add its `stem`/`title` under the right part in `config.yaml`;
2. add matching lab and question-bank entries under `appendices`;
3. run `scripts/scaffold_chapter.py`;
4. fill the stubs (Steps 3–6);
5. run the audit and tests until the contract passes.

<!-- STUB: project-specific authoring notes — house style, citation policy,
figure conventions — go here once you adopt the template. -->

See also: [Appendix B — Notation](appendix_notation.md),
[Appendix C — Mathematical Review](appendix_math_review.md), and the
[appendices README](README.md).
