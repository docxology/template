# Methods Module

> **Read-only methods orchestration plans over pipeline contracts and evidence.**

**Location:** `infrastructure/methods/`

## Purpose

The methods module turns existing project surfaces into one inspectable plan:

- pipeline DAG stages and contracts
- manuscript methods/methodology files
- artifact manifest
- evidence registry
- validation commands

It does not execute analysis or rewrite manuscripts. It reports whether the
source and evidence layers needed for a publishable methods section are present.

## CLI

```bash
uv run python -m infrastructure.methods plan --project template_code_project --format markdown
uv run python -m infrastructure.methods plan --project template_code_project --format json --check
```

## API

```python
from infrastructure.methods import (
    build_methods_orchestration_plan,
    render_methods_orchestration_markdown,
    validate_methods_orchestration_plan,
)

plan = build_methods_orchestration_plan(".", "template_code_project")
issues = validate_methods_orchestration_plan(plan)
markdown = render_methods_orchestration_markdown(plan)
```

## Testing

```bash
uv run pytest tests/infra_tests/methods -q
```

## See Also

- [`../../guides/methods-orchestration.md`](../../guides/methods-orchestration.md)
- [`../../../infrastructure/methods/AGENTS.md`](../../../infrastructure/methods/AGENTS.md)
- [`../modules-guide.md`](../modules-guide.md)
