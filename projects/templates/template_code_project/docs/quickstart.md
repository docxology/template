# Quick Start Guide

Get up and running with the `template_code_project` exemplar in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
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

Validate the environment and check that the project test suite passes with the ≥90% coverage gate:

```bash
uv run pytest projects/templates/template_code_project/tests/ -v --tb=short
```

Expected: passing tests and coverage above the 90% gate. Live collection counts are tracked in [`../../../docs/_generated/canonical_facts.md`](../../../../docs/_generated/canonical_facts.md).

## Execute the Analysis Pipeline

Generate figures, data, reports, and the analysis dashboard:

```bash
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
```

**Outputs created under `projects/templates/template_code_project/output/`:**
- `figures/` — 6 PNG plots (convergence, stability, benchmarks)
- `data/` — CSV and JSON results
- `reports/` — HTML dashboard and validation JSON
- `manuscript/` — token-substituted markdown sections
- `citations/` — APA/BibTeX/MLA citations

## Render the Publication PDF

Convert the manuscript to a PDF with LaTeX:

```bash
uv run python scripts/03_render_pdf.py --project template_code_project
```

Final PDF: `projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf`

## View Results

- **PDF manuscript**: open `projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf`
- **HTML dashboard**: open `projects/templates/template_code_project/output/web/dashboard.html` (via `scripts/build_dashboard.py`)
- **Figures**: browse `projects/templates/template_code_project/output/figures/`
- **Data**: `cat projects/templates/template_code_project/output/data/optimization_results.csv`

## Common Next Steps

- **Change step sizes**: edit `projects/templates/template_code_project/manuscript/config.yaml` → `experiment.step_sizes`, then re-run steps 2–4.
- **Add a new algorithm**: extend `src/optimizer.py`, add tests in `tests/test_optimizer.py`, and call it from the analysis script (see `docs/architecture.md`).
- **Modify the manuscript**: edit markdown files under `projects/templates/template_code_project/manuscript/`, then hydrate variables and re-render (steps 3–4).

## Getting Help

- **Full documentation**: [`docs/README.md`](README.md) — navigation hub
- **Agent rules**: [`docs/agent_instructions.md`](agent_instructions.md) — critical constraints before modifying code
- **Troubleshooting**: [`docs/troubleshooting.md`](troubleshooting.md) — common issues and fixes
- **FAQ**: [`docs/faq.md`](faq.md)

## Quick Command Reference

| Task | Command |
|---|---|
| Run tests | `uv run pytest projects/templates/template_code_project/tests/ -v` |
| Run analysis | `uv run python projects/templates/template_code_project/scripts/optimization_analysis.py` |
| Hydrate manuscript variables | `uv run python projects/templates/template_code_project/scripts/z_generate_manuscript_variables.py` (strict; requires analysis CSV; add `--allow-draft` for early drafts) |
| Render PDF | `uv run python scripts/03_render_pdf.py --project template_code_project` |
| Copy final deliverables | `uv run python scripts/05_copy_outputs.py --project template_code_project` |
| Clean outputs | `rm -rf projects/templates/template_code_project/output/` |
