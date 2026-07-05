---
name: infrastructure-fonds
description: "Skill for the fonds module — discovery, validation, scope, and private-sidecar symlink sync for the top-level fonds/ directory (archival collection units such as bibliographies, contact registries, and dataset catalogs). Use when discovering fonds (discover_fonds), resolving a fond path (resolve_fond_root), validating fond structure (validate_fond_structure), building FondInfo dataclasses (build_fond_info), checking PUBLIC_FOND_NAMES for CI-safe scope (public_scope.py), syncing private lifecycle fonds into the template checkout (sync_private_fond_links / linking.py), checking whether a path is a managed fond symlink (is_managed_symlink), or adding new public fonds exemplars. Distinct from projects/ (executable research code); fonds are passive data stores requiring fonds.yaml + data/ (not src/ + tests/)."
---

# Fonds Module

Discovery, validation, scope, and sidecar symlink sync for the `fonds/`
workspace — stable resource pools (bibliographies, contacts, datasets),
distinct from `projects/` (executable code).

## Modules

| File | Exports |
|------|---------|
| `__init__.py` | `FondInfo`, `build_fond_info`, `discover_fonds`, `resolve_fond_root`, `validate_fond_structure` |
| `discovery.py` | `discover_fonds`, `resolve_fond_root`, `NON_RENDERED_FOND_SUBDIRS`, `RENDERED_FOND_SUBDIRS` |
| `fonds_info.py` | `FondInfo`, `build_fond_info` |
| `validation.py` | `validate_fond_structure` |
| `public_scope.py` | `PUBLIC_FOND_NAMES`, `public_fond_infos`, `public_fond_names`, `public_fond_data_paths` |
| `linking.py` | `sync_private_fond_links`, `sync_active_fond_links`, `private_fonds_root`, `is_managed_symlink`, `LIFECYCLE_LINK_DIRS`, `LinkSyncResult` |

## Discovery and validation

```python
from pathlib import Path
from infrastructure.fonds import discover_fonds, resolve_fond_root, validate_fond_structure, FondInfo

# Discover all valid fonds (skips working/, archive/)
fonds: list[FondInfo] = discover_fonds(Path("."))
for f in fonds:
    print(f.qualified_name, f.fond_type, f.is_valid)

# Resolve by name
path = resolve_fond_root(Path("."), "templates/template_bibliography")
path = resolve_fond_root(Path("."), "template_bibliography")  # bare name

# Validate structure (requires fonds.yaml + data/)
is_valid, message = validate_fond_structure(Path("fonds/templates/template_bibliography"))
```

## FondInfo dataclass

```python
from infrastructure.fonds import FondInfo, build_fond_info

info = build_fond_info(Path("fonds/templates/template_bibliography"))
info.name           # "template_bibliography"
info.fond_type      # "type" from fonds.yaml, or "generic"
info.has_data       # True iff data/ exists
info.is_valid       # True iff has_data
info.qualified_name # "template_bibliography" or "program/name"
```

## Public scope

```python
from infrastructure.fonds.public_scope import (
    PUBLIC_FOND_NAMES,       # ('templates/template_bibliography', ...)
    public_fond_infos,       # list[FondInfo] present in checkout
    public_fond_names,       # list[str] sorted
    public_fond_data_paths,  # list[Path] repo-relative data/ paths for CI scope
)
```

## Sidecar sync

```python
from pathlib import Path
from infrastructure.fonds.linking import (
    sync_private_fond_links, private_fonds_root,
    is_managed_symlink, LinkSyncResult,
)

root = private_fonds_root(Path("."))   # Path | None
result: LinkSyncResult = sync_private_fond_links(Path("."), dry_run=True)
print(result.summary())
# result.created / .updated / .removed / .skipped / .changed
```

## CLI

```bash
uv run python -m infrastructure.fonds.linking --dry-run
uv run python -m infrastructure.fonds.linking
uv run python -m infrastructure.fonds.linking --no-prune
uv run python -m infrastructure.fonds.linking --private-root /path/to/fonds
```

## Fond structure contract

| Path | Required? |
|------|-----------|
| `fonds.yaml` | ✅ manifest |
| `data/` | ✅ resource data |
| `manuscript/` | optional |
| `scripts/` | optional |
| `tests/` | optional |

## Discovery scope constants

```python
from infrastructure.fonds.discovery import NON_RENDERED_FOND_SUBDIRS, RENDERED_FOND_SUBDIRS
# NON_RENDERED_FOND_SUBDIRS = frozenset({"working", "archive"})
# RENDERED_FOND_SUBDIRS = frozenset({"templates"})
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `TEMPLATE_FONDS_ROOT` | Override private fonds root (highest precedence) |
| `TEMPLATE_SKIP_FOND_LINK_SYNC` | Set to skip auto-sync in orchestration CLI |

## Safety invariants (linking.py)

- Real directories and unmanaged symlinks are **never** touched.
- `PROTECTED_NAMES` (public exemplars from `PUBLIC_FOND_NAMES`) are always skipped.
- No-op and no error when the private sidecar is absent.

## See also

- [`AGENTS.md`](AGENTS.md) — full operating contract, boundaries, lifecycle layout
- [`../project/SKILL.md`](../project/SKILL.md) — canonical project-layer skill (same pattern)
