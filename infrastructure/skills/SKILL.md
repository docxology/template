---
name: infrastructure-skills
description: Programmatic discovery of first-party agent SKILL.md files under configured public repo roots (infrastructure, scripts, projects/templates, resource-pool templates, docs/prompts, and .cursor/skills). Use when enumerating skills, validating .cursor/skill_manifest.json, writing docs/_generated/skills_index.md, checking docs/prompts workflow contracts, or wiring editor/Codex/MCP automation. Exposes discover_skills, write_skill_manifest, manifest_matches_discovery, and check_skill_contracts.
---

# Skill Descriptor — infrastructure/skills

## Module Overview

Machine-readable discovery for all `SKILL.md` descriptors used by Cursor and similar agents.

## Capabilities

- **Recursive scan**: `**/SKILL.md` under the default roots `infrastructure/`, `scripts/`, `projects/templates/`, `fonds/templates/`, `rules/templates/`, `tools/templates/`, `docs/prompts/`, and `.cursor/skills/` (configurable)
- **Project-local agents**: public exemplar `.agents/skills/<name>/SKILL.md` files are included so Hermes/agentskills.io descriptors also appear in `.cursor/skill_manifest.json` and MCP `list_skills`
- **Frontmatter parsing**: YAML `name` and `description` (full dict available)
- **Manifest I/O**: Write or verify `.cursor/skill_manifest.json`
- **Generated index**: Write `docs/_generated/skills_index.md` for human browsing
- **Workflow contracts**: Validate `docs/prompts/**/SKILL.md` metadata (`version`, `last_updated`, `status`, `data_access_level`, `task_type`, `modes`, `related_skills`)

## CLI

```bash
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills write-index
uv run python -m infrastructure.skills write --roots infrastructure docs/prompts .cursor/skills
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
uv run python -m infrastructure.skills list-json
```

## See Also

- [`discovery.py`](discovery.py) — API implementation
- [`contracts.py`](contracts.py) — docs/prompts workflow metadata contracts
- [`infrastructure/SKILL.md`](../SKILL.md) — human-oriented hub list
