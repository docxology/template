---
name: infrastructure-skills
description: Programmatic discovery of first-party agent SKILL.md files under configured public repo roots (infrastructure, projects, docs/prompts, and .cursor/skills). Use when enumerating skills, validating .cursor/skill_manifest.json, writing docs/_generated/skills_index.md, or wiring editor automation. Exposes discover_skills, write_skill_manifest, and manifest_matches_discovery.
---

# Skill Descriptor — infrastructure/skills

## Module Overview

Machine-readable discovery for all `SKILL.md` descriptors used by Cursor and similar agents.

## Capabilities

- **Recursive scan**: `**/SKILL.md` under the default roots `infrastructure/`, `projects/`, `docs/prompts/`, and `.cursor/skills/` (configurable)
- **Frontmatter parsing**: YAML `name` and `description` (full dict available)
- **Manifest I/O**: Write or verify `.cursor/skill_manifest.json`
- **Generated index**: Write `docs/_generated/skills_index.md` for human browsing

## CLI

```bash
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills write-index
uv run python -m infrastructure.skills write --roots infrastructure docs/prompts .cursor/skills
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills list-json
```

## See Also

- [`discovery.py`](discovery.py) — API implementation
- [`infrastructure/SKILL.md`](../SKILL.md) — human-oriented hub list
