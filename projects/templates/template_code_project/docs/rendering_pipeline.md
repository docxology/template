# Rendering Pipeline: Manuscript → PDF

The `manuscript/` directory contains the narrative components of the research. It is compiled into a publication-ready PDF automatically by the template's rendering infrastructure. This document describes every step, what it produces, which scripts run it, and how to troubleshoot failures.

## Prerequisite: Mermaid diagrams need `chrome-headless-shell`

This project's convention (`docs/AGENTS.md`) is that **every diagram is
Mermaid**. Any ```mermaid``` block that reaches the **combined PDF** is
rasterised by `mmdc` (mermaid-cli), which drives a **pinned**
`chrome-headless-shell` via Puppeteer. If that Chrome build is absent from
`~/.cache/puppeteer/`, the combined-PDF step — and the whole **PDF
Rendering** pipeline stage — fails with:

```
mmdc failed for inline_mermaid_0001_...: Could not find Chrome (ver. X)
```

Install it once (reversible, one-time per machine; CI provisions it
automatically, a fresh local clone does not):

```bash
npx --yes puppeteer browsers install chrome-headless-shell
# or pin to the exact version mmdc reports as missing:
npx --yes puppeteer browsers install chrome-headless-shell@131.0.6778.204
```

Per-section slide PDFs do **not** invoke `mmdc`, so "slides render but the
combined PDF fails" is the signature of this missing dependency. See
[troubleshooting.md](troubleshooting.md#pdf-rendering-fails-mmdc-could-not-find-chrome).

## The Self-Referential Flow

The pipeline has four steps. Each step must complete before the next begins.

### Analysis

**Script**: `scripts/optimization_analysis.py` (from repository root)

**Command**:
```bash
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
```

**Inputs**: `src/optimizer.py` functions + `manuscript/config.yaml` experiment parameters

**Outputs**:

| File | Location | Content |
|---|---|---|
| `convergence_plot.png` | `output/figures/` | Gradient descent trajectories for each step size |
| `step_size_sensitivity.png` | `output/figures/` | Dense sensitivity sweep across step sizes |
| `convergence_rate_comparison.png` | `output/figures/` | Error decay curves (log scale) |
| `algorithm_complexity.png` | `output/figures/` | Dimensional scaling behavior |
| `performance_benchmark.png` | `output/figures/` | Wall time and iteration counts across dimensions |
| `stability_analysis.png` | `output/figures/` | Heatmap of stability across (x₀, α) grid |
| `optimization_results.csv` | `output/data/` | Per-step-size convergence results table |
| `stability_analysis.json` | `output/reports/` | Aggregate stability score and per-cell results |
| `performance_benchmark.json` | `output/reports/` | Timing results per dimension |
| `dashboard.html` | `output/web/` | Plotly interactive dashboard (`build_dashboard.py`) |
| `optimization_metadata.json` | `output/citations/` | DOI, author, keyword metadata for citation tools |

### Manuscript variables

**Script**: `scripts/z_generate_manuscript_variables.py` (thin orchestrator; logic lives in `src/manuscript_variables.py`)

**Command**:
```bash
uv run python projects/templates/template_code_project/scripts/z_generate_manuscript_variables.py
```

**Inputs**: `manuscript/config.yaml` + `output/data/optimization_results.csv` + `output/reports/*.json`

**What it does**: Calls `src/manuscript_variables.py::generate_variables(..., require_analysis_outputs=True)` (default) to compute all token values, then calls `infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree()` to write substituted copies of `manuscript/*.md` to `output/manuscript/`. It also writes the full mapping to `output/data/manuscript_variables.json`.

**Strict default**: Fails with `FileNotFoundError` when `output/data/optimization_results.csv` is missing. Use `--allow-draft` only for intentional early drafts that may emit `"N/A"` for result-derived tokens.

**Critical**: ALL `{{VARIABLE}}` tokens must resolve to non-empty strings before PDF render. If any token is unresolved, the literal `{{TOKEN_NAME}}` string will appear in the rendered PDF.

**Outputs**:
- `output/manuscript/*.md` — substituted copies of all 8 manuscript sections
- `output/data/manuscript_variables.json` — complete `{ "TOKEN": "value" }` mapping

### PDF render

**Script**: `scripts/03_render_pdf.py` (at repository root, **not** inside `projects/`)

**Command**:
```bash
uv run python scripts/03_render_pdf.py --project template_code_project
```

**Inputs**: `output/manuscript/*.md` (substituted) + `manuscript/config.yaml` + `manuscript/preamble.md` + `manuscript/references.bib`

When `publication.transmission_bookends.enabled: true`, the combined PDF also includes generated `00_00_transmission_begin.md` and `99_zz_transmission_end.md` (compact metadata, dual-row integrity strip, `transmission_manifest.json`, prior releases capped at three rows on the end page). Verify single-page fit: `uv run python -m infrastructure.publishing.transmission_page_check projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf`. After render, run `uv run python -m infrastructure.orchestration secure --steganography-only --project template_code_project --deterministic` for the hardened `*_steganography.pdf` and `.hashes.json` manifest; the Python `secure` subcommand owns `--deterministic`. See [`docs/guides/publishing-guide.md`](../../../../docs/guides/publishing-guide.md#transmission-bookends-optional).

Zenodo and GitHub uploads use a metadata-driven basename from `publication.deposit_filename` (e.g. `Author_2026_Convergence_b591a0ce.pdf`); the local working file remains `template_code_project_combined.pdf`. See [Deposit upload filename](../../../../docs/guides/publishing-guide.md#deposit-upload-filename).

**Infrastructure modules involved**:

| Module | Role |
|---|---|
| `infrastructure/rendering/pdf_renderer.py` | Orchestrates Pandoc → XeLaTeX pipeline |
| `infrastructure/rendering/_pdf_latex_helpers.py` | LaTeX package validation and preamble injection |
| `infrastructure/rendering/manuscript_discovery.py` | Discovers and orders manuscript section files |
| `infrastructure/core/config/loader.py` | Reads `manuscript/config.yaml` for title, authors, metadata |

**Outputs**:
- `projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf` — working publication PDF
- `output/template_code_project/pdf/template_code_project_combined.pdf` — copied final publication PDF after Stage 07
- `projects/templates/template_code_project/output/pdf/_combined_manuscript.*` — LaTeX intermediates (`.tex`, `.aux`, `.log`)
- `projects/templates/template_code_project/output/slides/` — per-section Beamer slide PDFs (one per manuscript section)
- `projects/templates/template_code_project/output/web/` — HTML versions of each section

### Copy deliverables

**Script**: `scripts/05_copy_outputs.py` (at repository root)

**Command**:
```bash
uv run python scripts/05_copy_outputs.py --project template_code_project
```

**Output**: Final PDF and figures copied to `output/template_code_project/` at the repository root (used by CI artifact upload and the multi-project executive report).

## config.yaml Controls

| YAML Key | Controls | Consumed by |
|---|---|---|
| `paper.title` | PDF title page and page headers | `infrastructure/core/config/loader.py` → `pdf_renderer.py` |
| `paper.version` | `{{CONFIG_VERSION}}` token | `src/manuscript_variables.py` |
| `authors[*]` | Author list on title page | `pdf_renderer.py` + `{{CONFIG_FIRST_AUTHOR}}` |
| `publication.doi` | DOI on title page and citations | `pdf_renderer.py` |
| `keywords` | `{{CONFIG_KEYWORDS}}` count | `src/manuscript_variables.py` |
| `experiment.*` | Step sizes, tolerances, A/b, stability/benchmark grids | `src/experiment_config.py::load_experiment_config()` → `analysis/`, `figures/`, `dashboard.py`, `manuscript_variables.py` |
| `llm.translations.enabled` | Whether to run LLM translation step | `execute_pipeline.py` |

## Troubleshooting

### Unresolved `{{VARIABLE}}` appears in PDF

**Symptom**: The rendered PDF contains literal `{{TOKEN_NAME}}` text.

**Cause**: Manuscript variables (`scripts/z_generate_manuscript_variables.py`) did not run, failed silently, or the token is not defined in `src/manuscript_variables.py::generate_variables()`.

**Fix**:
```bash
# Check whether output/data/manuscript_variables.json exists
ls projects/templates/template_code_project/output/data/manuscript_variables.json

# Re-run manuscript variables
uv run python projects/templates/template_code_project/scripts/z_generate_manuscript_variables.py

# Detect remaining unresolved tokens
grep -r "{{" projects/templates/template_code_project/output/manuscript/ | grep -v ".json"
```

### Missing figure in PDF

**Symptom**: PDF has a broken image placeholder or missing figure reference.

**Cause**: Analysis (`optimization_analysis.py`) failed to generate one or more figures.

**Fix**:
```bash
ls projects/templates/template_code_project/output/figures/*.png
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
```

### BibTeX citation error / PDF fails to compile

**Symptom**: XeLaTeX exits with a BibTeX error or undefined citation key.

**Cause**: Malformed entry in `manuscript/references.bib` (unclosed braces, duplicate keys, missing required fields).

**Fix**: Validate `manuscript/references.bib` with a BibTeX linter or check `projects/templates/template_code_project/output/pdf/_combined_manuscript.log` for the specific error message.

### Slides not generated

**Symptom**: `output/slides/` is empty or missing sections.

**Cause**: `scripts/03_render_pdf.py` requires Pandoc with Beamer support. Check `pandoc --version`.

**Fix**:
```bash
pandoc --version
# If missing: brew install pandoc (macOS) or see docs/operational/error-handling-guide.md
```
