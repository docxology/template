# tests/infra_tests/orchestration/

Targets `infrastructure.orchestration`: CLI (`main`, `build_parser`), menu rendering, project discovery helpers, `PipelineRunner`, `stage_logger`, and `secure_run` wiring (real subprocess/fixtures — no mocks).

## Run

```bash
uv run pytest tests/infra_tests/orchestration/ -v
```

## See also

- [`AGENTS.md`](AGENTS.md)
- [`../../../infrastructure/orchestration/AGENTS.md`](../../../infrastructure/orchestration/AGENTS.md)
