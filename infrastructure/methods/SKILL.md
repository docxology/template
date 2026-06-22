---
name: infrastructure-methods
description: Methods orchestration contract builder for template projects. Use when mapping pipeline stages, manuscript methods, artifact manifests, evidence registries, and validation commands into one reproducible methods plan.
---

# Methods Orchestration

Use this package when adding or auditing repo-wide research-methods wiring.

## Public API

```python
from infrastructure.methods import (
    build_methods_orchestration_plan,
    render_methods_orchestration_markdown,
    validate_methods_orchestration_plan,
)
```

## CLI

```bash
uv run python -m infrastructure.methods plan --project templates/template_code_project --format markdown
uv run python -m infrastructure.methods plan --project templates/template_code_project --format json --check
```

## Boundaries

- Read-only contract builder.
- No project business logic.
- No pipeline stage reimplementation.
- Validation evidence stays in project outputs and existing validation modules.
