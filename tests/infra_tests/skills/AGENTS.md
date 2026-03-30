# tests/infra_tests/skills/

Tests for `infrastructure.skills`: YAML frontmatter parsing, recursive `SKILL.md` discovery under configurable roots, manifest write/check, and CLI entry points.

## Files

- `test_skill_discovery.py` — unit tests with `tmp_path` fixtures; integration checks against the real template repo and `.cursor/skill_manifest.json`

## Running

```bash
uv run pytest tests/infra_tests/skills/ -v
uv run pytest tests/infra_tests/skills/ --cov=infrastructure.skills --cov-report=term-missing
```

## See also

- [`../../../infrastructure/skills/AGENTS.md`](../../../infrastructure/skills/AGENTS.md)
