# infrastructure/fonds/ — Agent Notes

## Purpose

Discovery, validation, scope, and private-sidecar symlink sync for the
top-level `fonds/` directory — a parallel workspace to `projects/` for
**archival collection units** (fonds in the archival sense: stable pools of
reusable research resources — bibliographies, contact registries, dataset
catalogs — distinct from executable research projects).

The design mirrors `infrastructure/project/` adapted for passive data stores:

| Fonds module | Project analog | Role |
|---|---|---|
| `discovery.py` | `project/discovery.py` | `discover_fonds`, `resolve_fond_root`, subfolder constants |
| `fonds_info.py` | `project/discovery.py` (partial) | `FondInfo` dataclass + `build_fond_info` |
| `validation.py` | `project/discovery.py` (partial) | `validate_fond_structure` |
| `public_scope.py` | `project/public_scope.py` | `PUBLIC_FOND_NAMES`, helpers |
| `linking.py` | `project/linking.py` | Private sidecar symlink sync |

## Module Map

| File | Exports |
|------|---------|
| `discovery.py` | `discover_fonds`, `resolve_fond_root`, `NON_RENDERED_FOND_SUBDIRS`, `RENDERED_FOND_SUBDIRS` |
| `fonds_info.py` | `FondInfo`, `build_fond_info` |
| `validation.py` | `validate_fond_structure` |
| `public_scope.py` | `PUBLIC_FOND_NAMES`, `public_fond_infos`, `public_fond_names`, `public_fond_data_paths` |
| `linking.py` | `sync_private_fond_links`, `sync_active_fond_links`, `private_fonds_root`, `is_managed_symlink`, `LIFECYCLE_LINK_DIRS`, `LinkSyncResult` |
| `__init__.py` | Re-exports: `FondInfo`, `build_fond_info`, `discover_fonds`, `resolve_fond_root`, `validate_fond_structure` |

## Public API

### `discovery.py` (re-exported from `infrastructure.fonds`)

- `discover_fonds(repo_root) -> list[FondInfo]` — scan `fonds/` for valid
  fonds; skips `NON_RENDERED_FOND_SUBDIRS` (`working`, `archive`). Supports
  program directories (non-fond parent containing multiple fonds) and category
  groupings (child dirs starting with `_`, one level deep).
- `resolve_fond_root(repo_root, fond_name) -> Path` — resolve a fond by
  qualified name. Qualified `<head>/<name>` (head in `templates/`, `working/`,
  `archive/`) resolves directly under `fonds/<head>/<name>`. Bare names prefer
  `fonds/templates/<name>`, then `fonds/<name>`.
- `NON_RENDERED_FOND_SUBDIRS: frozenset[str]` — `{"working", "archive"}`.
- `RENDERED_FOND_SUBDIRS: frozenset[str]` — `{"templates"}`.

```python
from infrastructure.fonds import discover_fonds, resolve_fond_root
from pathlib import Path

fonds = discover_fonds(Path("."))
for f in fonds:
    print(f.qualified_name, f.fond_type, f.is_valid)

fond_path = resolve_fond_root(Path("."), "templates/template_bibliography")
```

### `fonds_info.py` (re-exported from `infrastructure.fonds`)

- `FondInfo` — dataclass for a discovered fond.
- `build_fond_info(fond_dir, program="") -> FondInfo` — build from a directory;
  loads `fonds.yaml` manifest.

```python
@dataclass
class FondInfo:
    name: str              # Directory name
    path: Path             # Absolute path
    fond_type: str         # "type" field from fonds.yaml, or "generic"
    has_data: bool         # Has data/ directory
    has_manuscript: bool   # Has manuscript/ directory
    metadata: dict         # Raw fonds.yaml content
    program: str           # Parent program dir ("" for standalone)

    @property
    def qualified_name(self) -> str: ...  # "name" or "program/name"
    @property
    def is_valid(self) -> bool: ...        # True iff has_data
```

### `validation.py` (re-exported from `infrastructure.fonds`)

- `validate_fond_structure(fond_dir) -> tuple[bool, str]` — gate on required
  layout: `fonds.yaml` manifest + `data/` directory.

```python
is_valid, message = validate_fond_structure(Path("fonds/my_bibliography"))
# (True, "Valid fond structure")
# (False, "Missing required file: fonds.yaml")
# (False, "Missing required directory: data")
```

**Required:** `fonds.yaml`, `data/`
**Optional:** `manuscript/`, `scripts/`, `tests/`

### `public_scope.py`

- `PUBLIC_FOND_NAMES: tuple[str, ...]` — CI-safe roster of tracked exemplar
  fonds. Currently: `("templates/template_bibliography", "templates/template_contacts", "templates/template_datasets")`.
- `public_fond_infos(repo_root) -> list[FondInfo]` — discovered fonds in the
  public roster present in this checkout.
- `public_fond_names(repo_root) -> list[str]` — sorted qualified names present.
- `public_fond_data_paths(repo_root) -> list[Path]` — `data/` paths for public
  fonds (repo-relative; for CI lint/type-check scope).

### `linking.py`

- `sync_private_fond_links(repo_root, private_root=None, *, prune=True, dry_run=False) -> LinkSyncResult` —
  mirror private lifecycle folders into `fonds/working/` and `fonds/archive/`
  via symlinks. No-op when no private root is found.
- `sync_active_fond_links(...)` — compatibility alias.
- `private_fonds_root(repo_root) -> Path | None` — resolve private sidecar
  root: `$TEMPLATE_FONDS_ROOT` → `<repo_root>/.fonds_root` → sibling `../fonds`
  (requires `working/` + `archive/`).
- `is_managed_symlink(path, private_root) -> bool` — True iff path is a syncer-
  managed symlink (points into expected private lifecycle subtree).
- `LIFECYCLE_LINK_DIRS: dict[str, str]` — `{"working": "fonds/working", "archive": "fonds/archive"}`.
- `PROTECTED_NAMES: frozenset[str]` — bare exemplar names; syncer never touches.
- `ENV_VAR = "TEMPLATE_FONDS_ROOT"`, `SKIP_ENV_VAR = "TEMPLATE_SKIP_FOND_LINK_SYNC"`.

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
uv run python -m infrastructure.fonds.linking --dry-run
uv run python -m infrastructure.fonds.linking
uv run python -m infrastructure.fonds.linking --no-prune
uv run python -m infrastructure.fonds.linking --private-root /path/to/fonds
```

## Fond Structure Requirements

A valid fond must have:
- `fonds.yaml` — manifest (required by `validate_fond_structure`)
- `data/` — resource data (required)

Optional: `manuscript/`, `scripts/`, `tests/`

Unlike projects, no Python code is required — fonds are passive data stores.

## Discovery Scope

```
fonds/
├── templates/               ← RENDERED_FOND_SUBDIRS (discovered by discover_fonds)
│   ├── template_bibliography/   ← public exemplar
│   ├── template_contacts/
│   └── template_datasets/
├── working/                 ← NON_RENDERED_FOND_SUBDIRS (skipped, sidecar links)
│   └── myfond -> /private/fonds/working/myfond
└── archive/                 ← NON_RENDERED_FOND_SUBDIRS (skipped, sidecar links)
    └── old_fond -> /private/fonds/archive/old_fond
```

Category groupings (`_<category>/`) nest one level deep inside any directory.

## Boundaries

- **No project-pipeline coupling.** Does not participate in
  `discover_projects()` or `run.sh` stage execution.
- **`fonds/` vs `projects/`.** Orthogonal top-level namespaces.
- **Sidecar links are local-only.** Only `PUBLIC_FOND_NAMES` is CI-safe.
- **Safety invariants (never violated by linker):**
  - Real directories and unmanaged symlinks are never touched.
  - `PROTECTED_NAMES` (public exemplars) are always skipped.
  - No-op when the private sidecar is absent.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TEMPLATE_FONDS_ROOT` | Override private fonds root | unset |
| `TEMPLATE_SKIP_FOND_LINK_SYNC` | Skip auto-sync in orchestration CLI | unset |

## See Also

- [`../project/AGENTS.md`](../project/AGENTS.md) — canonical project-layer analog
- [`../AGENTS.md`](../AGENTS.md) — infrastructure layer overview
- [`README.md`](README.md) — quick reference
- [`SKILL.md`](SKILL.md) — agent routing contract
