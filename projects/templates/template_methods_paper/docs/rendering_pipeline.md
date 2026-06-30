# Rendering Pipeline: Manuscript → PDF

The `manuscript/` directory contains the narrative components of the
research. It is compiled into a publication-ready PDF by the template's
rendering infrastructure. This document describes each step, what it
produces, and how to troubleshoot failures.

## Prerequisite: Mermaid diagrams need `chrome-headless-shell`

Several docs and manuscript sections embed ```mermaid``` blocks. Any block
that reaches the **combined PDF** is rasterised by `mmdc` (mermaid-cli),
which drives a **pinned** `chrome-headless-shell` via Puppeteer. If that
Chrome build is absent from `~/.cache/puppeteer/`, the combined-PDF step
fails with:

```
mmdc failed for inline_mermaid_0001_...: Could not find Chrome (ver. X)
```

Install it once (CI provisions it automatically; a fresh local clone does
not):

```bash
npx --yes puppeteer browsers install chrome-headless-shell
```

Per-section slide PDFs do **not** invoke `mmdc`, so "slides render but the
combined PDF fails" is the signature of this missing dependency.

## The Flow

The pipeline has four steps. Each must complete before the next begins.

### 1. Analysis

**Script**: `scripts/methods_analysis.py` (from the repository root)

```bash
uv run python projects/templates/template_methods_paper/scripts/methods_analysis.py
```

**Inputs**: `src/methods_dsl/examples_methods.py`'s worked example methods +
the tested gate/compiler/exporter functions in `src/methods_dsl/`.

**Outputs**:

| File | Location | Content |
|---|---|---|
| `*_worklist.md`, `*_plan.csv`, `*_graph.mmd`, `*_plan.json` (per method) | `output/data/` | Per-method exported plan |
| `compiled_plans.json` | `output/data/` | Per-method plan summary |
| `gate_report.json` | `output/reports/` | Staged-gate tally |
| `trust_chain_report.json` | `output/reports/` | Provenance hash-chain demo result |
| `step_counts.png` | `output/figures/` | Steps per example method |

### 2. Manuscript variable generation

**Script**: `scripts/z_generate_manuscript_variables.py` (from the
repository root)

```bash
uv run python projects/templates/template_methods_paper/scripts/z_generate_manuscript_variables.py
```

**Inputs**: `manuscript/config.yaml` + the `output/data` and `output/reports`
artifacts from step 1.

**Outputs**: `output/data/manuscript_variables.json` and a
`{{TOKEN}}`-resolved manuscript tree consumed by step 3.

### 3. PDF render

**Script**: `scripts/03_render_pdf.py` (at the repository root, **not**
inside `projects/`)

```bash
uv run python scripts/03_render_pdf.py --project templates/template_methods_paper
```

**Inputs**: `manuscript/*.md` (resolved) + `manuscript/config.yaml` +
`manuscript/preamble.md` + `manuscript/references.bib`.

**Infrastructure modules involved**:

| Module | Role |
|---|---|
| `infrastructure/rendering/pdf_renderer.py` | Orchestrates Pandoc → XeLaTeX |
| `infrastructure/rendering/manuscript_discovery.py` | Discovers and orders manuscript section files |
| `infrastructure/rendering/manuscript_injection.py` | Resolves `{{TOKEN}}` markers via `write_resolved_manuscript_tree` |
| `infrastructure/core/config/loader.py` | Reads `manuscript/config.yaml` for title, authors, metadata |

**Outputs**: a combined publication PDF, per-section Beamer slides, and HTML
versions of each section, all under `output/`.

### 4. Copy deliverables

**Script**: `scripts/05_copy_outputs.py` (at the repository root)

```bash
uv run python scripts/05_copy_outputs.py --project templates/template_methods_paper
```

**Output**: final PDF and figures copied to the repo-level
`output/templates/template_methods_paper/` tree (used by CI artifact
upload).

## config.yaml Controls

| YAML Key | Controls | Consumed by |
|---|---|---|
| `paper.title` | PDF title page and page headers | `infrastructure/core/config/loader.py` → `pdf_renderer.py` |
| `paper.version` | Title page version; `{{CONFIG_VERSION}}` | `pdf_renderer.py`, `src/manuscript_variables.py` |
| `authors[*]` | Author list on the title page; `{{CONFIG_FIRST_AUTHOR}}` | `pdf_renderer.py`, `src/manuscript_variables.py` |
| `publication.doi` | DOI on the title page and citations | `pdf_renderer.py` |
| `keywords` | Keyword metadata; `{{CONFIG_KEYWORDS}}` | `pdf_renderer.py`, `src/manuscript_variables.py` |
| `render.formats.*` | Which output formats are produced | `infrastructure/rendering/config.py` |

## Troubleshooting

### Missing figure in PDF

**Cause**: the analysis script did not generate the figure.

```bash
ls projects/templates/template_methods_paper/output/figures/*.png
uv run python projects/templates/template_methods_paper/scripts/methods_analysis.py
```

### Unresolved `{{TOKEN}}` warning

**Cause**: a manuscript file references a token `generate_variables()` does
not emit, or the analysis step (step 1) was skipped so `require_analysis_outputs`
fallbacks to `N/A`. Run step 1, then step 2, in order — never skip step 1.

### BibTeX citation error / PDF fails to compile

**Cause**: malformed entry in `manuscript/references.bib`. Check the LaTeX
log under `output/pdf/` for the specific error.

### Slides not generated

**Cause**: `scripts/03_render_pdf.py` needs Pandoc with Beamer support.

```bash
pandoc --version
```
