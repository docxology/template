---
name: template-gates
description: |
  Optional validation gates for Hermes-plugin and advisory workflows.
  Includes cache validation, methods plan checks, line-count gates,
  security scanning, plugin export checks, and skill reachability checks.
  None run in the default pipeline; invoked explicitly when needed.
---
# SKILL: template-gates

Optional validation gate scripts.

## Invocation

```bash
uv run python scripts/gates/security_scan.py
uv run python scripts/gates/module_line_count_check.py
uv run python scripts/gates/methods_plan_check.py [--project <name>]
uv run python scripts/gates/gate_cache.py
uv run python scripts/gates/plugin_export_check.py
uv run python scripts/gates/skill_reachability_check.py
```

## Related

- `scripts/gates/AGENTS.md` — detailed gate documentation
- `infrastructure/validation/` — validation infrastructure