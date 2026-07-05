# CLAUDE.md — template_pools_rules_tools

Agent guidance for code agents (Claude, Codex, Gemini, etc.) working in
`projects/templates/template_pools_rules_tools/`.

---

## Project purpose

Exemplar demonstrating how a project reads from the three top-level
resource directories without writing back to them:

| Resource dir | What this project reads |
|---|---|
| `fonds/templates/` | bibliography, contacts, datasets fonds |
| `rules/templates/` | template_project_rules, template_manuscript_rules |
| `tools/templates/` | all tool manifests under `tools/templates/` |

---

## Key source modules

| Module | Role |
|---|---|
| `src/types.py` | All TypedDict definitions — **edit here first** when adding return fields |
| `src/fonds_reader.py` | Reads 3 fond types; returns typed dicts |
| `src/rules_applier.py` | Loads soft/strong rules; returns typed dicts |
| `src/tools_invoker.py` | Discovers tool manifests; returns typed dicts |
| `src/integration.py` | Orchestrates all three; adds `generate_figure_data()` |
| `src/__init__.py` | Re-exports all public symbols |

---

## Invariants you must maintain

1. **No `Any` in public signatures.** Use `object` for truly-unknown YAML
   payloads; use specific TypedDicts for all function return types.
2. **No writes to fonds/, rules/, or tools/.** These are read-only from
   this project's perspective.
3. **Graceful fallback everywhere.** Functions return `None` or empty
   collections when files are absent — they never raise.
4. **`src/types.py` is the single source of truth** for all TypedDict shapes.
   Do not declare inline dicts in other modules.
5. **`__all__` in every module.** Keep `src/__init__.py` in sync.

---

## Adding a new return field

1. Add the field to the appropriate TypedDict in `src/types.py`.
2. Update the producing function to populate it.
3. Update any downstream callers in `integration.py`.
4. Add or update the corresponding test.
5. Run mypy to confirm no new errors.

---

## Running tests

```bash
# From repository root:
uv run pytest projects/templates/template_pools_rules_tools/tests/ -v \
    --cov=projects/templates/template_pools_rules_tools/src \
    --cov-fail-under=90
```

---

## Type-checking

```bash
# From repository root:
uv run mypy projects/templates/template_pools_rules_tools/src \
    --config-file projects/templates/template_pools_rules_tools/pyproject.toml
```

---

## Standalone use (no monorepo)

See `STANDALONE.md` for instructions on using this project outside the
full template repository.

---

## Error recovery pattern

All `src/` functions catch exceptions internally and log structured warnings
via the module-level `logger`. Callers should inspect the `warnings` list
inside returned dicts (e.g. `RuleSetResult.warnings`) for structured error
reports rather than relying on exceptions.

---

## Common pitfalls

- **Repo-root resolution** uses `pathlib.Path(__file__).resolve().parents[4]`.
  This is correct for the nested path
  `projects/templates/template_pools_rules_tools/src/<module>.py`.
  Do not change this without updating all four modules.
- **`pathlib.Path` objects in TypedDicts** (`ToolEntry.path`) are not JSON-
  serialisable. Convert to `str` before serialising to JSON.
- **YAML `safe_load` returns `None`** for empty files. The code guards with
  `or []` / `or {}` where appropriate — preserve those guards.
- **`csv.DictReader` yields `dict[str, str]`** — all values are strings even
  for numeric columns. Callers must cast if needed.
