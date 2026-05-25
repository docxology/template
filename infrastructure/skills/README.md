# infrastructure/skills

Discovers `SKILL.md` files, parses YAML frontmatter, and maintains `.cursor/skill_manifest.json` for editor and agent routing.

## Commands

```bash
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills write-index
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
uv run python -m infrastructure.skills list-json
```

Default discovery roots are `infrastructure/`, `projects/`, `docs/prompts/`,
and `.cursor/skills/`. Override them with `--roots` after the subcommand when
you need a focused manifest.

## Python API

```python
from pathlib import Path
from infrastructure.skills import discover_skills, write_skill_manifest

root = Path(".")
skills = discover_skills(root)
write_skill_manifest(root)
```

See [AGENTS.md](AGENTS.md) for function-level detail.
