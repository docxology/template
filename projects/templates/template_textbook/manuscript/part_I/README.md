# Part I — Fundamentals

> **Theme.** Establish the irreducible ideas the rest of the book builds on:
> the first principles of the field, the smallest reusable building blocks, and
> how those blocks combine into structure and form. Part I is where a reader
> first meets the vocabulary, the core formalism, and the patterns that Parts II
> and III then put to work.

This directory holds the three chapters of Part I. The part, its title, and its
chapter order are **not** defined here — they are read from
[`../config.yaml`](../config.yaml) (`parts:` → `part_I`). This README is a
human-facing index; edit `config.yaml` to change the structure, then run
`scripts/scaffold_chapter.py` to materialise any missing stub files.

Chapters number sequentially across the whole book, so the numbers shown by the
renderer depend on how many chapters precede Part I in `config.yaml`. Never
hand-number a chapter, figure, equation, table, or section: use pandoc-crossref
references (`[@sec:…]`, `[@fig:…]`, `[@eq:…]`, `[@tbl:…]`) and let the build
resolve them.

## Chapters

Each chapter ships as a **stub** carrying the full authoring skeleton (labelled
H1, metadata badge, Study Blueprint, Learning Objectives, a worked formalism,
an inline `mermaid` diagram, a figure, and the Summary / Key Terms / Further
Reading / Practice sections). Stub markers (`<!-- STUB -->`, `TODO:`, `TKTK`)
flag the prose a future author must replace. See
[`AGENTS.md`](AGENTS.md) for the per-chapter contract and the
[Authoring Guide appendix](../appendices/appendix_authoring_guide.md) for the fill workflow.

| # | Chapter | Stub description | Chapter | Lab | Questions |
|---|---------|------------------|---------|-----|-----------|
| 1 | **First Principles** | The starting axioms and definitions of the field; what is assumed, what is derived, and why. | [`first_principles.md`](first_principles.md) | [lab](../labs/part_I/lab_first_principles.md) | [bank](../questions/part_I/q_first_principles.md) |
| 2 | **Building Blocks** | The smallest reusable units — the components every later model is assembled from. | [`building_blocks.md`](building_blocks.md) | [lab](../labs/part_I/lab_building_blocks.md) | [bank](../questions/part_I/q_building_blocks.md) |
| 3 | **Structure and Form** | How building blocks compose into larger structures, and the patterns that recur across scales. | [`structure_and_form.md`](structure_and_form.md) | [lab](../labs/part_I/lab_structure_and_form.md) | [bank](../questions/part_I/q_structure_and_form.md) |

## How Part I fits together

- **First Principles** fixes the assumptions and the core formalism (the worked
  equation a reader can compute by hand).
- **Building Blocks** names the reusable units those principles produce.
- **Structure and Form** shows the units composing into structure — the bridge
  into Part II ("Core Systems").

## Editing this part

1. **Change the structure** in [`../config.yaml`](../config.yaml) — add, reorder,
   or disable a chapter (`enabled: false` skips without deleting).
2. **Materialise stubs** with `scripts/scaffold_chapter.py`, which writes any
   missing chapter, lab, and question file in the correct shape.
3. **Fill the prose**, replacing every stub marker; keep all cross-references,
   citations (`[@key]` resolving in [`../references.bib`](../references.bib)), and
   glossary links (`[**term**](#gl:…)`).
4. **Verify** with `scripts/audit_textbook_quality.py` and the manuscript
   integrity tests (`uv run --extra dev python -m pytest`).
