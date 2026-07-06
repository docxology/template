# Front Matter

<!-- This file is the first front-matter document rendered (see
`manuscript/config.yaml` → `front_matter.files`). It carries the dedication,
an explanation of what this template is, a reader navigation guide, and a short
note on how the book is generated. Replace the STUB content with your own. -->

## Dedication

<!-- STUB: dedication --> *TKTK — dedicate this book to whom you choose. One or
two lines is conventional. Delete this comment and the placeholder once written.*

---

## About This Template

This is **not a finished book**. It is a *scaffold* — a complete, internally
consistent skeleton for a book-length technical work, with every structural
element in place and every author-specific passage left as a marked **stub** for
you to fill.

The whole book is **data-driven from a single source of truth**,
[`config.yaml`](config.yaml). That file declares the parts, the chapters inside
each part, the front matter, the appendices, and the labs and question banks. The
table of contents, chapter numbering, figure numbering, and the
manuscript-integrity tests all read from it. You grow the book by editing
`config.yaml` and then materialising any missing files — you never hand-number a
chapter, figure, equation, or table.

What is already provided for you:

- **Twelve chapters** across four parts, each a valid chapter shell with a
  labelled heading, a figure, a metadata badge, a Study Blueprint, Learning
  Objectives, a worked formalism (equation + parameter table), an inline Mermaid
  diagram, and Summary / Key Terms / Further Reading / Practice sections.
- **A matching lab and question bank** for every chapter, under
  [`labs/`](labs/) and [`questions/`](questions/).
- **A tested computational backbone** in `src/` — the worked equations are real,
  tested Python functions (`textbook.models`), and figures are generated
  deterministically. Chapter prose *calls* these functions rather than retyping
  the mathematics.
- **A test gate** (`tests/test_manuscript_integrity.py` plus
  `scripts/audit_textbook_quality.py`) that checks the structural contract holds
  as you write.

Everywhere author-specific content belongs, you will find a stub marker:
`<!-- STUB -->`, `TODO:`, or `TKTK`. The quality audit counts these, so your
progress toward a finished book is measurable. See
[Appendix A — Authoring Guide](appendices/appendix_authoring_guide.md) and
[`AGENTS.md`](AGENTS.md) for the full filling workflow.

---

## How to Read This Book

The book is organised into four parts that build on one another. A first-time
reader should move through them in order; an instructor can assign parts
independently.

- **Part 0 — Orientation and Methods.** Where the field sits, the core methods
  and tools, and the quantitative foundations the rest of the book assumes. Start
  here even if you are experienced; it fixes notation and conventions.
- **Part I — Fundamentals.** First principles, the building blocks, and how
  structure and form arise. The conceptual bedrock.
- **Part II — Core Systems.** A systems overview, dynamics and change, and
  regulation and control. The working theory.
- **Part III — Applications and Synthesis.** Applied models, case studies, and
  frontiers with open problems. Where the ideas meet practice and the edge of
  what is known.

Each chapter ends with a **Practice** section pointing to its **lab** (a guided,
hands-on exercise) and its **question bank** (self-check questions). Work the lab
after reading; use the question bank to confirm you can recall and apply the
material. New terms are linked to the [Master Glossary](glossary.md) the first
time they appear.

---

## Methodology: How This Book Is Generated

This manuscript is rendered, not typeset by hand. The pipeline reads
[`config.yaml`](config.yaml), runs the analysis scripts that produce figures and
diagrams, assembles the Markdown sections in declared order, and renders a PDF
through Pandoc with `pandoc-crossref` resolving every cross-reference and
citation.

To build the book from the repository root:

```bash
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_textbook
uv run python scripts/pipeline/stage_03_render.py    --project templates/template_textbook
```

or run the full pipeline with `./run.sh`. See [`README.md`](README.md) for the
manuscript directory layout and [`SYNTAX.md`](SYNTAX.md) for the exact authoring
syntax.

<!-- STUB: add a copyright line, ISBN, and edition statement here at
publication time. The licence and edition are declared in config.yaml. -->
