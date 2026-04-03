# infrastructure/core/pipeline/ - Pipeline Helper Documentation

## Purpose

The `infrastructure/core/pipeline/` package contains the executor, DAG, summary, and multi-project orchestration helpers used by the pipeline entry points.

## Files

- `executor.py` - pipeline execution
- `dag.py` - stage dependency graph helpers
- `multi_project.py` - multi-project orchestration
- `resume.py` - checkpoint resume helpers
- `stages.py` - stage definitions
- `stage_monitor.py` - stage resource monitoring
- `_stage_tracker.py` - tracking internals
- `_performance_monitor.py` - performance internals
- `_monitor_types.py` - shared monitoring types
- `summary.py` - pipeline summaries
- `summary_formatters.py` - summary formatting
- `summary_helpers.py` - summary helpers
- `summary_models.py` - summary dataclasses
- `types.py` - shared pipeline types

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
