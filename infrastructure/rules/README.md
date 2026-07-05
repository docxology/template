# infrastructure/rules — Quick Reference

Soft guidelines and strong formal constraints for research templates.
Distinct from `projects/` (executable code) and `fonds/` (data resource pools).
Full discovery, validation, public scope, and private-sidecar symlink sync.

## Quick start

```python
from pathlib import Path
from infrastructure.rules import (
    discover_rules,
    resolve_rule_root,
    validate_rule_structure,
    RuleInfo,
    build_rule_info,
)
from infrastructure.rules.public_scope import (
    PUBLIC_RULE_NAMES,
    public_rule_infos,
    public_rule_names,
)
from infrastructure.rules.linking import sync_private_rule_links

# Discover all public exemplar rules
rules = discover_rules(Path("."))
for r in rules:
    print(r.qualified_name, r.rule_type, r.is_valid)

# Validate a rule
is_valid, msg = validate_rule_structure(Path("rules/templates/template_project_rules"))

# Check public CI scope
print(PUBLIC_RULE_NAMES)
# ('templates/template_project_rules', 'templates/template_manuscript_rules')

# Sync private sidecar (no-op when absent)
result = sync_private_rule_links(Path("."), dry_run=True)
print(result.summary())
```

## File layout

```
infrastructure/rules/
├── AGENTS.md          ← operating contract for agents
├── README.md          ← this file
├── SKILL.md           ← agent routing contract (YAML frontmatter)
├── __init__.py        ← re-exports: RuleInfo, discover_rules, resolve_rule_root, validate_rule_structure, build_rule_info
├── discovery.py       ← discover_rules, resolve_rule_root, NON_RENDERED_RULE_SUBDIRS, RENDERED_RULE_SUBDIRS
├── rules_info.py      ← RuleInfo dataclass + build_rule_info
├── validation.py      ← validate_rule_structure
├── public_scope.py    ← PUBLIC_RULE_NAMES, public_rule_infos, public_rule_names
└── linking.py         ← sidecar symlink sync
```

## Rule structure requirements

| Path | Required? | Description |
|------|-----------|-------------|
| `rules.yaml` | ✅ Yes | Manifest describing the rule set |
| `soft/` | At least one | Markdown guideline files (prose / prompt-style) |
| `strong/` | At least one | YAML or JSON formal constraint files |
| `scripts/` | Optional | Processing or generation scripts |
| `tests/` | Optional | Rule integrity tests |
| `examples/` | Optional | Worked examples |

No Python code required — rules are passive specifications.

## RuleInfo dataclass

```python
info: RuleInfo = build_rule_info(Path("rules/templates/template_project_rules"))
info.name           # "template_project_rules"
info.rule_type      # from rules.yaml "type", or "project"
info.has_soft       # True iff soft/ exists
info.has_strong     # True iff strong/ exists
info.is_valid       # True iff has_soft or has_strong
info.qualified_name # "template_project_rules" or "templates/template_project_rules"
```

## Discovery scope

`discover_rules()` scans `rules/` and skips `NON_RENDERED_RULE_SUBDIRS`
(`working`, `archive`). Only `templates/` (and any other flat valid rules) are
discovered and validated.

```python
from infrastructure.rules.discovery import (
    NON_RENDERED_RULE_SUBDIRS,  # {"working", "archive"}
    RENDERED_RULE_SUBDIRS,      # {"templates"}
)
```

## Resolve a rule root

```python
from infrastructure.rules import resolve_rule_root

# Qualified name (head in templates/working/archive) resolves directly
path = resolve_rule_root(Path("."), "templates/template_project_rules")

# Bare name prefers rules/templates/<name>, then rules/<name>
path = resolve_rule_root(Path("."), "template_project_rules")
```

## Public scope

```python
from infrastructure.rules.public_scope import (
    PUBLIC_RULE_NAMES,     # tuple of qualified names
    public_rule_infos,     # list[RuleInfo] present in this checkout
    public_rule_names,     # list[str] sorted
)
```

## Sidecar sync

```bash
uv run python -m infrastructure.rules.linking --dry-run
uv run python -m infrastructure.rules.linking
uv run python -m infrastructure.rules.linking --no-prune
```

```python
from infrastructure.rules.linking import (
    sync_private_rule_links, private_rules_root,
    is_managed_symlink, LinkSyncResult,
)

result = sync_private_rule_links(Path("."), dry_run=True)
# result.created / .updated / .removed / .skipped / .changed / .summary()
```

Private lifecycle rules mirror as: `private/working/<n>` → `rules/working/<n>`,
`private/archive/<n>` → `rules/archive/<n>`.

## Rule types

| `rule_type` | Domain |
|-------------|--------|
| `project` | Entire project governance (default) |
| `manuscript` | Manuscript style, structure, or content |
| `code` | Code quality, formatting, architecture |
| `data` | Data schema, validation, or quality |

## Adding a new public rule

1. Create `rules/templates/<name>/` with `rules.yaml` + at least one of `soft/` or `strong/`.
2. Append `"templates/<name>"` to `PUBLIC_RULE_NAMES` in `public_scope.py`.
3. Refresh the skill manifest: `uv run python -m infrastructure.skills write`.

## Environment variables

| Variable | Effect |
|----------|--------|
| `TEMPLATE_RULES_ROOT` | Override private rules root path |
| `TEMPLATE_SKIP_RULE_LINK_SYNC` | Skip auto-sync in orchestration CLI |

## Related modules

- [`infrastructure/fonds/`](../fonds/README.md) — resource pool analog (same pattern)
- [`infrastructure/project/`](../project/README.md) — canonical analog for research projects
- [`infrastructure/SKILL.md`](../SKILL.md) — infrastructure skill hub
- [`AGENTS.md`](AGENTS.md) — full API reference and boundaries
