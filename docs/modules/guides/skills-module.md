# Skills Module

> **Agent skill discovery and manifest generation**

**Location:** `infrastructure/skills/`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **SKILL.md Discovery**: Scans infrastructure modules for `SKILL.md` files with YAML frontmatter
- **Manifest Generation**: Writes the default manifest at repo-root `.cursor/skill_manifest.json` when you run `uv run python -m infrastructure.skills write` (the `.cursor/` directory is created if needed)
- **Manifest Validation**: Checks if manifest matches current on-disk skills
- **MCP Alignment**: Skill descriptors follow Model Context Protocol conventions

---

## Usage Examples

### Discover All Skills

```python
from pathlib import Path
from infrastructure.skills import discover_skills, SkillDescriptor

skills: list[SkillDescriptor] = discover_skills(Path("."))
for skill in skills:
    print(f"{skill.name}: {skill.description[:60]}...")
```

### Write Skill Manifest

```python
from pathlib import Path
from infrastructure.skills import write_skill_manifest

# Default: <repo>/.cursor/skill_manifest.json
path = write_skill_manifest(Path("."))
print(f"Manifest written to {path}")
```

### Check Manifest Freshness

```python
from pathlib import Path
from infrastructure.skills import manifest_matches_discovery

is_fresh = manifest_matches_discovery(Path("."))
if not is_fresh:
    print("Manifest is stale — run `uv run python -m infrastructure.skills write`")
```

**CLI Usage:**

```bash
# Write/refresh the skill manifest
uv run python -m infrastructure.skills write

# Check if manifest is up to date
uv run python -m infrastructure.skills check
```

---

## SKILL.md Format

Each infrastructure module's `SKILL.md` uses YAML frontmatter:

```yaml
---
name: infrastructure-rendering
description: >
  Multi-format output generation (PDF, HTML, slides).
  Use for: Pandoc/XeLaTeX rendering, RenderManager, slide deck generation.
  Key imports: RenderManager, RenderingConfig from infrastructure.rendering
---
```

The body contains markdown instructions for AI agents.

---

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| `SkillDescriptor` | Dataclass | Parsed SKILL.md metadata |
| `discover_skills` | Function | Find all SKILL.md files |
| `write_skill_manifest` | Function | Generate manifest JSON |
| `manifest_matches_discovery` | Function | Check manifest freshness |
| `load_skill_descriptor` | Function | Parse single SKILL.md |
| `split_yaml_frontmatter` | Function | Extract YAML from markdown |

---

## Related Documentation

- **[Modules Guide](../modules-guide.md)** — Module overview
- **[Infrastructure SKILL.md](../../../infrastructure/SKILL.md)** — Root skill descriptor
- **[Infrastructure AGENTS.md](../../../infrastructure/skills/AGENTS.md)** — Machine-readable API spec
