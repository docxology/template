# `template_code_project/src/analysis/`

Importable analysis package for the code exemplar.

This package runs convergence experiments, stability and benchmark reports, and
publishing metadata preparation. Scripts delegate here so the analysis workflow
is testable without shell logic.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | Public analysis exports. |
| `_infra.py` | Optional infrastructure availability helpers. |
| `_logging.py` | Logging fallback helpers. |
| `experiments.py` | Convergence experiments and result persistence. |
| `pipeline.py` | Composable step exports (`run_convergence_experiment`, metadata, validation). |
| `workflow.py` | Full `run_analysis_pipeline` / `main` orchestration. |
| `publishing.py` | Citation and metadata material generation. |
| `scientific_reports.py` | Benchmark, stability, validation, and figure registry reports. |

## See Also

- [`../README.md`](../README.md) - project source overview
- [`../AGENTS.md`](../AGENTS.md) - source-layer editing rules
