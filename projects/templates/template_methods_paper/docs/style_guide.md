# Style Guide

This document defines the coding and communication style for the
`template_methods_paper` exemplar. Every rule has a concrete consequence for
test correctness, reproducibility, or manuscript accuracy.

---

## 1. Zero-Mock Policy

The most critical rule is the absolute prohibition of mocking. The following
are **forbidden** anywhere inside
`projects/templates/template_methods_paper/tests/`:

- `import unittest.mock`
- `from unittest.mock import MagicMock, patch, create_autospec, Mock, AsyncMock`
- `@patch(...)` decorators
- monkeypatching a real function with a fake callable

**Why**: `src/methods_dsl/` contains pure model/validation/compilation logic.
You can always test it with a real `Method`/`Step`/`Quantity` and real
results. A test that requires a mock tests the wrong thing.

**Forbidden pattern**:
```python
# BAD — tests behavior, not correctness
from unittest.mock import MagicMock
method = MagicMock()
compile_method(method)
```

**Correct pattern** (from `tests/test_compiler.py`):
```python
# GOOD — tests real output with a designed Method fixture
plan = compile_method(linear_method)
assert plan.method_name == "LinearDemo"
assert len(plan.steps) == 3
```

**Verify cleanliness**:
```bash
grep -r "unittest.mock\|MagicMock\|@patch" projects/templates/template_methods_paper/tests/ || echo "Clean"
```

---

## 2. Library Purity (no infrastructure, no plotting, no I/O)

| File | May Import | Must NOT Import / Do |
|---|---|---|
| `src/methods_dsl/*.py` (except `_logging.py`) | stdlib (`dataclasses`, `enum`, `hashlib`, `json`, `typing`) | **Anything from `infrastructure.*`; matplotlib; file writes** |
| `src/methods_dsl/_logging.py` | `infrastructure.core.logging.utils` (the one sanctioned exception) | Anything else from `infrastructure.*` |
| `scripts/methods_analysis.py` | `src.methods_dsl`, `src.project_paths`, `matplotlib` | Gate, compilation, or scheduling logic |
| `tests/test_*.py` | `src.*`, `pytest` | `unittest.mock.*`, `infrastructure.*` |

**Verify `src/methods_dsl/` is clean outside the declared exception**:
```bash
grep -rnE "^(from|import) infrastructure" projects/templates/template_methods_paper/src/methods_dsl/ \
    | grep -v "_logging.py" || echo "Clean"
```

---

## 3. The Thin Orchestrator Pattern

`scripts/methods_analysis.py` may call gates/compiler/exporters, plot the
returned data, and write files, but must not implement validation or
scheduling logic that belongs in `src/methods_dsl/`.

**Forbidden** — gate logic re-implemented in a script:
```python
# BAD — scheduling logic belongs in src/methods_dsl/compiler.py
ready = [s for s in method.steps if not s.depends_on]
```

**Correct** — call the tested function:
```python
# GOOD
plan = compile_method(method)
```

**Decision rule**: if a line of code in a script validates, schedules, or
hashes a `Method` (not just exports/plots an already-compiled `Plan`), move
it to `src/methods_dsl/` and write a test.

---

## 4. Manuscript "Show, Not Tell"

Use explicit, verifiable references instead of vague descriptions.

| BAD (vague) | GOOD (concrete) |
|---|---|
| "The compiler figures out a sensible order." | "`src/methods_dsl/compiler.py::topological_order()` schedules steps with Kahn's algorithm, breaking ties by ascending `step_id`." |
| "We validated the methods." | "`tests/test_validation.py` asserts each of the four staged gates against `conftest.py`'s fixtures, including one fixture per gate-failure mode." |

---

## 5. Explicit File Paths

Refer to files by their path relative to the repository root:

| Short Name | Path (from repo root) |
|---|---|
| method model | `projects/templates/template_methods_paper/src/methods_dsl/model.py` |
| compiler | `projects/templates/template_methods_paper/src/methods_dsl/compiler.py` |
| analysis script | `projects/templates/template_methods_paper/scripts/methods_analysis.py` |
| config | `projects/templates/template_methods_paper/manuscript/config.yaml` |
| worked examples | `projects/templates/template_methods_paper/src/methods_dsl/examples_methods.py` |

Never hardcode an absolute filesystem path in code — resolve relative to the
project root (see `src/project_paths.py`).

---

## 6. Dataclass and Type Hint Standards

- Use Python 3.10+ union syntax: `str | Path | None`, not `Optional[...]`.
- Use `@dataclass(frozen=True)` for every model, gate-result, and plan type
  (`Method`, `Step`, `Resource`, `Parameter`, `Quantity`, `GateResult`,
  `Plan`, `PlanStep`, `StateRecord`); collection fields are `tuple[X, ...]`,
  never `list[X]`, so instances stay hashable and immutable.
- All public functions have complete annotations and `Raises:` docstring
  clauses where they validate input.

```python
@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    issues: tuple[str, ...] = ()
```

---

## 7. Error Message Format

All `ValueError` subclasses must include the actual problematic value.

**Forbidden**:
```python
raise ValueError("bad argument")
```

**Correct** (following the pattern in `src/methods_dsl/`):
```python
raise MethodModelError(f"Step.step_id must be positive, got {self.step_id}")
raise DimensionError(f"unknown unit {unit!r} — not in the controlled unit vocabulary")
raise CycleError(f"method {method.name!r} has a cyclic dependency among steps {unscheduled}")
```
