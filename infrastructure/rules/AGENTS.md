# infrastructure/rules/ — Agent Notes

## Purpose

Discovery, validation, scope, and private-sidecar symlink sync for the
top-level `rules/` directory — a parallel workspace to `projects/` and `fonds/`
for **specifications**: soft (prose/markdown guidelines, prompt-style) and
strong (yaml/json formal constraints) that govern how projects, manuscripts,
code, or data must be structured or authored.

The design mirrors `infrastructure/fonds/` adapted for specifications:

| Rules module | Fonds analog | Role |
|---|---|---|
| `discovery.py` | `fonds/discovery.py` | `discover_rules`, `resolve_rule_root`, subfolder constants |
| `rules_info.py` | `fonds/fonds_info.py` | `RuleInfo` dataclass + `build_rule_info` |
| `validation.py` | `fonds/validation.py` | `validate_rule_structure` |
| `public_scope.py` | `fonds/public_scope.py` | `PUBLIC_RULE_NAMES`, helpers |
| `linking.py` | `fonds/linking.py` | Private sidecar symlink sync |

## Module Map

| File | Exports |
|------|---------|
| `discovery.py` | `discover_rules`, `resolve_rule_root`, `NON_RENDERED_RULE_SUBDIRS`, `RENDERED_RULE_SUBDIRS` |
| `rules_info.py` | `RuleInfo`, `build_rule_info` |
| `validation.py` | `validate_rule_structure` |
| `public_scope.py` | `PUBLIC_RULE_NAMES`, `public_rule_infos`, `public_rule_names` |
| `linking.py` | `sync_private_rule_links`, `sync_active_rule_links`, `private_rules_root`, `is_managed_symlink`, `LIFECYCLE_LINK_DIRS`, `LinkSyncResult` |
| `__init__.py` | Re-exports: `RuleInfo`, `build_rule_info`, `discover_rules`, `resolve_rule_root`, `validate_rule_structure` |

## Public API

### `discovery.py` (re-exported from `infrastructure.rules`)

- `discover_rules(repo_root) -> list[RuleInfo]` — scan `rules/` for valid
  rules; skips `NON_RENDERED_RULE_SUBDIRS` (`working`, `archive`). Supports
  program directories (non-rule parent containing multiple rules) and category
  groupings (child dirs starting with `_`, one level deep).
- `resolve_rule_root(repo_root, rule_name) -> Path` — resolve a rule by
  qualified name. Qualified `<head>/<name>` (head in `templates/`, `working/`,
  `archive/`) resolves directly under `rules/<head>/<name>`. Bare names prefer
  `rules/templates/<name>`, then `rules/<name>`.
- `NON_RENDERED_RULE_SUBDIRS: frozenset[str]` — `{"working", "archive"}`.
- `RENDERED_RULE_SUBDIRS: frozenset[str]` — `{"templates"}`.

```python
from infrastructure.rules import discover_rules, resolve_rule_root
from pathlib import Path

rules = discover_rules(Path("."))
for r in rules:
    print(r.qualified_name, r.rule_type, r.is_valid)

rule_path = resolve_rule_root(Path("."), "templates/template_project_rules")
```

### `rules_info.py` (re-exported from `infrastructure.rules`)

- `RuleInfo` — dataclass for a discovered rule.
- `build_rule_info(rule_dir, program="") -> RuleInfo` — build from a directory;
  loads `rules.yaml` manifest.

```python
@dataclass
class RuleInfo:
    name: str              # Directory name
    path: Path             # Absolute path
    rule_type: str         # "type" field from rules.yaml, or "project"
    has_soft: bool         # Has soft/ directory (markdown guidelines)
    has_strong: bool       # Has strong/ directory (yaml/json formal specs)
    metadata: dict         # Raw rules.yaml content
    program: str           # Parent program dir ("" for standalone)

    @property
    def qualified_name(self) -> str: ...  # "name" or "program/name"
    @property
    def is_valid(self) -> bool: ...        # True iff has_soft or has_strong
```

### `validation.py` (re-exported from `infrastructure.rules`)

- `validate_rule_structure(rule_dir) -> tuple[bool, str]` — gate on required
  layout: `rules.yaml` manifest + at least one of `soft/` or `strong/`.

```python
is_valid, message = validate_rule_structure(Path("rules/my_rule"))
# (True, "Valid rule structure")
# (False, "Missing required file: rules.yaml")
# (False, "Missing required directory: at least one of soft/ or strong/ must exist")
```

**Required:** `rules.yaml`, and at least one of `soft/` or `strong/`
**Optional:** `scripts/`, `tests/`, `examples/`

### `public_scope.py`

- `PUBLIC_RULE_NAMES: tuple[str, ...]` — CI-safe roster of tracked exemplar
  rules. Currently: `("templates/template_project_rules", "templates/template_manuscript_rules")`.
- `public_rule_infos(repo_root) -> list[RuleInfo]` — discovered rules in the
  public roster present in this checkout.
- `public_rule_names(repo_root) -> list[str]` — sorted qualified names present.

### `linking.py`

- `sync_private_rule_links(repo_root, private_root=None, *, prune=True, dry_run=False) -> LinkSyncResult` —
  mirror private lifecycle folders into `rules/working/` and `rules/archive/`
  via symlinks. No-op when no private root is found.
- `sync_active_rule_links(...)` — compatibility alias.
- `private_rules_root(repo_root) -> Path | None` — resolve private sidecar
  root: `$TEMPLATE_RULES_ROOT` → `<repo_root>/.rules_root` → sibling `../rules`
  (requires `working/` + `archive/`).
- `is_managed_symlink(path, private_root) -> bool` — True iff path is a syncer-
  managed symlink (points into expected private lifecycle subtree).
- `LIFECYCLE_LINK_DIRS: dict[str, str]` — `{"working": "rules/working", "archive": "rules/archive"}`.
- `PROTECTED_NAMES: frozenset[str]` — bare exemplar names; syncer never touches.
- `ENV_VAR = "TEMPLATE_RULES_ROOT"`, `SKIP_ENV_VAR = "TEMPLATE_SKIP_RULE_LINK_SYNC"`.

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
uv run python -m infrastructure.rules.linking --dry-run
uv run python -m infrastructure.rules.linking
uv run python -m infrastructure.rules.linking --no-prune
uv run python -m infrastructure.rules.linking --private-root /path/to/rules
```

## Rule Structure Requirements

A valid rule must have:
- `rules.yaml` — manifest (required by `validate_rule_structure`)
- At least one of:
  - `soft/` — markdown guideline files (prompt-style prose)
  - `strong/` — yaml or json formal constraint files

Optional: `scripts/`, `tests/`, `examples/`

Unlike projects, no Python code is required — rules are passive specifications.

## Discovery Scope

```
rules/
├── templates/                     ← RENDERED_RULE_SUBDIRS (discovered by discover_rules)
│   ├── template_project_rules/    ← public exemplar
│   └── template_manuscript_rules/ ← public exemplar
├── working/                       ← NON_RENDERED_RULE_SUBDIRS (skipped, sidecar links)
│   └── myrule -> /private/rules/working/myrule
└── archive/                       ← NON_RENDERED_RULE_SUBDIRS (skipped, sidecar links)
    └── old_rule -> /private/rules/archive/old_rule
```

Category groupings (`_<category>/`) nest one level deep inside any directory.

## Rule Types

The `rule_type` field (from `rules.yaml` `type:`) can be one of:
- `project` — governance rules for an entire project (default)
- `manuscript` — style, structure, or content rules for manuscripts
- `code` — code quality, formatting, or architecture constraints
- `data` — data schema, validation, or quality specifications

## Boundaries

- **No project-pipeline coupling.** Does not participate in
  `discover_projects()` or `run.sh` stage execution.
- **`rules/` vs `projects/` vs `fonds/`.** Three orthogonal top-level namespaces.
- **Sidecar links are local-only.** Only `PUBLIC_RULE_NAMES` is CI-safe.
- **Safety invariants (never violated by linker):**
  - Real directories and unmanaged symlinks are never touched.
  - `PROTECTED_NAMES` (public exemplars) are always skipped.
  - No-op when the private sidecar is absent.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TEMPLATE_RULES_ROOT` | Override private rules root | unset |
| `TEMPLATE_SKIP_RULE_LINK_SYNC` | Skip auto-sync in orchestration CLI | unset |

## See Also

- [`../fonds/AGENTS.md`](../fonds/AGENTS.md) — fonds module (same pattern, resource pools)
- [`../project/AGENTS.md`](../project/AGENTS.md) — canonical project-layer analog
- [`../AGENTS.md`](../AGENTS.md) — infrastructure layer overview
- [`README.md`](README.md) — quick reference
- [`SKILL.md`](SKILL.md) — agent routing contract
