# Rendering Pipeline: Manuscript → PDF

The `manuscript/` directory contains the narrative components of the research. It is compiled into a publication-ready PDF automatically by the template's rendering infrastructure. This document describes every step, what it produces, which scripts run it, and how to troubleshoot failures.

## The Self-Referential Flow

The pipeline has four phases. Each phase must complete before the next begins.

### Phase 1 — Run Analysis

**Script**: `scripts/optimization_analysis.py` (from repository root)

**Command**:
```bash
uv run python projects/code_project/scripts/optimization_analysis.py
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
| `analysis_dashboard.html` | `output/reports/` | HTML dashboard with all metrics |
| `optimization_metadata.json` | `output/citations/` | DOI, author, keyword metadata for citation tools |

### Phase 2 — Generate Manuscript Variables

**Script**: `scripts/z_generate_manuscript_variables.py` (from repository root)

**Command**:
```bash
uv run python projects/code_project/scripts/z_generate_manuscript_variables.py
```

**Inputs**: `manuscript/config.yaml` + `output/data/optimization_results.csv` + `output/reports/*.json`

**What it does**: Reads each `manuscript/*.md` template file, replaces every `{{VARIABLE_NAME}}` token with a computed value, and writes the substituted copy to `output/manuscript/`. It also writes the full mapping to `output/data/manuscript_variables.json`.

**Critical**: ALL `{{VARIABLE}}` tokens must resolve to non-empty strings before Phase 3. If any token is unresolved, the literal `{{TOKEN_NAME}}` string will appear in the rendered PDF.

**Outputs**:
- `output/manuscript/*.md` — substituted copies of all 8 manuscript sections
- `output/data/manuscript_variables.json` — complete `{ "TOKEN": "value" }` mapping

### Phase 3 — Render PDF

**Script**: `scripts/03_render_pdf.py` (at repository root, **not** inside `projects/`)

**Command**:
```bash
uv run python scripts/03_render_pdf.py --project code_project
```

**Inputs**: `output/manuscript/*.md` (substituted) + `manuscript/config.yaml` + `manuscript/preamble.md` + `manuscript/references.bib`

**Infrastructure modules involved**:

| Module | Role |
|---|---|
| `infrastructure/rendering/pdf_renderer.py` | Orchestrates Pandoc → pdflatex pipeline |
| `infrastructure/rendering/_pdf_latex_helpers.py` | LaTeX package validation and preamble injection |
| `infrastructure/rendering/manuscript_discovery.py` | Discovers and orders manuscript section files |
| `infrastructure/core/config_loader.py` | Reads `manuscript/config.yaml` for title, authors, metadata |

**Outputs**:
- `output/pdf/code_project_combined.pdf` — final publication PDF
- `output/tex/` — LaTeX intermediates (`.tex`, `.aux`, `.log`)
- `output/slides/` — Per-section Beamer slide PDFs (one per manuscript section)
- `output/web/` — HTML versions of each section

### Phase 4 — Copy Final Deliverables

**Script**: `scripts/05_copy_outputs.py` (at repository root)

**Command**:
```bash
uv run python scripts/05_copy_outputs.py --project code_project
```

**Output**: Final PDF and figures copied to `output/code_project/` at the repository root (used by CI artifact upload and the multi-project executive report).

## config.yaml Controls

| YAML Key | Controls | Consumed by |
|---|---|---|
| `paper.title` | PDF title page and page headers | `infrastructure/core/config_loader.py` → `pdf_renderer.py` |
| `paper.version` | `{{CONFIG_VERSION}}` token | `z_generate_manuscript_variables.py` |
| `authors[*]` | Author list on title page | `pdf_renderer.py` + `{{CONFIG_FIRST_AUTHOR}}` |
| `publication.doi` | DOI on title page and citations | `pdf_renderer.py` |
| `keywords` | `{{CONFIG_KEYWORDS}}` count | `z_generate_manuscript_variables.py` |
| `experiment.step_sizes` | Drives ALL convergence experiments | `optimization_analysis.py` |
| `experiment.max_iterations` | `{{CONFIG_MAX_ITERATIONS}}` | `z_generate_manuscript_variables.py` |
| `experiment.tolerance` | `{{CONFIG_TOLERANCE}}` | `z_generate_manuscript_variables.py` |
| `experiment.stability_starting_points` | Stability grid rows | `optimization_analysis.py` |
| `experiment.stability_step_sizes` | Stability grid columns | `optimization_analysis.py` |
| `experiment.benchmark_dimensions` | Performance benchmark dimensions | `optimization_analysis.py` |
| `llm.translations.enabled` | Whether to run LLM translation step | `execute_pipeline.py` |

## Troubleshooting

### Unresolved `{{VARIABLE}}` appears in PDF

**Symptom**: The rendered PDF contains literal `{{TOKEN_NAME}}` text.

**Cause**: Phase 2 (`z_generate_manuscript_variables.py`) did not run, failed silently, or the token is not defined in the script.

**Fix**:
```bash
# Check whether output/data/manuscript_variables.json exists
ls projects/code_project/output/data/manuscript_variables.json

# Re-run Phase 2
uv run python projects/code_project/scripts/z_generate_manuscript_variables.py

# Detect remaining unresolved tokens
grep -r "{{" projects/code_project/output/manuscript/ | grep -v ".json"
```

### Missing figure in PDF

**Symptom**: PDF has a broken image placeholder or missing figure reference.

**Cause**: Phase 1 (`optimization_analysis.py`) failed to generate one or more figures.

**Fix**:
```bash
ls projects/code_project/output/figures/*.png
uv run python projects/code_project/scripts/optimization_analysis.py
```

### BibTeX citation error / PDF fails to compile

**Symptom**: pdflatex exits with a BibTeX error or undefined citation key.

**Cause**: Malformed entry in `manuscript/references.bib` (unclosed braces, duplicate keys, missing required fields).

**Fix**: Validate `manuscript/references.bib` with a BibTeX linter or check the `.log` file in `output/tex/` for the specific error message.

### Slides not generated

**Symptom**: `output/slides/` is empty or missing sections.

**Cause**: `scripts/03_render_pdf.py` requires Pandoc with Beamer support. Check `pandoc --version`.

**Fix**:
```bash
pandoc --version
# If missing: brew install pandoc (macOS) or see docs/operational/error-handling-guide.md
```
