# Quickstart

The shipped core analysis uses the local corpus and disables remote enrichment,
LLM synthesis, and deep search. Install declared dependencies and required
rendering tools before these commands, executed from the repository root.

## Verify current project behavior

```bash
uv run --no-sync --offline pytest projects/templates/template_search_project/tests/ \
  --cov=projects/templates/template_search_project/src --cov-branch \
  --cov-fail-under=90
```

Report actual current outcomes and measured coverage. Earlier snapshots do not
guarantee a fresh pass.

## Run canonical core analysis

```bash
uv run --no-sync --offline python scripts/runner/execute_pipeline.py \
  --project templates/template_search_project --mode core --stage analysis
```

The explicit allowlist runs search, figures, hydration, review report, and
dashboard. Search writes `output/search/results.json`, `output/corpus.json`,
`output/bibliography/references.bib`, and a reading report. Hydration copies
source markdown/config/curated references to `output/manuscript/`, substitutes
variables, and projects additional citations into `generated_search.bib`.
Authored markdown/BibTeX remains unchanged.

## Render and validate

```bash
uv run --no-sync --offline python scripts/runner/execute_pipeline.py \
  --project templates/template_search_project --mode core --stage render_pdf
uv run --no-sync --offline python scripts/runner/execute_pipeline.py \
  --project templates/template_search_project --mode core --stage validate
```

Canonical execution uses the nominated candidate's measured epoch and selected
renderer with actual artifact receipts. Installed tools are required; dependency
installation is separate from offline analysis. See
[`rendering_pipeline.md`](rendering_pipeline.md) for the artifact flow.

## Explicit unpaid discovery and synthesis

Select remote backends, licensed fulltext scope, and a local model deliberately.
Convenience search/deep CLIs consume project configuration. The separate
`scripts/_run_unpaid_acceptance.py --mode live` lane records bounded actual
provider/model/source/input evidence. Paid providers remain optional and are
excluded from required unpaid acceptance.

For generated deep composition, configure/enable the explicit producer, then run
`run_deep_search.py`, `s_compose_literature_review.py`, and
`z_generate_manuscript_variables.py` with consistent configuration. Composition
requires a current producer record and writes generated S02 under
`output/manuscript/`; hydration checks exact receipt/input/SHA dependencies.
The default core allowlist does not launch those opt-in producers.

A model seed does not guarantee repeatability. Controlled tests, artifact
snapshots, actual unpaid-provider acceptance, rendered output, and installed
wheel acceptance are distinct evidence.
