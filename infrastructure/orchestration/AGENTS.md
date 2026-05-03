# Orchestration Package

## Purpose

This package hosts the logic that historically lived almost entirely in `run.sh` and `secure_run.sh`. The shell scripts are thin: they bootstrap `uv` / `.venv` and delegate here via `python -m infrastructure.orchestration`.

This package coordinates existing Layer-1 modules (`infrastructure.core.pipeline`, `infrastructure.project.discovery`, `infrastructure.steganography`, …). It does **not** re-implement DAG stages.

## Files

| File | Role |
| --- | --- |
| `cli.py` | Argument parser and `main()` entry wired from `__main__.py`. |
| `discovery.py` | `validate_project_slug`, `select_project_interactive`, `discover_qualified_names` — wraps `discover_projects()`. |
| `menu.py` | `MENU_OPTIONS`, `render_menu` — deterministic menu text for TTY workflows. |
| `pipeline_runner.py` | `PipelineRunner` — thin adapter over `PipelineExecutor`. |
| `stage_logger.py` | `setup_stage_log`, `stage_log_path` — append-only banners under project log paths. |
| `secure_run.py` | `run_secure_pipeline` — pipeline + steganography post-processing. |

## Contracts

- **No pipeline stage logic.** Stage scripts remain under [`scripts/`](../../scripts/).
- **Slug validation** rejects traversal (`..`), NUL bytes, `-` prefixes, unknown project names from `discover_projects()`.
- **Tests:** [`tests/infra_tests/orchestration/`](../../tests/infra_tests/orchestration/).

## See also

- [`README.md`](README.md)
- [`SKILL.md`](SKILL.md)
