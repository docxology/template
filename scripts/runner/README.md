# scripts/runner/

Pipeline execution runners — entry points for single-project and multi-project runs.

## Scripts

| Script | One-liner |
|--------|-----------|
| `execute_pipeline.py` | Run full pipeline for one project |
| `execute_multi_project.py` | Run pipeline for all (or selected) projects |
| `run_matrix.py` | Deterministic project × stage matrix |

## Usage

```bash
# Single project
uv run python scripts/runner/execute_pipeline.py --project my_project

# All projects
uv run python scripts/runner/execute_multi_project.py

# Parallel
uv run python scripts/runner/execute_multi_project.py --parallel

# Matrix
uv run python scripts/runner/run_matrix.py
```

## Notes

- Bootstrap uses `parents[2]` from `scripts/runner/` to reach repo root.
- Individual numbered stages live in [`scripts/pipeline/`](../pipeline/).
- The canonical stage ordering is in `infrastructure/core/pipeline/pipeline.yaml`.
