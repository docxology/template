# tests/infra_tests/skills/

Tests for `infrastructure.skills` — YAML frontmatter parsing, recursive `SKILL.md` discovery under configurable roots, manifest write/check, and CLI entry points.

## Run

```bash
uv run pytest tests/infra_tests/skills/ -v
uv run pytest tests/infra_tests/skills/ --cov=infrastructure.skills --cov-report=term-missing
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../../../infrastructure/skills/README.md`](../../../infrastructure/skills/README.md)
