# infrastructure/fonds — Quick Reference

Stable resource pools (bibliographies, contacts, datasets) for research
templates. Distinct from `projects/` (executable code). Full discovery,
validation, public scope, and private-sidecar symlink sync.

## Quick start

```python
from pathlib import Path
from infrastructure.fonds import (
    discover_fonds,
    resolve_fond_root,
    validate_fond_structure,
    FondInfo,
    build_fond_info,
)
from infrastructure.fonds.public_scope import (
    PUBLIC_FOND_NAMES,
    public_fond_infos,
    public_fond_names,
    public_fond_data_paths,
)
from infrastructure.fonds.linking import sync_private_fond_links

# Discover all public exemplar fonds
fonds = discover_fonds(Path("."))
for f in fonds:
    print(f.qualified_name, f.fond_type, f.is_valid)

# Validate a fond
is_valid, msg = validate_fond_structure(Path("fonds/templates/template_bibliography"))

# Check public CI scope
print(PUBLIC_FOND_NAMES)
# ('templates/template_bibliography', 'templates/template_contacts', 'templates/template_datasets')

# Sync private sidecar (no-op when absent)
result = sync_private_fond_links(Path("."), dry_run=True)
print(result.summary())
```

## File layout

```
infrastructure/fonds/
├── AGENTS.md          ← operating contract for agents
├── README.md          ← this file
├── SKILL.md           ← agent routing contract (YAML frontmatter)
├── __init__.py        ← re-exports: FondInfo, discover_fonds, resolve_fond_root, validate_fond_structure, build_fond_info
├── discovery.py       ← discover_fonds, resolve_fond_root, NON_RENDERED_FOND_SUBDIRS, RENDERED_FOND_SUBDIRS
├── fonds_info.py      ← FondInfo dataclass + build_fond_info
├── validation.py      ← validate_fond_structure
├── public_scope.py    ← PUBLIC_FOND_NAMES, public_fond_infos, public_fond_names, public_fond_data_paths
└── linking.py         ← sidecar symlink sync
```

## Fond structure requirements

| Path | Required? | Description |
|------|-----------|-------------|
| `fonds.yaml` | ✅ Yes | Manifest describing the resource pool |
| `data/` | ✅ Yes | Actual resource data |
| `manuscript/` | Optional | Cross-reference documentation |
| `scripts/` | Optional | Processing scripts |
| `tests/` | Optional | Data integrity tests |

No Python code required — fonds are passive data stores.

## FondInfo dataclass

```python
info: FondInfo = build_fond_info(Path("fonds/templates/template_bibliography"))
info.name           # "template_bibliography"
info.fond_type      # from fonds.yaml "type", or "generic"
info.has_data       # True iff data/ exists
info.has_manuscript # True iff manuscript/ exists
info.is_valid       # True iff has_data
info.qualified_name # "template_bibliography" or "templates/template_bibliography"
```

## Discovery scope

`discover_fonds()` scans `fonds/` and skips `NON_RENDERED_FOND_SUBDIRS`
(`working`, `archive`). Only `templates/` (and any other flat valid fonds) are
discovered and validated.

```python
from infrastructure.fonds.discovery import (
    NON_RENDERED_FOND_SUBDIRS,  # {"working", "archive"}
    RENDERED_FOND_SUBDIRS,      # {"templates"}
)
```

## Resolve a fond root

```python
from infrastructure.fonds import resolve_fond_root

# Qualified name (head in templates/working/archive) resolves directly
path = resolve_fond_root(Path("."), "templates/template_bibliography")

# Bare name prefers fonds/templates/<name>, then fonds/<name>
path = resolve_fond_root(Path("."), "template_bibliography")
```

## Public scope

```python
from infrastructure.fonds.public_scope import (
    PUBLIC_FOND_NAMES,         # tuple of qualified names
    public_fond_infos,         # list[FondInfo] present in this checkout
    public_fond_names,         # list[str] sorted
    public_fond_data_paths,    # list[Path] repo-relative data/ paths
)
```

## Sidecar sync

```bash
uv run python -m infrastructure.fonds.linking --dry-run
uv run python -m infrastructure.fonds.linking
uv run python -m infrastructure.fonds.linking --no-prune
```

```python
from infrastructure.fonds.linking import (
    sync_private_fond_links, private_fonds_root,
    is_managed_symlink, LinkSyncResult,
)

result = sync_private_fond_links(Path("."), dry_run=True)
# result.created / .updated / .removed / .skipped / .changed / .summary()
```

Private lifecycle fonds mirror as: `private/working/<n>` → `fonds/working/<n>`,
`private/archive/<n>` → `fonds/archive/<n>`.

## Adding a new public fond

1. Create `fonds/templates/<name>/` with `fonds.yaml` + `data/`.
2. Append `"templates/<name>"` to `PUBLIC_FOND_NAMES` in `public_scope.py`.
3. Refresh the skill manifest: `uv run python -m infrastructure.skills write`.

## Environment variables

| Variable | Effect |
|----------|--------|
| `TEMPLATE_FONDS_ROOT` | Override private fonds root path |
| `TEMPLATE_SKIP_FOND_LINK_SYNC` | Skip auto-sync in orchestration CLI |

## Related modules

- [`infrastructure/project/`](../project/README.md) — canonical analog for research projects
- [`infrastructure/SKILL.md`](../SKILL.md) — infrastructure skill hub
- [`AGENTS.md`](AGENTS.md) — full API reference and boundaries
