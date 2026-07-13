# template_autoresearch_project tests

Tests for the deterministic bounded AutoResearch public exemplar.

The suite runs against a session sandbox with a copied baseline output tree and
real source/infrastructure paths, so full loop and subprocess tests cannot dirty
tracked artifacts.

## Quick Start

```bash
uv run pytest projects/templates/template_autoresearch_project/tests/ -q
```

Pipeline parity:

```bash
uv run python scripts/pipeline/stage_01_test.py --project template_autoresearch_project --project-only
```

## Coverage

| File | Focus |
| --- | --- |
| `test_config.py` | Project and manuscript configuration parsing |
| `test_loop.py` | AutoResearch loop artifacts, readiness, stage matrix, and figures |
| `test_manuscript_variables.py` | Manuscript token coverage and resolved manuscript output |
| `test_ml_task.py` | Fixed-seed ML dataset, candidate evaluation, selection, and budget behavior |
| `test_reports.py` | Loop and ML experiment report rendering |
| `test_scripts.py` | Thin script smoke coverage |

See [AGENTS.md](AGENTS.md) for local editing guidance.
