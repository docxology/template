# Template Meta-Project Verification

Quick verification routine to run after changes. All steps should complete in under one minute.

## 1. Run Tests

```bash
cd /path/to/template  # repo root
PYTHONPATH=. uv run pytest projects/template/tests/ -v --tb=short
```

Expected: **65 passed**, 0 failed.

Coverage target: 90%+ for `projects/template/src/`.

To run with coverage:

```bash
PYTHONPATH=. uv run pytest projects/template/tests/ -v --tb=short \
  --cov=projects/template/src --cov-report=term-missing
```

## 2. Generate Figures

```bash
PYTHONPATH=. uv run python projects/template/scripts/generate_architecture_viz.py
```

Expected: **Four** figures written to `projects/template/output/figures/`:

- `architecture_overview.png` — Two-Layer Architecture diagram
- `pipeline_stages.png` — Eight-stage pipeline flow
- `module_inventory.png` — Infrastructure module bar chart
- `comparative_feature_matrix.png` — 14×10 tool comparison heatmap

All figures should meet accessibility requirements: 16pt minimum font, colorblind-safe palettes, 150–300 DPI.

## 3. Generate Metrics and Inject Variables

```bash
PYTHONPATH=. uv run python projects/template/scripts/generate_manuscript_metrics.py
```

Expected outputs:

- `projects/template/output/data/metrics.json` — Live repository metrics
- `projects/template/output/manuscript/*.md` — 21 chapters with `${variable}` tokens replaced by computed values

## 4. Introspection Sanity Check

```bash
PYTHONPATH=".:projects/template/src" uv run python -c "
from pathlib import Path
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'projects/template/src')
from template.introspection import build_infrastructure_report
r = build_infrastructure_report(Path('.'))
assert r.module_count >= 10, f'Expected >=10 modules, got {r.module_count}'
assert r.project_count >= 2, f'Expected >=2 projects, got {r.project_count}'
assert r.stage_count >= 7, f'Expected >=7 stages, got {r.stage_count}'
assert r.total_python_files > 500, f'Expected >500 Python files, got {r.total_python_files}'
assert r.total_test_files > 100, f'Expected >100 test files, got {r.total_test_files}'
print('OK:', r.module_count, 'modules,', r.project_count, 'projects,', r.stage_count, 'stages')
print('   ', r.total_python_files, 'Python files,', r.total_test_files, 'test files')
"
```

## 5. Full Pipeline (optional)

Run the complete template project through the pipeline:

```bash
./run.sh  # Select "template" project, then "Core pipeline"
```

Or non-interactively:

```bash
./run.sh --pipeline --project template --core-only
```

This executes all 9 pipeline stages and produces the final PDF in `output/template/`.

## Quick Checklist

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Tests pass | `pytest projects/template/tests/` | 65/65 passed |
| Coverage met | `--cov` flag | ≥90% |
| Figures generated | `ls projects/template/output/figures/` | 4 PNG files |
| Metrics current | `cat projects/template/output/data/metrics.json` | Valid JSON with current counts |
| Manuscript rendered | `ls projects/template/output/manuscript/` | 21 .md files with no `${` tokens |
| Introspection valid | Step 4 above | ≥10 modules, ≥2 projects |

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: template` | Missing `PYTHONPATH` | Ensure `projects/template/src` is on path |
| `ModuleNotFoundError: infrastructure` | Missing repo root | Ensure repo root `.` is on `PYTHONPATH` |
| Stale `${variable}` in PDF | Skipped Stage 02 | Run `generate_manuscript_metrics.py` first |
| Figure font too small | Matplotlib DPI | Check `dpi=` parameter in `architecture_viz.py` |
| Test count mismatch | New tests added | Update this file and `manuscript/AGENTS.md` |
