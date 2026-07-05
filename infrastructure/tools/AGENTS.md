# infrastructure/tools/ — Agent Notes

## Purpose

Discovery, validation, scope, and private-sidecar symlink sync for the
top-level `tools/` directory — a parallel workspace to `projects/` and `fonds/`
for **executable entry points** (scripts, skills, agents) stored as passive
manifests with accompanying `scripts/` directories.

The design mirrors `infrastructure/fonds/` adapted for executable tools rather
than passive data stores:

| Tools module | Fonds analog | Role |
|---|---|---|
| `discovery.py` | `fonds/discovery.py` | `discover_tools`, `resolve_tool_root`, subfolder constants |
| `tools_info.py` | `fonds/fonds_info.py` | `ToolInfo` dataclass + `build_tool_info` |
| `validation.py` | `fonds/validation.py` | `validate_tool_structure` |
| `public_scope.py` | `fonds/public_scope.py` | `PUBLIC_TOOL_NAMES`, helpers |
| `linking.py` | `fonds/linking.py` | Private sidecar symlink sync |

## Module Map

| File | Exports |
|------|---------|
| `discovery.py` | `discover_tools`, `resolve_tool_root`, `NON_RENDERED_TOOL_SUBDIRS`, `RENDERED_TOOL_SUBDIRS` |
| `tools_info.py` | `ToolInfo`, `build_tool_info` |
| `validation.py` | `validate_tool_structure` |
| `public_scope.py` | `PUBLIC_TOOL_NAMES`, `public_tool_infos`, `public_tool_names` |
| `linking.py` | `sync_private_tool_links`, `sync_active_tool_links`, `private_tools_root`, `is_managed_symlink`, `LIFECYCLE_LINK_DIRS`, `LinkSyncResult` |
| `__init__.py` | Re-exports: `ToolInfo`, `build_tool_info`, `discover_tools`, `resolve_tool_root`, `validate_tool_structure` |

## Public API

### `discovery.py` (re-exported from `infrastructure.tools`)

- `discover_tools(repo_root) -> list[ToolInfo]` — scan `tools/` for valid
  tools; skips `NON_RENDERED_TOOL_SUBDIRS` (`working`, `archive`). Supports
  program directories and category groupings.
- `resolve_tool_root(repo_root, tool_name) -> Path` — resolve a tool by
  qualified name. Qualified `<head>/<name>` (head in `templates/`, `working/`,
  `archive/`) resolves directly under `tools/<head>/<name>`. Bare names prefer
  `tools/templates/<name>`, then `tools/<name>`.
- `NON_RENDERED_TOOL_SUBDIRS: frozenset[str]` — `{"working", "archive"}`.
- `RENDERED_TOOL_SUBDIRS: frozenset[str]` — `{"templates"}`.

```python
from infrastructure.tools import discover_tools, resolve_tool_root
from pathlib import Path

tools = discover_tools(Path("."))
for t in tools:
    print(t.qualified_name, t.tool_type, t.is_valid)

tool_path = resolve_tool_root(Path("."), "templates/template_code_executor")
```

### `tools_info.py` (re-exported from `infrastructure.tools`)

- `ToolInfo` — dataclass for a discovered tool.
- `build_tool_info(tool_dir, program="") -> ToolInfo` — build from a directory;
  loads `tools.yaml` manifest.

```python
@dataclass
class ToolInfo:
    name: str              # Directory name
    path: Path             # Absolute path
    tool_type: str         # "type" field from tools.yaml, or "generic"
    has_scripts: bool      # Has scripts/ directory
    has_tests: bool        # Has tests/ directory
    metadata: dict         # Raw tools.yaml content
    program: str           # Parent program dir ("" for standalone)

    @property
    def qualified_name(self) -> str: ...  # "name" or "program/name"
    @property
    def is_valid(self) -> bool: ...        # True iff has_scripts
```

### `validation.py` (re-exported from `infrastructure.tools`)

- `validate_tool_structure(tool_dir) -> tuple[bool, str]` — gate on required
  layout: `tools.yaml` manifest + `scripts/` directory.

```python
is_valid, message = validate_tool_structure(Path("tools/templates/template_code_executor"))
# (True, "Valid tool structure")
# (False, "Missing required file: tools.yaml")
# (False, "Missing required directory: scripts")
```

**Required:** `tools.yaml`, `scripts/`  
**Optional:** `tests/`, `docs/`

### `public_scope.py`

- `PUBLIC_TOOL_NAMES: tuple[str, ...]` — CI-safe roster of tracked exemplar
  tools. Initially: `("templates/template_code_executor",)`.
- `public_tool_infos(repo_root) -> list[ToolInfo]` — discovered tools in the
  public roster present in this checkout.
- `public_tool_names(repo_root) -> list[str]` — sorted qualified names present.

### `linking.py`

- `sync_private_tool_links(repo_root, private_root=None, *, prune=True, dry_run=False) -> LinkSyncResult` —
  mirror private lifecycle folders into `tools/working/` and `tools/archive/`
  via symlinks. No-op when no private root is found.
- `sync_active_tool_links(...)` — compatibility alias.
- `private_tools_root(repo_root) -> Path | None` — resolve private sidecar
  root: `$TEMPLATE_TOOLS_ROOT` → `<repo_root>/.tools_root` → sibling `../tools`
  (requires `working/` + `archive/`).
- `is_managed_symlink(path, private_root) -> bool` — True iff path is a syncer-
  managed symlink (points into expected private lifecycle subtree).
- `LIFECYCLE_LINK_DIRS: dict[str, str]` — `{"working": "tools/working", "archive": "tools/archive"}`.
- `PROTECTED_NAMES: frozenset[str]` — bare exemplar names; syncer never touches.
- `ENV_VAR = "TEMPLATE_TOOLS_ROOT"`, `SKIP_ENV_VAR = "TEMPLATE_SKIP_TOOL_LINK_SYNC"`.

```python
@dataclass
class LinkSyncResult:
    created: list[str]; updated: list[str]; removed: list[str]; skipped: list[str]
    private_root: Path | None
    @property
    def changed(self) -> bool: ...
    def summary(self) -> str: ...
```

**CLI:**

```bash
uv run python -m infrastructure.tools.linking --dry-run
uv run python -m infrastructure.tools.linking
uv run python -m infrastructure.tools.linking --no-prune
uv run python -m infrastructure.tools.linking --private-root /path/to/tools
```

## Tool Structure Requirements

A valid tool must have:
- `tools.yaml` — manifest (required by `validate_tool_structure`)
- `scripts/` — executable entry points (required)

Optional: `tests/`, `docs/`

Unlike fonds (passive data stores), tools are executable and require a `scripts/`
directory instead of a `data/` directory.

## Discovery Scope

```
tools/
├── templates/                       ← RENDERED_TOOL_SUBDIRS (discovered)
│   └── template_code_executor/      ← public exemplar
│       ├── tools.yaml
│       └── scripts/
├── working/                         ← NON_RENDERED_TOOL_SUBDIRS (skipped, sidecar links)
│   └── mytool -> /private/tools/working/mytool
└── archive/                         ← NON_RENDERED_TOOL_SUBDIRS (skipped, sidecar links)
    └── old_tool -> /private/tools/archive/old_tool
```

## Boundaries

- **No project-pipeline coupling.** Does not participate in
  `discover_projects()` or `run.sh` stage execution.
- **`tools/` vs `projects/` vs `fonds/`.** Orthogonal top-level namespaces.
- **Sidecar links are local-only.** Only `PUBLIC_TOOL_NAMES` is CI-safe.
- **Safety invariants (never violated by linker):**
  - Real directories and unmanaged symlinks are never touched.
  - `PROTECTED_NAMES` (public exemplars) are always skipped.
  - No-op when the private sidecar is absent.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TEMPLATE_TOOLS_ROOT` | Override private tools root | unset |
| `TEMPLATE_SKIP_TOOL_LINK_SYNC` | Skip auto-sync in orchestration CLI | unset |

## See Also

- [`../fonds/AGENTS.md`](../fonds/AGENTS.md) — fonds module (closest analog)
- [`../project/AGENTS.md`](../project/AGENTS.md) — project module (canonical pattern)
- [`../AGENTS.md`](../AGENTS.md) — infrastructure layer overview
- [`README.md`](README.md) — quick reference
- [`SKILL.md`](SKILL.md) — agent routing contract
