# infrastructure/tools — Quick Reference

Executable entry points (scripts, skills, agents) for research workflows.
Distinct from `projects/` (full research environments) and `fonds/` (passive
data stores). Full discovery, validation, public scope, and private-sidecar
symlink sync.

## Quick start

```python
from pathlib import Path
from infrastructure.tools import (
    discover_tools,
    resolve_tool_root,
    validate_tool_structure,
    ToolInfo,
    build_tool_info,
)
from infrastructure.tools.public_scope import (
    PUBLIC_TOOL_NAMES,
    public_tool_infos,
    public_tool_names,
)
from infrastructure.tools.linking import sync_private_tool_links

# Discover all public exemplar tools
tools = discover_tools(Path("."))
for t in tools:
    print(t.qualified_name, t.tool_type, t.is_valid)

# Validate a tool
is_valid, msg = validate_tool_structure(Path("tools/templates/template_code_executor"))

# Check public CI scope
print(PUBLIC_TOOL_NAMES)
# ('templates/template_code_executor',)

# Sync private sidecar (no-op when absent)
result = sync_private_tool_links(Path("."), dry_run=True)
print(result.summary())
```

## File layout

```
infrastructure/tools/
├── AGENTS.md          ← operating contract for agents
├── README.md          ← this file
├── SKILL.md           ← agent routing contract (YAML frontmatter)
├── __init__.py        ← re-exports: ToolInfo, discover_tools, resolve_tool_root, validate_tool_structure, build_tool_info
├── discovery.py       ← discover_tools, resolve_tool_root, NON_RENDERED_TOOL_SUBDIRS, RENDERED_TOOL_SUBDIRS
├── tools_info.py      ← ToolInfo dataclass + build_tool_info
├── validation.py      ← validate_tool_structure
├── public_scope.py    ← PUBLIC_TOOL_NAMES, public_tool_infos, public_tool_names
└── linking.py         ← sidecar symlink sync
```

## Tool structure requirements

| Path | Required? | Description |
|------|-----------|-------------|
| `tools.yaml` | ✅ Yes | Manifest describing the tool |
| `scripts/` | ✅ Yes | Executable entry points |
| `tests/` | Optional | Tool-level tests |
| `docs/` | Optional | Documentation |

Unlike fonds, tools require a `scripts/` directory (not `data/`).

## ToolInfo dataclass

```python
info: ToolInfo = build_tool_info(Path("tools/templates/template_code_executor"))
info.name           # "template_code_executor"
info.tool_type      # from tools.yaml "type", or "generic"
info.has_scripts    # True iff scripts/ exists
info.has_tests      # True iff tests/ exists
info.is_valid       # True iff has_scripts
info.qualified_name # "template_code_executor" or "templates/template_code_executor"
```

## Discovery scope

`discover_tools()` scans `tools/` and skips `NON_RENDERED_TOOL_SUBDIRS`
(`working`, `archive`). Only `templates/` (and any other flat valid tools) are
discovered and validated.

```python
from infrastructure.tools.discovery import (
    NON_RENDERED_TOOL_SUBDIRS,  # {"working", "archive"}
    RENDERED_TOOL_SUBDIRS,      # {"templates"}
)
```

## Resolve a tool root

```python
from infrastructure.tools import resolve_tool_root

# Qualified name (head in templates/working/archive) resolves directly
path = resolve_tool_root(Path("."), "templates/template_code_executor")

# Bare name prefers tools/templates/<name>, then tools/<name>
path = resolve_tool_root(Path("."), "template_code_executor")
```

## Public scope

```python
from infrastructure.tools.public_scope import (
    PUBLIC_TOOL_NAMES,      # tuple of qualified names
    public_tool_infos,      # list[ToolInfo] present in this checkout
    public_tool_names,      # list[str] sorted
)
```

## Sidecar sync

```bash
uv run python -m infrastructure.tools.linking --dry-run
uv run python -m infrastructure.tools.linking
uv run python -m infrastructure.tools.linking --no-prune
```

```python
from infrastructure.tools.linking import (
    sync_private_tool_links, private_tools_root,
    is_managed_symlink, LinkSyncResult,
)

result = sync_private_tool_links(Path("."), dry_run=True)
# result.created / .updated / .removed / .skipped / .changed / .summary()
```

Private lifecycle tools mirror as: `private/working/<n>` → `tools/working/<n>`,
`private/archive/<n>` → `tools/archive/<n>`.

## Adding a new public tool

1. Create `tools/templates/<name>/` with `tools.yaml` + `scripts/`.
2. Append `"templates/<name>"` to `PUBLIC_TOOL_NAMES` in `public_scope.py`.
3. Refresh the skill manifest: `uv run python -m infrastructure.skills write`.

## Environment variables

| Variable | Effect |
|----------|--------|
| `TEMPLATE_TOOLS_ROOT` | Override private tools root path |
| `TEMPLATE_SKIP_TOOL_LINK_SYNC` | Skip auto-sync in orchestration CLI |

## Related modules

- [`infrastructure/fonds/`](../fonds/README.md) — closest analog (passive data stores)
- [`infrastructure/project/`](../project/README.md) — canonical analog (research projects)
- [`infrastructure/SKILL.md`](../SKILL.md) — infrastructure skill hub
- [`AGENTS.md`](AGENTS.md) — full API reference and boundaries
