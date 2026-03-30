---
name: infrastructure-skills
description: Programmatic discovery of agent SKILL.md files under infrastructure/. Use when enumerating skills, validating .cursor/skill_manifest.json, or wiring editor automation. Exposes discover_skills, write_skill_manifest, and manifest_matches_discovery.
---

# Skill Descriptor — infrastructure/skills

## Module Overview

Machine-readable discovery for all `SKILL.md` descriptors used by Cursor and similar agents.

## Capabilities

- **Recursive scan**: `**/SKILL.md` under `infrastructure/` (configurable roots)
- **Frontmatter parsing**: YAML `name` and `description` (full dict available)
- **Manifest I/O**: Write or verify `.cursor/skill_manifest.json`

## CLI

```bash
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills write --roots infrastructure docs
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills list-json
```

## See Also

- [`discovery.py`](discovery.py) — API implementation
- [`infrastructure/SKILL.md`](../SKILL.md) — human-oriented hub list
