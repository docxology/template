# Quick Start Guide

Get up and running with the `template_methods_paper` exemplar in 5 minutes.

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

Validate the environment and check that the project test suite passes with
the ≥90% coverage gate:

```bash
uv run pytest projects/templates/template_methods_paper/tests -v --tb=short
```

Expected: passing tests and coverage above the 90% gate. Live collection
counts are tracked in [`../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## Execute the Analysis Pipeline

Compile the two worked example methods, run every staged gate, export
worklist/CSV/Mermaid/JSON, demonstrate the trust hash-chain, and plot the
step-count figure:

```bash
uv run python projects/templates/template_methods_paper/scripts/methods_analysis.py
```

**Outputs created under `projects/templates/template_methods_paper/output/`:**
- `data/` — per-method worklist/CSV/Mermaid/JSON exports, `compiled_plans.json`
- `reports/` — `gate_report.json`, `trust_chain_report.json`
- `figures/` — `step_counts.png`

## Generate and Inject Manuscript Variables

```bash
uv run python projects/templates/template_methods_paper/scripts/z_generate_manuscript_variables.py
```

This reads `manuscript/config.yaml` plus the analysis outputs above and
resolves every `{{TOKEN}}` in `manuscript/*.md`.

## Render the Publication PDF

```bash
uv run python scripts/pipeline/stage_03_render.py --project templates/template_methods_paper
```

## View Results

- **Exports**: browse `projects/templates/template_methods_paper/output/data/`
- **Reports**: `cat projects/templates/template_methods_paper/output/reports/gate_report.json`
- **Figure**: `projects/templates/template_methods_paper/output/figures/step_counts.png`
- **PDF manuscript**: under `output/.../pdf/` after rendering

## Common Next Steps

- **Specify your own method**: add a new `Method` (via
  `src/methods_dsl/model.py`'s dataclasses) to
  `src/methods_dsl/examples_methods.py`, add a test, wire it into
  `scripts/methods_analysis.py`, then re-run the analysis.
- **Extend the controlled vocabulary**: only if your domain genuinely needs a
  new `StepKind` or `Dimension` — add it to `vocabulary.py`/`units.py` with a
  test (see `docs/architecture.md`).
- **Modify the manuscript**: edit markdown files under `manuscript/`, then
  re-render.

## Getting Help

- **Full documentation**: [`docs/README.md`](README.md) — navigation hub.
- **Agent rules**: [`docs/agent_instructions.md`](agent_instructions.md).
- **Troubleshooting**: [`docs/troubleshooting.md`](troubleshooting.md).
- **FAQ**: [`docs/faq.md`](faq.md).

## Quick Command Reference

| Task | Command |
|---|---|
| Run tests | `uv run pytest projects/templates/template_methods_paper/tests -v` |
| Run analysis | `uv run python projects/templates/template_methods_paper/scripts/methods_analysis.py` |
| Generate manuscript variables | `uv run python projects/templates/template_methods_paper/scripts/z_generate_manuscript_variables.py` |
| Render PDF | `uv run python scripts/pipeline/stage_03_render.py --project templates/template_methods_paper` |
| Copy final deliverables | `uv run python scripts/pipeline/stage_05_copy.py --project templates/template_methods_paper` |
| Clean outputs | `rm -rf projects/templates/template_methods_paper/output/` |
