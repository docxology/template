# Orchestration Package

## Purpose

This package hosts the logic that historically lived almost entirely in `run.sh` and `secure_run.sh`. The shell scripts are thin: they bootstrap `uv` / `.venv` and delegate here via `python -m infrastructure.orchestration`.

This package coordinates existing Layer-1 modules (`infrastructure.core.pipeline`, `infrastructure.project.discovery`, `infrastructure.steganography`, …). It does **not** re-implement DAG stages.

## Files

| File | Role |
| --- | --- |
| `cli.py` | Argument parser and `main()` entry wired from `__main__.py`. Bare invocation runs `_interactive()` — prints a choice prompt each turn and passes `writer=sys.stdout` into `select_project_interactive`. |
| `discovery.py` | `validate_project_slug`, `select_project_interactive`, `discover_qualified_names` — wraps `discover_projects()`. When `writer` is set, the picker lists projects and prints `Choice [index / a=all / q=quit]: ` before reading input. |
| `menu.py` | `MENU_OPTIONS`, `render_menu`, `_menu_row` — deterministic, ANSI-free menu text. Framing and section rules use ASCII (`+`, `=`, `-`, `|`) for TTY compatibility; option rows stay column-aligned. [`tests/infra_tests/orchestration/test_menu.py`](../../tests/infra_tests/orchestration/test_menu.py) asserts stable legend substrings and each `_menu_row` line. Used by `_interactive` and the `menu` subcommand. |
| `pipeline_runner.py` | `PipelineRunner` — thin adapter over `PipelineExecutor`. |
| `stage_logger.py` | `setup_stage_log`, `stage_log_path` — append-only banners under project log paths. |
| `secure_run.py` | `run_secure_pipeline` — pipeline + steganography post-processing. |
| `link_sync.py` | Sidecar link-sync hook registry: `register_link_sync` / `registered_link_sync_hooks`, `maybe_sync_all_links`, and `print_link_sync_result(s)`. Registers the projects/fonds/rules/tools sync hooks (each skipped via its own `*_SKIP` env var). |

## Contracts

- **No pipeline stage logic.** Stage scripts remain under [`scripts/`](../../scripts/).
- **Interactive menu keys `0`–`7`** dispatch single stages via [`stage_registry.MENU_KEY_TO_STAGE`](../core/pipeline/stage_registry.py) → [`execute_single_stage()`](../core/pipeline/single_stage.py) (direct subprocess to `scripts/NN_*.py`); they do not shell out to `execute_pipeline.py --stage`.
- **Slug validation** rejects traversal (`..`), NUL bytes, `-` prefixes, unknown project names from `discover_projects()`.
- **Qualified exemplar paths** resolve as `templates/<name>` and `active/<name>` under `projects/` (see [`docs/_generated/active_projects.md`](../../docs/_generated/active_projects.md)). Live counts link to [`docs/_generated/COUNTS.md`](../../docs/_generated/COUNTS.md).
- **Tests:** [`tests/infra_tests/orchestration/`](../../tests/infra_tests/orchestration/).

## See also

- [`README.md`](README.md)
- [`SKILL.md`](SKILL.md)
