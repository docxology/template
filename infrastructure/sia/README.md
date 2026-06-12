# SIA harness

> **Tier: exemplar-support.** Layer-1 by location, but imported only by its
> `template_sia` exemplar — intentionally not generic-reach across
> `infrastructure/`. See [AGENTS.md](AGENTS.md).

Self-Improving AI loop utilities: task layout validation, execution
log parsing, evaluation runner, and fixture-backed generation replay.

```bash
uv run python -m infrastructure.sia.cli path/to/task
uv run pytest tests/infra_tests/sia/ -v
```

See [AGENTS.md](AGENTS.md) for module map.
