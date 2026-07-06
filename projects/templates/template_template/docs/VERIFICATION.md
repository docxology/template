# Template Meta-Project Verification

Quick verification routine to run after changes.

## 1. Run Tests

Run from the template repo root:

```bash
uv run pytest projects/templates/template_template/tests/ -v --tb=short \
  --cov=projects/templates/template_template/src/template_template --cov-fail-under=90
```

Expected: all tests passed, 90%+ coverage on `src/template_template/`.

## 2. Generate Figures

```bash
uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
```

Expected: four PNG files under `projects/templates/template_template/output/figures/`:

- `architecture_overview.png`
- `pipeline_stages.png` — YAML DAG (${pipeline_stages_declared} stages)
- `module_inventory.png`
- `comparative_feature_matrix.png`

## 3. Generate Metrics and Inject Variables

```bash
uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py
```

Expected:

- `output/data/metrics.json` — includes `pipeline_stages_declared`, `pipeline_stages_core_only`, `public_exemplar_list`
- `output/manuscript/*.md` — numbered chapters without unresolved `${...}` tokens

## 4. Introspection Sanity Check

```bash
uv run python -c "
from pathlib import Path
from template_template.introspection import build_infrastructure_report
r = build_infrastructure_report(Path('.'))
assert r.pipeline_stages_declared >= 14
assert r.pipeline_stages_core_only == 8
assert r.pipeline_stages_default_full == 10
print('OK:', r.pipeline_stages_declared, 'declared,', len(r.modules), 'modules')
"
```

Run from repo root with `projects/templates/template_template/src` on `PYTHONPATH` (pytest conftest handles this).

## 5. Full Pipeline (optional)

```bash
uv run python scripts/pipeline/stage_02_analysis.py --project template_template
uv run python scripts/pipeline/stage_03_render.py --project template_template
```

## Quick Checklist

| Check | Pass criteria |
|-------|---------------|
| Tests | All passed, ≥90% cov on `src/template_template/` |
| Figures | 4 PNG files in `output/figures/` |
| Metrics | Valid JSON; pipeline keys present |
| Manuscript | No unresolved `${` in numbered chapters |
| Introspection | 14 declared stages, 8 core-only |

## Common Issues

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: template` | Run from template repo root; use `projects/templates/template_template/tests/` |
| `Could not locate template repo root` | Ensure `projects/templates/template_template` exists in the checkout |
| Stale `${variable}` in PDF | Re-run `generate_manuscript_metrics.py` |
