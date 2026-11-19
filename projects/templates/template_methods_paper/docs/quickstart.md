# Quick Start Guide

Prepare the `template_methods_paper` environment and generate local method
artifacts, or continue to the separate manuscript-rendering workflow.

## Prerequisites

- Python 3.14 (3.14 and 3.15 are the supported minors)
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
- Git

## Setup (One-Time)

This walkthrough runs from the canonical monorepo root. Common environment
preparation belongs to the
[shared run surface](https://github.com/docxology/template/blob/main/projects/README.md#run-surface);
Root dispatch belongs to
[RUN_GUIDE](https://github.com/docxology/template/blob/main/docs/RUN_GUIDE.md).
Independent project boundaries remain in [STANDALONE.md](../STANDALONE.md).

```bash
# 1. Clone the template repository (if you haven't already)
git clone https://github.com/docxology/template.git
cd template

# 2. Install dependencies at the repository root
uv sync --locked
uv sync --locked --project projects/templates/template_methods_paper --extra dev \
  --python "$PWD/.venv/bin/python"

# 3. Observe the selected own interpreter, not the Root interpreter
uv run --no-sync --offline --project projects/templates/template_methods_paper python --version
```

## Run the Test Suite

Validate the environment and check that the project test suite passes with
the ≥90% coverage gate:

```bash
uv run --no-sync --offline --project projects/templates/template_methods_paper \
  python -m pytest projects/templates/template_methods_paper/tests/ -v --tb=short \
  --cov=projects/templates/template_methods_paper/src --cov-fail-under=90
```

Expected: passing tests and coverage above the 90% gate. Live collection
counts are tracked in [`../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## Execute the Analysis Pipeline

Compile the two worked example methods, run every staged gate, export
worklist/CSV/Mermaid/JSON, demonstrate the trust hash-chain, and plot the
step-count figure:

```bash
uv run --no-sync --offline --project projects/templates/template_methods_paper \
  python projects/templates/template_methods_paper/scripts/methods_analysis.py
```

**Outputs created under `projects/templates/template_methods_paper/output/`:**
- `data/` — per-method worklist/CSV/Mermaid/JSON exports, `compiled_plans.json`
- `reports/` — `gate_report.json`, `trust_chain_report.json`
- `figures/` — `step_counts.png`

## Generate and Inject Manuscript Variables

```bash
uv run --no-sync --offline --project projects/templates/template_methods_paper \
  python projects/templates/template_methods_paper/scripts/z_generate_manuscript_variables.py
```

This reads `manuscript/config.yaml` plus the analysis outputs above and
resolves every `{{TOKEN}}` in `manuscript/*.md`.

## Render the Publication PDF

This is a separate Root operation with prepared rendering tools, not proof
supplied by the local analysis command.

```bash
uv run --no-sync --offline python scripts/pipeline/stage_03_render.py --project templates/template_methods_paper
```

## View Results

- **Exports**: browse `projects/templates/template_methods_paper/output/data/`
- **Reports**: `cat projects/templates/template_methods_paper/output/reports/gate_report.json`
- **Figure**: `projects/templates/template_methods_paper/output/figures/step_counts.png`
- **PDF manuscript**: under `output/.../pdf/` after rendering

## Common Next Steps

- **Specify your own method**: add a new `Method` (via
  `src/template_methods_paper/methods_dsl/model.py`'s dataclasses) to
  `src/template_methods_paper/methods_dsl/examples_methods.py`, add a test, wire it into
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

Run these from the monorepo root after preparation above. Project-local rows
select the own environment; render/copy rows use the prepared Root environment.

| Task | Command |
|---|---|
| Run tests | `uv run --no-sync --offline --project projects/templates/template_methods_paper python -m pytest projects/templates/template_methods_paper/tests -v` |
| Run analysis | `uv run --no-sync --offline --project projects/templates/template_methods_paper python projects/templates/template_methods_paper/scripts/methods_analysis.py` |
| Generate manuscript variables | `uv run --no-sync --offline --project projects/templates/template_methods_paper python projects/templates/template_methods_paper/scripts/z_generate_manuscript_variables.py` |
| Root render PDF | `uv run --no-sync --offline python scripts/pipeline/stage_03_render.py --project templates/template_methods_paper` |
| Root copy final deliverables | `uv run --no-sync --offline python scripts/pipeline/stage_05_copy.py --project templates/template_methods_paper` |
| Output custody | Canonical project outputs and copied deliverables can be tracked publication evidence. Preserve retained snapshots and immutable receipts; do not use blanket output deletion as setup. |
