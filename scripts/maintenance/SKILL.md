---
name: template-maintenance
description: |
  On-demand maintenance helpers for the template repository. Includes
  workspace management, project info display, working-project rendering,
  PDF re-rendering, executive output organization, test supplement merging,
  batch source improvement, pre-commit setup, and CodeGraph index helpers.
  None run in the default pipeline or CI.
---
# SKILL: template-maintenance

Maintenance orchestrators for repository upkeep.

## Invocation

```bash
uv run python scripts/maintenance/setup_pre_commit.py
uv run python scripts/maintenance/manage_workspace.py status
uv run python scripts/maintenance/render_working_projects.py
uv run python scripts/maintenance/codegraph_local.py commands .
```

## Related

- `scripts/maintenance/AGENTS.md` — detailed documentation
- `infrastructure/project/` — workspace and project management