---
name: infrastructure-methods
description: Methods orchestration contract builder for template projects. Use when mapping pipeline stages, manuscript methods, artifact manifests, evidence registries, figures, claim ledgers, experiment plans, and validation commands into one reproducible methods plan.
---

# Methods Orchestration

Use this package when adding or auditing repo-wide research-methods wiring.

## Public API

```python
from infrastructure.methods import (
    audit_methods_projects,
    audit_public_methods,
    build_methods_orchestration_plan,
    render_methods_orchestration_markdown,
    validate_methods_orchestration_plan,
)
```

## CLI

```bash
uv run python -m infrastructure.methods plan --project templates/template_code_project --format markdown
uv run python -m infrastructure.methods plan --all-public --artifact-mode source --format json
uv run python -m infrastructure.methods plan --all-public --artifact-mode rendered --format json
```

## Boundaries

- Read-only contract builder.
- No project business logic.
- No pipeline stage reimplementation.
- Validation evidence stays in project outputs and existing validation modules.
- Optional figure registries, claim ledgers, and experiment plans are reported
  only when their source files exist; missing optional surfaces are rendered as
  `null`/`not present`, not as fabricated evidence.
