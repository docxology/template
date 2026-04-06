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
pytest tests/infra_tests/ --cov=infrastructure
```

## Project Tests (`projects/{name}/tests/`)

- Test algorithm correctness
- Verify statistical computations
- Check data processing
- Validate visualization output
- No dependency on build infrastructure

**Command:**

```bash
pytest projects/{name}/tests/ --cov=projects/{name}/src
```

## Integration Tests (`tests/integration/`)

- End-to-end pipeline validation
- Script execution testing
- Layer interaction verification
- Output completeness checking

**Command:**

```bash
pytest tests/integration/ --cov=projects/{name}/src --cov=infrastructure
```

## Full Test Suite

```bash
# All tests with coverage
pytest tests/ projects/{name}/tests/ --cov=infrastructure --cov=projects/{name}/src --cov-fail-under=70

# Generate HTML coverage report
pytest tests/ projects/{name}/tests/ --cov=infrastructure --cov=projects/{name}/src --cov-report=html
open htmlcov/index.html
```

## Coverage Requirements

| Layer | Minimum | Current | Target |
|-------|---------|---------|--------|
| **Infrastructure** (`infrastructure/`) | 60% | 83.33% | Exceeds stretch goal |
| **Project** (`projects/{name}/src/`) | 90% | 100% | Full coverage |

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

**Solution:** Ensure `tests/conftest.py` includes `projects/{name}/` on path:

```python
import sys
sys.path.insert(0, os.path.join(repo_root, "projects", project_name))
```

### Layer Violations

**Error:** Infrastructure module imports from project

**Solution:** Refactor to remove dependency or move code to appropriate layer

**Check:**

```bash
# Find infrastructure imports of project code
grep -r "from projects\." infrastructure/
grep -r "import projects\." infrastructure/
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
