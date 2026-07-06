---
name: template-runner
version: 1.0.0
description: >
  Pipeline execution runners for the template research framework.
  Contains execute_pipeline.py (single-project), execute_multi_project.py
  (multi-project serial/parallel), and run_matrix.py (deterministic matrix).
tags:
  - pipeline
  - runner
  - orchestration
  - template
trigger: "execute pipeline|run pipeline|multi.project|run matrix|execute_pipeline|execute_multi"
---

# template-runner

Pipeline execution runners in `scripts/runner/`.

## When to use

Load this skill when you need to:
- Run the full pipeline for one or many projects
- Debug pipeline execution or PipelineExecutor
- Understand how `run.sh` delegates to Python runners
- Add or modify a runner script

## Runner scripts

| Script | Delegates to |
|--------|-------------|
| `execute_pipeline.py` | `infrastructure.core.pipeline.PipelineExecutor` |
| `execute_multi_project.py` | `infrastructure.core.pipeline.PipelineExecutor` (per project) |
| `run_matrix.py` | `infrastructure.core.pipeline.run_matrix` |

## Bootstrap note

Runner scripts use `parents[2]` from `scripts/runner/` — this reaches the
repo root (3 levels up: runner/ → scripts/ → repo root).

## Pitfalls

- `execute_pipeline.py` re-exports `PipelineArgs`, `handle_hitl_command`, etc.
  for test compatibility — do not remove `__all__`.
- `run_matrix.py` reads `run.config` for project selection; verify it exists.
