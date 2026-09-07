# Testing Strategy

> **Test organization and execution** across the two-layer architecture

**Quick Reference:** [Two-Layer Architecture](two-layer-architecture.md) | [Testing Guide](../development/testing/testing-guide.md) | [Workflow](../core/workflow.md)

This document describes how tests are structured and run across both layers of the architecture.

---

## Infrastructure Tests (`tests/infra_tests/`)

- Verify build orchestration works
- Test validation logic
- Check file integrity checking
- Validate PDF generation
- No dependency on scientific code

**Command:**

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure
```

## Project Tests (`projects/{name}/tests/`)

- Test algorithm correctness
- Verify statistical computations
- Check data processing
- Validate visualization output
- May use generic infrastructure APIs, but must test project-owned scientific
  behavior rather than duplicate infrastructure tests

**Command:**

```bash
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_code_project --project-only --profile release
```

## Integration Tests (`tests/integration/`)

- End-to-end pipeline validation
- Script execution testing
- Layer interaction verification
- Output completeness checking

**Command:**

```bash
uv run pytest tests/integration/ --cov=projects/{name}/src --cov=infrastructure
```

## Release test surfaces

```bash
# Infrastructure release profile and its 60% aggregate floor
uv run python scripts/pipeline/stage_01_test.py --infra-only --profile release

# Every public project in a separate pytest process; each project keeps its own 90% floor
uv run python scripts/pipeline/stage_01_test.py \
  --project-only --all-projects --public-projects --profile release
```

Do not concatenate every `projects/*/tests/` path into one pytest invocation:
several projects intentionally use the same `tests.conftest` package name. The
stage runner isolates projects and combines only the resulting coverage data.

## Coverage Requirements

| Layer | Minimum | Current | Target |
|-------|---------|---------|--------|
| **Infrastructure** (`infrastructure/`) | 60% | live → [`../_generated/COUNTS.md`](../_generated/COUNTS.md) | gated by CI; never hardcode the percentage in prose |
| **Project** (`projects/{name}/src/`) | 90% | live → `COUNTS.md` | per-exemplar live percentages live there |

## Best Practices

### For Infrastructure Development

✅ **Do:**
- Write generic, reusable code
- Document with project-independent examples
- Test extensively with real scenarios
- Handle errors gracefully
- Provide clear logging

❌ **Don't:**
- Import scientific modules
- Assume specific research domain
- Skip tests to ship features
- Hardcode project-specific values
- Mix concerns (building vs. computation)

### For Scientific Development

✅ **Do:**
- Use infrastructure tools for document management
- Follow thin orchestrator pattern in `projects/{name}/scripts/`
- Implement algorithms in `projects/{name}/src/` modules
- Test with data
- Document domain-specific concepts

❌ **Don't:**
- Duplicate build/validation logic
- Implement document generation in scripts
- Skip layer abstraction
- Mix orchestration with computation

### Logging Best Practices

```python
# In project scripts — mark layer transitions
import logging
logger = logging.getLogger(__name__)

logger.info("[LAYER-2-PROJECT] Starting simulation...")
logger.info("[LAYER-1-INFRASTRUCTURE] Using FigureManager for output...")
```

```bash
# In build scripts — mark phase transitions
log_info "━━━ LAYER 1: Infrastructure Validation ━━━"
log_info "━━━ LAYER 2: Scientific Computation ━━━"
```

---

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'project.src'`

**Solution:** Reproduce through the project-aware stage runner shown above. It
runs pyproject-based projects with `uv run --directory`, injects the test-runner
dependencies, and preserves the project import root. If the focused command
still fails, fix the project's package metadata or documented script bootstrap;
do not hide an invalid install by adding a global ad hoc `sys.path` mutation.

### Layer Violations

**Error:** Infrastructure module imports from project

**Solution:** Refactor to remove dependency or move code to appropriate layer

**Check:**

```bash
# Find infrastructure imports of project code
rg "from projects\.|import projects\." infrastructure/
```

### Mixed Concerns

**Error:** Build logic in project module

**Solution:** Move to infrastructure layer or extract into separate module

---

**Related Documentation:**

- [Two-Layer Architecture](two-layer-architecture.md) — Full architecture guide
- [Decision Tree](decision-tree.md) — Code placement flowchart
- [Testing Guide](../development/testing/testing-guide.md) — Testing requirements
- [Workflow](../core/workflow.md) — Development process
