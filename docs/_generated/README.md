# Generated documentation snippets

Files here are produced by repository scripts so human-written docs stay aligned with code and layout.

| File | Generator |
|------|-----------|
| [active_projects.md](active_projects.md) | `uv run python scripts/generate_active_projects_doc.py` |

## Policy

- **[active_projects.md](active_projects.md)** lists active `projects/` names from `discover_projects()`. Treat it as authoritative; do not duplicate that roster in RUN_GUIDE, PAI, security tables, or similar.
- For walkthroughs, commands, and “see also” paths, use **`projects/code_project/`** as the control-positive exemplar unless the doc’s purpose is to compare layouts.
- Describe other work as folder patterns (`projects/{name}/`, `projects_in_progress/`, `projects_archive/`) rather than enumerating sibling projects in prose.

## Regeneration

Run after adding, removing, or renaming directories under `projects/`:

```bash
uv run python scripts/generate_active_projects_doc.py
```
