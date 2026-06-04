# Manuscript Directory

This directory holds the **content** of the textbook — the Markdown the renderer
turns into a PDF. Everything here is driven by one file, [`config.yaml`](config.yaml),
which is the single source of truth for the book's structure.

## Layout

```
manuscript/
├── config.yaml          # THE single source of truth: parts, chapters, front
│                        #   matter, appendices, labs, question banks, layout,
│                        #   typography, numbering. Edit this to grow the book.
├── front_matter.md      # Dedication, "About This Template", navigation guide
├── preface.md           # Preface STUB (purpose, audience, how to use the book)
├── preamble.md          # LaTeX preamble (packages, margins) — fenced ```latex
├── references.bib       # BibTeX database; every [@key] must resolve here
├── glossary.md          # Master glossary; anchors {#gl:...} for [**term**] links
├── part_0/              # Orientation and Methods   (3 chapters)
├── part_I/              # Fundamentals              (3 chapters)
├── part_II/             # Core Systems              (3 chapters)
├── part_III/            # Applications and Synthesis(3 chapters)
├── labs/                # One guided lab per chapter, grouped by part
│   ├── part_0/  part_I/  part_II/  part_III/
├── questions/           # One question bank per chapter, grouped by part
│   ├── part_0/  part_I/  part_II/  part_III/
├── appendices/          # Authoring guide, notation, math review, index
└── assets/              # Cover image and other static assets
```

Each chapter file lives under `part_<label>/<stem>.md`. Its companion lab is
`labs/<part>/lab_<stem>.md` and its companion question bank is
`questions/<part>/q_<stem>.md`. These names are not arbitrary — they are derived
from `config.yaml`, and `scripts/scaffold_chapter.py` will materialise any
missing file in exactly the right shape.

## How `config.yaml` Controls Everything

| You change in `config.yaml`… | …and this updates automatically |
| --- | --- |
| `parts:` (add/remove a chapter) | Table of contents, chapter numbers, integrity tests |
| `appendices.labs` / `.questions` | Which labs and banks are included and titled |
| `front_matter.files` | Front-matter order and titles |
| `rendering.number_*` | Whether chapters/figures/equations/tables are numbered |
| `layout` / `typography` | Page geometry, fonts, link colour |

You never hand-number anything. Figures, tables, equations, sections, labs, and
question banks are referenced by **label** (e.g. `[@fig:part_0_orientation]`) and
numbered at render time by `pandoc-crossref`. See [`SYNTAX.md`](SYNTAX.md).

## Render Flow

The PDF is built, not typeset by hand. From the repository root:

```bash
# 1. Generate figures and diagrams (the analysis stage; deterministic)
uv run python scripts/02_run_analysis.py --project templates/template_textbook

# 2. Render the manuscript to PDF (Pandoc + pandoc-crossref, multiple passes)
uv run python scripts/03_render_pdf.py --project templates/template_textbook
```

Or run the full pipeline interactively with `./run.sh`. The renderer reads
`config.yaml`, assembles the front matter, parts, chapters, appendices, labs, and
question banks in declared order, resolves cross-references and citations, and
writes the PDF to `output/templates/template_textbook/pdf/`.

> **Tip:** a single render pass leaves cross-references and citations showing as
> `??`. The full pipeline runs the multiple LaTeX passes (plus BibTeX) needed to
> resolve them — prefer it for a final check.

## Validating as You Write

```bash
# Structural contract + stub accounting
uv run python scripts/audit_textbook_quality.py --project templates/template_textbook

# Manuscript-integrity tests (headings, labels, citations, glossary anchors)
uv run --extra dev python -m pytest projects/templates/template_textbook/tests/test_manuscript_integrity.py -v

# Markdown validation
uv run python -m infrastructure.validation.cli markdown projects/templates/template_textbook/manuscript/
```

For the full editing contract see [`AGENTS.md`](AGENTS.md); for the authoring
walkthrough see [`appendices/appendix_authoring_guide.md`](appendices/appendix_authoring_guide.md).
