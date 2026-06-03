# Part 0 — Orientation and Methods

> **Theme.** Orientation and Methods is the on-ramp to the book. Before any
> domain content, it sets out *how the field thinks*: where the subject sits,
> which methods and tools the rest of the book leans on, and the quantitative
> backbone (units, estimates, simple models, basic statistics) that later parts
> assume the reader already carries. Fill these three chapters first — the
> vocabulary, notation, and worked formalisms you establish here propagate
> forward into Parts I–III.

This part is **data-driven from [`../config.yaml`](../config.yaml)**. Its title,
label (`0`), directory, and the chapter list below all come from the `parts:`
block of that file. To change the structure, edit the config and run
[`scripts/scaffold_chapter.py`](../../scripts/scaffold_chapter.py) to materialise
any missing stub files in the correct shape — do not add chapters by hand.

## Chapters in this part

Each chapter ships as a stub that satisfies the structural contract (see
[`AGENTS.md`](AGENTS.md)) and is waiting for an author to fill it. Every chapter
is paired with a hands-on **lab** and a **question bank**.

| # | Chapter | What the stub covers (fill this in) | Lab | Questions |
|---|---------|-------------------------------------|-----|-----------|
| 1 | [Orientation to the Field](orientation.md) | Stub: situates the subject — scope, key questions, the map of the rest of the book, and why the field matters. | [Lab](../labs/part_0/lab_orientation.md) | [Bank](../questions/part_0/q_orientation.md) |
| 2 | [Core Methods and Tools](core_methods.md) | Stub: the working toolkit — methods, conventions, software, and reproducible-workflow habits the book relies on. | [Lab](../labs/part_0/lab_core_methods.md) | [Bank](../questions/part_0/q_core_methods.md) |
| 3 | [Quantitative Foundations](quantitative_foundations.md) | Stub: units and dimensions, order-of-magnitude estimation, simple models, and the descriptive statistics later chapters assume. | [Lab](../labs/part_0/lab_quantitative_foundations.md) | [Bank](../questions/part_0/q_quantitative_foundations.md) |

Chapters number sequentially across the whole book; chapter numbers shown here
are within-part positions and are assigned at render time by
[`src/textbook/toc.py`](../../src/textbook/toc.py). Never hand-number — let
pandoc-crossref and the TOC engine do it.

## How to fill this part

1. Open a chapter stub and read its `<!-- STUB -->`, `TODO:`, and `TKTK` markers.
2. Replace each placeholder while keeping the required structure (labelled H1,
   figure with alt text, metadata badge, Study Blueprint, Learning Objectives,
   worked formalism + parameter table, inline `mermaid` diagram, and the
   Summary / Key Terms / Further Reading / Practice sections).
3. Wire its figure with [`scripts/generate_figures.py`](../../scripts/generate_figures.py)
   (filename convention `part_0_<stem>.png`) and any diagram with
   [`scripts/generate_diagrams.py`](../../scripts/generate_diagrams.py).
4. Cross-link to the matching **lab** and **question bank** as you go.
5. Run the gate: [`scripts/audit_textbook_quality.py`](../../scripts/audit_textbook_quality.py)
   and `uv run --extra dev python -m pytest`.

See the per-chapter contract in [`AGENTS.md`](AGENTS.md), the repo-wide
[Authoring Guide](../appendix_authoring_guide.md), and the
[Master Glossary](../glossary.md).
