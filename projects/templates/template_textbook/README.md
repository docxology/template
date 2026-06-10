# The Template Textbook — Modular, Fillable Book Scaffold

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20533125.svg)](https://zenodo.org/record/20533126)

A domain-neutral exemplar that demonstrates the **book-length manuscript** shape
for this research-template monorepo: a data-driven manuscript (parts → chapters →
labs → question banks), a tested computational backbone under `src/`,
deterministic figure and diagram generators, and a content scaffold/validation
engine that lets a future author fill marked stubs out to hundreds or thousands
of pages without drifting from the structural contract.

Everything downstream — the table of contents, chapter auto-numbering, figure
generation, lab/question wiring, and the manuscript-integrity tests — reads a
single source of truth: [`manuscript/config.yaml`](manuscript/config.yaml). To
grow the book you edit that file, then run a thin orchestrator that materialises
the missing stub files in the correct shape.

## When to use this template

Use this template for **book-length manuscripts**: parts → chapters → labs →
question banks declared in a single `config.yaml`, with auto-numbering,
deterministic figure/diagram generation, and structural-contract tests that
keep hundreds of pages from drifting. For a single-paper computational
project see [`template_code_project`](../template_code_project/); for
editorial/prose review see
[`template_prose_project`](../template_prose_project/). Full roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## What this template is

- **Modular.** Structure is declared in YAML, not hand-numbered. Add a part or a
  chapter in `config.yaml` and the numbering, TOC labels, lab, and question bank
  all follow.
- **Fillable.** Every generated chapter ships as a structurally-complete stub:
  labelled headings, a figure with alt text, a Study Blueprint, Learning
  Objectives, a worked formalism (equation + parameter table), an inline Mermaid
  diagram, and Summary / Key Terms / Further Reading / Practice sections. An
  author fills the prose between the markers.
- **Reproducible.** Figures and diagrams come from deterministic Python (fixed
  seeds, headless matplotlib). The same inputs always produce the same outputs.
- **Tested.** The computational backbone and the structural contract are both
  enforced by a no-mocks test suite at ≥90% coverage.

## Directory map

```
template_textbook/
├── manuscript/
│   ├── config.yaml            # SINGLE SOURCE OF TRUTH (parts → chapters)
│   ├── references.bib         # citation keys ([@key] must resolve here)
│   ├── glossary.md            # glossary anchors ([**term**](#gl:anchor))
│   ├── part_0/ … part_III/    # one .md per chapter; parts & chapters declared in config.yaml
│   ├── labs/<part>/           # one lab per chapter (lab_<stem>.md)
│   ├── questions/<part>/      # one question bank per chapter (q_<stem>.md)
│   ├── appendices/            # reference appendices
│   └── assets/                # cover and static assets
├── src/
│   ├── textbook/              # config, toc, content engine, constants, models
│   ├── visualization/         # deterministic matplotlib figures
│   ├── mermaid/               # Mermaid sources (PNG or .mmd fallback)
│   └── textbook_*.py          # paths, io, logging, visuals utilities
├── scripts/                   # thin orchestrators (figures, diagrams, analysis, scaffold, audit)
├── tests/                     # no-mocks suite incl. test_manuscript_integrity.py
└── pyproject.toml             # project config (90% coverage gate)
```

The four parts are: **Part 0** Orientation and Methods, **Part I** Fundamentals,
**Part II** Core Systems, **Part III** Applications and Synthesis — twelve
chapters in all.

## Quick start

All commands assume `uv` (never `pip`/`npm`). Run them from the monorepo root.

```bash
# 1. Install dependencies for the workspace
uv sync

# 2. Materialise any missing stub files declared in config.yaml
uv run python projects/templates/template_textbook/scripts/scaffold_chapter.py

# 3. Generate deterministic figures and diagrams
uv run python projects/templates/template_textbook/scripts/generate_figures.py
uv run python projects/templates/template_textbook/scripts/generate_diagrams.py

# 4. Run the test suite with coverage (must collect >0 tests, ≥90% coverage)
#    From the monorepo root, `dev` is a default dependency-group (plain `uv run`);
#    the `--extra dev` form only works from inside the project dir.
uv run python -m pytest projects/templates/template_textbook/tests/ \
  --cov=projects/templates/template_textbook/src --cov-fail-under=90

# 5. Audit the manuscript against the structural contract
uv run python projects/templates/template_textbook/scripts/audit_textbook_quality.py
```

> Exit code 0 alone is not proof: confirm the suite collected more than zero
> tests and that coverage met the floor.

## How to grow the book

The workflow is always **edit config, then scaffold**:

1. Open [`manuscript/config.yaml`](manuscript/config.yaml) and add a chapter under
   the relevant part (a `file:` + `title:` entry), or add a whole new part with
   its `id`, `title`, `label`, `directory`, and `chapters`.
2. Run `scripts/scaffold_chapter.py`. It reads the config and writes any missing
   chapter, lab, and question-bank stub in the contract-compliant shape. Existing
   files are left untouched.
3. Fill the prose between the stub markers (`<!-- STUB -->`, `TODO:`, `TKTK`).
   Keep the labelled headings, the figure/equation/table cross-references, and the
   curriculum scaffold intact.
4. Regenerate figures/diagrams if you added new ones, then run the tests and the
   audit. Both must pass before rendering.

Because structure is declared once in YAML, the book can scale from this 12-chapter
skeleton to an arbitrarily large work without renumbering anything by hand.

## The design in one paragraph

`config.yaml` declares the structure. `src/textbook/` turns that declaration into
numbering (`toc.py`), validation and scaffolding (`content.py`), the structural
contract (`constants.py`), and worked formalisms (`models.py`). `scripts/` are
**thin orchestrators**: they import tested methods from `src/`, handle I/O and
visualization, and never implement business logic themselves. `tests/` enforce
both the math and the manuscript contract with real data and no mocks.

## Documentation map

| Document | Read it for |
| --- | --- |
| **This file (`README.md`)** | Overview, directory map, quick-start commands, how to grow the book |
| [`AGENTS.md`](AGENTS.md) | Agent-facing reference: invariants, editing checklist, frozen vs. fillable files |
| [`manuscript/config.yaml`](manuscript/config.yaml) | The single source of truth for book structure |
| Monorepo [`README.md`](https://github.com/docxology/template/blob/main/README.md) / [`CLAUDE.md`](https://github.com/docxology/template/blob/main/CLAUDE.md) / [`AGENTS.md`](https://github.com/docxology/template/blob/main/AGENTS.md) | Pipeline semantics, CI parity, two-layer architecture |

## Worked exemplars vs. stubs

Two chapters are filled to completion as **finished-prose references** — copy
their shape when filling the rest:

- [`manuscript/part_I/first_principles.md`](manuscript/part_I/first_principles.md) — a *model-derivation* chapter (logistic growth, worked numbers from `textbook.models`).
- [`manuscript/part_III/case_studies.md`](manuscript/part_III/case_studies.md) — a *data-driven case study* (grouping, a fit, and honest limits).

Every other chapter ships as a structurally-complete **stub** (marked with
`<!-- STUB -->` / `TODO:`). The appendices
[`appendix_format_gallery.md`](manuscript/appendices/appendix_format_gallery.md)
and [`appendix_formalisms.md`](manuscript/appendices/appendix_formalisms.md)
demonstrate every content primitive and every formal element.

## Output formats

The book renders to **PDF, HTML, EPUB, and DOCX** (`render.formats` in
`config.yaml`). Diagrams embed as images when a Chrome binary is reachable by
`mmdc` (see [`docs/visualization_guide.md`](docs/visualization_guide.md)).

## License

Dual-licensed: **code** (`src/`, `scripts/`, `tests/`) under **Apache-2.0**
([`LICENSE`](LICENSE)); **manuscript content** (`manuscript/`) under
**CC BY 4.0** ([`LICENSE-CONTENT.md`](LICENSE-CONTENT.md)). See also
[`CHANGELOG.md`](CHANGELOG.md).
