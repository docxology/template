---
name: infrastructure-rules
description: "Skill for the rules module — discovery, validation, scope, and private-sidecar symlink sync for the top-level rules/ directory (specifications include soft markdown guidelines and strong yaml/json formal constraints). Use when discovering rules (discover_rules), resolving a rule path (resolve_rule_root), validating rule structure (validate_rule_structure), building RuleInfo dataclasses (build_rule_info), checking PUBLIC_RULE_NAMES for CI-safe scope (public_scope.py), syncing private lifecycle rules into the template checkout (sync_private_rule_links / linking.py), checking whether a path is a managed rule symlink (is_managed_symlink), or adding new public rule exemplars. Distinct from projects/ (executable research code) and fonds/ (data resource pools); rules are passive specifications requiring rules.yaml + at least one of soft/ or strong/."
---

# Rules Module

Discovery, validation, scope, and sidecar symlink sync for the `rules/`
workspace — soft guidelines (markdown, prompt-style) and strong formal
constraints (yaml/json), distinct from `projects/` (executable code) and
`fonds/` (data resource pools).

## Modules

| File | Exports |
|------|---------| 
| `__init__.py` | `RuleInfo`, `build_rule_info`, `discover_rules`, `resolve_rule_root`, `validate_rule_structure` |
| `discovery.py` | `discover_rules`, `resolve_rule_root`, `NON_RENDERED_RULE_SUBDIRS`, `RENDERED_RULE_SUBDIRS` |
| `rules_info.py` | `RuleInfo`, `build_rule_info` |
| `validation.py` | `validate_rule_structure` |
| `public_scope.py` | `PUBLIC_RULE_NAMES`, `public_rule_infos`, `public_rule_names` |
| `linking.py` | `sync_private_rule_links`, `sync_active_rule_links`, `private_rules_root`, `is_managed_symlink`, `LIFECYCLE_LINK_DIRS`, `LinkSyncResult` |

## Discovery and validation

```python
from pathlib import Path
from infrastructure.rules import discover_rules, resolve_rule_root, validate_rule_structure, RuleInfo

# Discover all valid rules (skips working/, archive/)
rules: list[RuleInfo] = discover_rules(Path("."))
for r in rules:
    print(r.qualified_name, r.rule_type, r.is_valid)

# Resolve by name
path = resolve_rule_root(Path("."), "templates/template_project_rules")
path = resolve_rule_root(Path("."), "template_project_rules")  # bare name

# Validate structure (requires rules.yaml + soft/ or strong/)
is_valid, message = validate_rule_structure(Path("rules/templates/template_project_rules"))
```

## RuleInfo dataclass

```python
from infrastructure.rules import RuleInfo, build_rule_info

info = build_rule_info(Path("rules/templates/template_project_rules"))
info.name           # "template_project_rules"
info.rule_type      # "type" from rules.yaml, or "project"
info.has_soft       # True iff soft/ exists
info.has_strong     # True iff strong/ exists
info.is_valid       # True iff has_soft or has_strong
info.qualified_name # "template_project_rules" or "program/name"
```

## Public scope

```python
from infrastructure.rules.public_scope import (
    PUBLIC_RULE_NAMES,   # ('templates/template_project_rules', 'templates/template_manuscript_rules')
    public_rule_infos,   # list[RuleInfo] present in checkout
    public_rule_names,   # list[str] sorted
)
```

## Sidecar sync

```python
from pathlib import Path
from infrastructure.rules.linking import (
    sync_private_rule_links, private_rules_root,
    is_managed_symlink, LinkSyncResult,
)

root = private_rules_root(Path("."))   # Path | None
result: LinkSyncResult = sync_private_rule_links(Path("."), dry_run=True)
print(result.summary())
# result.created / .updated / .removed / .skipped / .changed
```

## CLI

```bash
uv run python -m infrastructure.rules.linking --dry-run
uv run python -m infrastructure.rules.linking
uv run python -m infrastructure.rules.linking --no-prune
uv run python -m infrastructure.rules.linking --private-root /path/to/rules
```

## Rule structure contract

| Path | Required? |
|------|-----------|
| `rules.yaml` | ✅ manifest |
| `soft/` | ✅ or `strong/` |
| `strong/` | ✅ or `soft/` |
| `scripts/` | optional |
| `tests/` | optional |
| `examples/` | optional |

## Discovery scope constants

```python
from infrastructure.rules.discovery import NON_RENDERED_RULE_SUBDIRS, RENDERED_RULE_SUBDIRS
# NON_RENDERED_RULE_SUBDIRS = frozenset({"working", "archive"})
# RENDERED_RULE_SUBDIRS = frozenset({"templates"})
```

## Rule types

| `rule_type` | Domain |
|-------------|--------|
| `project` | Entire project governance (default) |
| `manuscript` | Manuscript style, structure, content |
| `code` | Code quality, formatting, architecture |
| `data` | Data schema, validation, quality |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `TEMPLATE_RULES_ROOT` | Override private rules root (highest precedence) |
| `TEMPLATE_SKIP_RULE_LINK_SYNC` | Set to skip auto-sync in orchestration CLI |

## Safety invariants (linking.py)

- Real directories and unmanaged symlinks are **never** touched.
- `PROTECTED_NAMES` (public exemplars from `PUBLIC_RULE_NAMES`) are always skipped.
- No-op and no error when the private sidecar is absent.

## See also

- [`AGENTS.md`](AGENTS.md) — full operating contract, boundaries, lifecycle layout
- [`../fonds/SKILL.md`](../fonds/SKILL.md) — fonds module (same pattern, resource pools)
- [`../project/SKILL.md`](../project/SKILL.md) — canonical project-layer skill
