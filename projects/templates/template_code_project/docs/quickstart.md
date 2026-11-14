# Quick Start Guide

Produce numerical analysis artifacts or choose the complete manuscript path for
`template_code_project`. Actual elapsed time depends on the selected tools and inputs.

## Prerequisites

- Python 3.14 (3.14 and 3.15 are the supported minors)
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
- Git

## Setup (One-Time)

```bash
# 1. Clone the template repository (if you haven't already)
git clone https://github.com/docxology/template.git
cd template

# 2. Prepare the locked Root and this project's own declared development environment
uv sync --locked
uv sync --locked --project projects/templates/template_code_project --extra dev \
  --python "$PWD/.venv/bin/python"

# 3. Observe the selected own interpreter
uv run --no-sync --offline --project projects/templates/template_code_project python --version
```

## Run the Test Suite

Validate the environment and check that the project test suite passes with the ≥90% coverage gate.
Falling below that floor fails the gate outright (`--cov-fail-under` enforces it), and zero-collected suites fail too rather than counting as a pass.

```bash
uv run --no-sync --offline --project projects/templates/template_code_project \
  python -m pytest projects/templates/template_code_project/tests/ -v --tb=short \
  --cov=projects/templates/template_code_project/src --cov-fail-under=90
```

Expected: passing tests and coverage above the 90% gate. Live collection counts are tracked in [`../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## Execute the Analysis Pipeline

For analysis-only use, generate numerical figures, data, validation and citation
artifacts. This command does not also build the dashboard or hydrate manuscripts:

```bash
uv run --no-sync --offline --project projects/templates/template_code_project \
  python projects/templates/template_code_project/scripts/optimization_analysis.py
```

**Outputs created under `projects/templates/template_code_project/output/`:**
- `figures/` — 6 PNG plots (convergence, stability, benchmarks)
- `data/` — CSV and JSON results
- `reports/` — generated analysis validation JSON
- `citations/` — APA/BibTeX/MLA citations

## Render the Publication PDF

For the complete manuscript path, use the resolved core pipeline instead of
the analysis-only command above. It executes the configured producers,
including the separate dashboard and token hydration, then renders, validates
and copies the deliverables. Rendering tools and the Root runtime must already
be prepared; see the [shared run surface](../../../README.md#run-surface).

```bash
./run.sh --pipeline --project templates/template_code_project --mode core
```

Final PDF: `projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf`

## View Results

- **PDF manuscript**: open `projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf`
- **HTML dashboard**: open `projects/templates/template_code_project/output/web/dashboard.html` (via `scripts/build_dashboard.py`)
- **Figures**: browse `projects/templates/template_code_project/output/figures/`
- **Data**: `cat projects/templates/template_code_project/output/data/optimization_results.csv`

## Common Next Steps

- **Change step sizes**: edit `projects/templates/template_code_project/manuscript/config.yaml` → `experiment.step_sizes`, then re-run steps 2–4.
- **Add a new algorithm**: extend `src/template_code_project/core/optimizer.py`, add tests in `tests/core/test_optimizer.py`, and call it from the analysis script (see `docs/architecture.md`).
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
| Render PDF | `uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project` |
| Copy final deliverables | `uv run python scripts/pipeline/stage_05_copy.py --project templates/template_code_project` |
| Clean outputs | `rm -rf projects/templates/template_code_project/output/` |
