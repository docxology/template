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

Default discovery roots are `infrastructure/`, `scripts/`,
`projects/templates/`, `fonds/templates/`, `rules/templates/`,
`tools/templates/`, `docs/prompts/`, `.agents/skills/`, and `.cursor/skills/`.
Repository-scoped plus public-exemplar `.agents/skills/<name>/SKILL.md`
descriptors are included for Hermes/agentskills.io, Codex, and MCP
`list_skills` visibility.
Override roots with `--roots` after the subcommand when you need a focused
manifest.

## Python API

```python
from pathlib import Path
from infrastructure.skills import discover_skills, write_skill_manifest

root = Path(".")
skills = discover_skills(root)
write_skill_manifest(root)
```

See [AGENTS.md](AGENTS.md) for function-level detail.

## Cross-runtime parity

```bash
# Read-only: pinned source + Codex/Claude/Hermes parity
uv run python -m infrastructure.skills runtime-status

# Reversible install: revisioned shared copy, backups, links, receipt
uv run python -m infrastructure.skills runtime-install
```

The installer manages only the names derived from the tracked
`.agents/skills/` tree. It does not bulk-mirror unrelated platform-specific
skills and never executes bundled examples. Per-run receipts are immutable
under `~/.local/state/template-agent-skills/receipts/`; the adjacent
`context-engineering.json` is the current-state view.
