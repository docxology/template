# tests/infra_tests/orchestration/

## Coverage

Mirrors [`infrastructure/orchestration/`](../../../infrastructure/orchestration/).

| Test module | Focus |
| --- | --- |
| `test_cli.py` | CLI parsing and exit behaviour |
| `test_menu.py` | `render_menu`, `MENU_OPTIONS` |
| `test_discovery.py` | `validate_project_slug`, `select_project_interactive` |
| `test_pipeline_runner.py` | `PipelineRunner` delegation |
| `test_stage_logger.py` | Log paths and append banners |
| `test_secure_run.py` | Secure pipeline wrapper |

## Run

```bash
uv run pytest tests/infra_tests/orchestration/ -v
```

## See also

- [`README.md`](README.md)
- [`../../../infrastructure/orchestration/AGENTS.md`](../../../infrastructure/orchestration/AGENTS.md)
