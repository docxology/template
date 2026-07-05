---
name: infrastructure-tools
description: "Skill for the tools module — discovery, validation, scope, and private-sidecar symlink sync for the top-level tools/ directory (executable entry points such as scripts, skills, and agents stored as passive manifests with scripts/ directories). Use when discovering tools (discover_tools), resolving a tool path (resolve_tool_root), validating tool structure (validate_tool_structure), building ToolInfo dataclasses (build_tool_info), checking PUBLIC_TOOL_NAMES for CI-safe scope (public_scope.py), syncing private lifecycle tools into the template checkout (sync_private_tool_links / linking.py), checking whether a path is a managed tool symlink (is_managed_symlink), or adding new public tool exemplars. Distinct from projects/ (full research environments) and fonds/ (passive data stores requiring data/ instead of scripts/)."
---

# Tools Module

Discovery, validation, scope, and sidecar symlink sync for the `tools/`
workspace — executable entry points (scripts, skills, agents), distinct from
`projects/` (executable research code) and `fonds/` (passive data stores).

## Modules

| File | Exports |
|------|---------|
| `__init__.py` | `ToolInfo`, `build_tool_info`, `discover_tools`, `resolve_tool_root`, `validate_tool_structure` |
| `discovery.py` | `discover_tools`, `resolve_tool_root`, `NON_RENDERED_TOOL_SUBDIRS`, `RENDERED_TOOL_SUBDIRS` |
| `tools_info.py` | `ToolInfo`, `build_tool_info` |
| `validation.py` | `validate_tool_structure` |
| `public_scope.py` | `PUBLIC_TOOL_NAMES`, `public_tool_infos`, `public_tool_names` |
| `linking.py` | `sync_private_tool_links`, `sync_active_tool_links`, `private_tools_root`, `is_managed_symlink`, `LIFECYCLE_LINK_DIRS`, `LinkSyncResult` |

## Discovery and validation

```python
from pathlib import Path
from infrastructure.tools import discover_tools, resolve_tool_root, validate_tool_structure, ToolInfo

# Discover all valid tools (skips working/, archive/)
tools: list[ToolInfo] = discover_tools(Path("."))
for t in tools:
    print(t.qualified_name, t.tool_type, t.is_valid)

# Resolve by name
path = resolve_tool_root(Path("."), "templates/template_code_executor")
path = resolve_tool_root(Path("."), "template_code_executor")  # bare name

# Validate structure (requires tools.yaml + scripts/)
is_valid, message = validate_tool_structure(Path("tools/templates/template_code_executor"))
```

## ToolInfo dataclass

```python
from infrastructure.tools import ToolInfo, build_tool_info

info = build_tool_info(Path("tools/templates/template_code_executor"))
info.name           # "template_code_executor"
info.tool_type      # "type" from tools.yaml, or "generic"
info.has_scripts    # True iff scripts/ exists
info.is_valid       # True iff has_scripts
info.qualified_name # "template_code_executor" or "program/name"
```

## Public scope

```python
from infrastructure.tools.public_scope import (
    PUBLIC_TOOL_NAMES,   # ('templates/template_code_executor',)
    public_tool_infos,   # list[ToolInfo] present in checkout
    public_tool_names,   # list[str] sorted
)
```

## Sidecar sync

```python
from pathlib import Path
from infrastructure.tools.linking import (
    sync_private_tool_links, private_tools_root,
    is_managed_symlink, LinkSyncResult,
)

root = private_tools_root(Path("."))   # Path | None
result: LinkSyncResult = sync_private_tool_links(Path("."), dry_run=True)
print(result.summary())
# result.created / .updated / .removed / .skipped / .changed
```

## CLI

```bash
uv run python -m infrastructure.tools.linking --dry-run
uv run python -m infrastructure.tools.linking
uv run python -m infrastructure.tools.linking --no-prune
uv run python -m infrastructure.tools.linking --private-root /path/to/tools
```

## Tool structure contract

| Path | Required? |
|------|-----------|
| `tools.yaml` | ✅ manifest |
| `scripts/` | ✅ executable entry points |
| `tests/` | optional |
| `docs/` | optional |

## Discovery scope constants

```python
from infrastructure.tools.discovery import NON_RENDERED_TOOL_SUBDIRS, RENDERED_TOOL_SUBDIRS
# NON_RENDERED_TOOL_SUBDIRS = frozenset({"working", "archive"})
# RENDERED_TOOL_SUBDIRS = frozenset({"templates"})
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `TEMPLATE_TOOLS_ROOT` | Override private tools root (highest precedence) |
| `TEMPLATE_SKIP_TOOL_LINK_SYNC` | Set to skip auto-sync in orchestration CLI |

## Safety invariants (linking.py)

- Real directories and unmanaged symlinks are **never** touched.
- `PROTECTED_NAMES` (public exemplars from `PUBLIC_TOOL_NAMES`) are always skipped.
- No-op and no error when the private sidecar is absent.

## See also

- [`AGENTS.md`](AGENTS.md) — full operating contract, boundaries, lifecycle layout
- [`../fonds/SKILL.md`](../fonds/SKILL.md) — closest analog (fonds module skill)
- [`../project/SKILL.md`](../project/SKILL.md) — canonical project-layer skill (same pattern)
