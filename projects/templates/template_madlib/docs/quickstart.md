# Quickstart — Template Madlib

## Monorepo checkout

Prepare Root and this project's own environment through the
[shared run surface](https://github.com/docxology/template/blob/main/projects/README.md#run-surface).
The following stage commands run from the prepared monorepo root, following the
[dispatch guide](https://github.com/docxology/template/blob/main/docs/RUN_GUIDE.md):

```bash
# Analysis and configured rendering stages, not a complete core pipeline
uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_madlib
uv run --no-sync --offline python scripts/pipeline/stage_03_render.py --project templates/template_madlib

# Run tests
uv run --no-sync --offline --project projects/templates/template_madlib \
  python -m pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```

## Standalone checkout

Use the SDK/dev preparation in
[`README.md`](../README.md#standalone-project-commands); the source-only ancestor
resolver does not supply a standalone SDK. From the prepared project root:

```bash
.venv/bin/python scripts/z_generate_manuscript_variables.py
.venv/bin/python scripts/02_validate_outputs.py
```

The first command generates configured data/reports/figures, writes
`output/data/manuscript_variables.json`, and hydrates `output/manuscript/`.
The second validates those local outputs, writes
`output/reports/output_validation.json`, and exits nonzero on failed bindings.
Running validation before hydration can consume missing or retained old
manuscript artifacts. No successful execution, PDF layout, domain truth or
publication acceptance is claimed here.

For artifacts without hydration, the separate entrypoint remains
`scripts/01_generate_madlib_artifacts.py`; do not run it redundantly before the
hydration entrypoint merely to complete this walkthrough.

## Separate own-suite and SDK checks

From the same prepared project root:

```bash
.venv/bin/python -I -m pytest tests/ --cov=src --cov-fail-under=90
.venv/bin/python -I -m infrastructure.validation.cli prerender manuscript --repo-root .
```

The installed SDK supplies the prerender validator; it is not native rendering
acceptance. `scripts/pipeline/` and `scripts/audit/` remain monorepo-only paths,
not shipped standalone scripts. Preserve retained public outputs and immutable
evidence; generated does not mean disposable.
