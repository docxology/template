# SIA harness

Generic Self-Improving AI loop utilities: task layout validation, execution
log parsing, evaluation runner, and fixture-backed generation replay.

```bash
uv run python -m infrastructure.sia.cli path/to/task
uv run pytest tests/infra_tests/sia/ -v
```

See [AGENTS.md](AGENTS.md) for module map.
