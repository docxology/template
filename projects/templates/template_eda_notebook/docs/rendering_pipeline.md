# Rendering Pipeline: Manuscript → PDF

The `manuscript/` directory contains the narrative components of the research. It
is compiled into a publication-ready PDF by the template's rendering
infrastructure. This document describes each step, what it produces, and how to
troubleshoot failures.

## Prerequisite: Mermaid diagrams need `chrome-headless-shell`

Several docs and manuscript sections embed ```mermaid``` blocks. Any block that
reaches the **combined PDF** is rasterised by `mmdc` (mermaid-cli), which drives
a **pinned** `chrome-headless-shell` via Puppeteer. If that Chrome build is
absent from `~/.cache/puppeteer/`, the combined-PDF step fails with:

```
mmdc failed for inline_mermaid_0001_...: Could not find Chrome (ver. X)
```

Install it once (CI provisions it automatically; a fresh local clone does not):

```bash
npx --yes puppeteer browsers install chrome-headless-shell
```

Per-section slide PDFs do **not** invoke `mmdc`, so "slides render but the
combined PDF fails" is the signature of this missing dependency.

## The Flow

The pipeline has three steps. Each must complete before the next begins.

### 1. Analysis

**Script**: `scripts/eda_analysis.py` (from the repository root)

```bash
uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
```

**Inputs**: `data/measurements.csv` + the tested functions in `src/eda/`.

**Outputs**:

| File | Location | Content |
|---|---|---|
| `height_histogram.png` | `output/figures/` | Height distribution |
| `correlation_heatmap.png` | `output/figures/` | Feature correlation heatmap |
| `group_counts.png` | `output/figures/` | Rows per group |
| `figure_registry.json` | `output/figures/` | Labels, filenames, captions, and qualified generators for all three PNGs |
| `summary_statistics.csv` | `output/data/` | Per-column descriptive statistics |

### 2. PDF render

**Script**: `scripts/pipeline/stage_03_render.py` (at the repository root, **not** inside
`projects/`)

```bash
uv run python scripts/pipeline/stage_03_render.py --project templates/template_eda_notebook
```

**Inputs**: `manuscript/*.md` + `manuscript/config.yaml` + `manuscript/preamble.md`
+ `manuscript/references.bib`.

**Infrastructure modules involved**:

| Module | Role |
|---|---|
| `infrastructure/rendering/pdf_renderer.py` | Orchestrates Pandoc → XeLaTeX |
| `infrastructure/rendering/manuscript_discovery.py` | Discovers and orders manuscript section files |
| `infrastructure/core/config/loader.py` | Reads `manuscript/config.yaml` for title, authors, metadata |

**Outputs**: a combined publication PDF, per-section Beamer slides, and HTML
versions of each section, all under `output/`.

### 3. Copy deliverables

**Script**: `scripts/pipeline/stage_05_copy.py` (at the repository root)

```bash
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_eda_notebook
```

**Output**: final PDF and figures copied to the repo-level
`output/templates/template_eda_notebook/` tree (used by CI artifact upload).

## config.yaml Controls

| YAML Key | Controls | Consumed by |
|---|---|---|
| `paper.title` | PDF title page and page headers | `infrastructure/core/config/loader.py` → `pdf_renderer.py` |
| `paper.version` | Title page version | `pdf_renderer.py` |
| `authors[*]` | Author list on the title page | `pdf_renderer.py` |
| `publication.doi` | DOI on the title page and citations | `pdf_renderer.py` |
| `keywords` | Keyword metadata | `pdf_renderer.py` |
| `render.formats.*` | Which output formats are produced | `infrastructure/rendering/config.py` |

## Troubleshooting

### Missing figure in PDF

**Cause**: the analysis script did not generate one or more figures.

```bash
ls projects/templates/template_eda_notebook/output/figures/*.png
uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
```

### BibTeX citation error / PDF fails to compile

**Cause**: malformed entry in `manuscript/references.bib`. Check the LaTeX log
under `output/pdf/` for the specific error.

### Slides not generated

**Cause**: `scripts/pipeline/stage_03_render.py` needs Pandoc with Beamer support.

```bash
pandoc --version
```
