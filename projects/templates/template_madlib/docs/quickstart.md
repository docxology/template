# Quickstart — Template Madlib

## Monorepo checkout

The following paths run from the template monorepo root:

```bash
# Run the full pipeline
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_madlib
uv run python scripts/pipeline/stage_03_render.py --project templates/template_madlib

# Run tests
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```

## Standalone checkout

Use the SDK/dev preparation in
[`README.md`](../README.md#standalone-project-commands); the source-only ancestor
resolver does not supply a standalone SDK. From the prepared project root:

```bash
.venv/bin/python -I -m pytest tests/ --cov=src --cov-fail-under=90
.venv/bin/python scripts/01_generate_madlib_artifacts.py
.venv/bin/python scripts/02_validate_outputs.py
.venv/bin/python scripts/z_generate_manuscript_variables.py
.venv/bin/python -I -m infrastructure.validation.cli prerender manuscript --repo-root .
```

The installed SDK provides the validator above; `scripts/pipeline/` and
`scripts/audit/` remain monorepo-only paths, not shipped standalone scripts.
