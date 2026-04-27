# Quick Start Guide

Get up and running with the `code_project` exemplar in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv) package manager (recommended) or `pip`
- Git

## Setup (One-Time)

```bash
# 1. Clone the template repository (if you haven't already)
git clone https://github.com/docxology/template.git
cd template

# 2. Install dependencies at the repository root
uv sync

# 3. Verify installation
uv run python --version
```

## Run the Test Suite

Validate the environment and check that all 42 tests pass with ≥90% coverage:

```bash
uv run pytest projects/code_project/tests/ -v --tb=short
```

Expected: **42 passed**, coverage ~99%.

## Execute the Analysis Pipeline

Generate figures, data, reports, and the analysis dashboard:

```bash
uv run python projects/code_project/scripts/optimization_analysis.py
```

**Outputs created under `projects/code_project/output/`:**
- `figures/` — 7 PNG plots (convergence, stability, benchmarks)
- `data/` — CSV and JSON results
- `reports/` — HTML dashboard and validation JSON
- `manuscript/` — token-substituted markdown sections
- `citations/` — APA/BibTeX/MLA citations

## Render the Publication PDF

Convert the manuscript to a PDF with LaTeX:

```bash
uv run python scripts/03_render_pdf.py --project code_project
```

Final PDF: `projects/code_project/output/pdf/code_project_combined.pdf`

## View Results

- **PDF manuscript**: open `projects/code_project/output/pdf/code_project_combined.pdf`
- **HTML dashboard**: open `projects/code_project/output/reports/analysis_dashboard.html`
- **Figures**: browse `projects/code_project/output/figures/`
- **Data**: `cat projects/code_project/output/data/optimization_results.csv`

## Common Next Steps

- **Change step sizes**: edit `projects/code_project/manuscript/config.yaml` → `experiment.step_sizes`, then re-run steps 2–4.
- **Add a new algorithm**: extend `src/optimizer.py`, add tests in `tests/test_optimizer.py`, and call it from the analysis script (see `docs/architecture.md`).
- **Modify the manuscript**: edit markdown files under `projects/code_project/manuscript/`, then hydrate variables and re-render (steps 3–4).

## Getting Help

- **Full documentation**: [`docs/README.md`](README.md) — navigation hub
- **Agent rules**: [`docs/agent_instructions.md`](agent_instructions.md) — critical constraints before modifying code
- **Troubleshooting**: [`docs/troubleshooting.md`](troubleshooting.md) — common issues and fixes
- **FAQ**: [`docs/faq.md`](faq.md)

## Quick Command Reference

| Task | Command |
|---|---|
| Run tests | `uv run pytest projects/code_project/tests/ -v` |
| Run analysis | `uv run python projects/code_project/scripts/optimization_analysis.py` |
| Hydrate manuscript variables | `uv run python projects/code_project/scripts/z_generate_manuscript_variables.py` |
| Render PDF | `uv run python scripts/03_render_pdf.py --project code_project` |
| Copy final deliverables | `uv run python scripts/05_copy_outputs.py --project code_project` |
| Clean outputs | `rm -rf projects/code_project/output/` |
