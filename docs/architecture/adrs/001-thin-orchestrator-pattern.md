# ADR 001: Thin Orchestrator Pattern

## Status

Accepted

## Context

Scripts in `scripts/` (root level) and `projects/{name}/scripts/` need a clear contract about their role. Without enforcement, scripts tend to accumulate business logic, making code harder to test, reuse, and maintain.

## Decision

Scripts must be **thin wrappers** that import logic from `infrastructure/` modules or `projects/{name}/src/`. Scripts contain no business logic themselves.

### Enforcement

- Code reviews check for business logic in scripts
- `scripts/verify_no_mocks.py` ensures no mock usage; similar checks could be added for orchestrator purity
- The "thin orchestrator" pattern is enforced by convention and the project's AGENTS.md documentation

## Consequences

### Positive

- **Testability:** Algorithms in `src/` can be unit tested directly without running the full pipeline
- **Reusability:** Infrastructure functions are callable from multiple scripts
- **Clarity:** Easy to locate implementation — always in `src/` or `infrastructure/`
- **Agent routing:** Cursor/Claude can map skills to actual modules via SKILL.md
- **Scripts become simple** — their only job is to orchestrate
- **Faster onboarding:** new contributors know where to look

### Negative

- More files (separate `src/` and `scripts/`)
- Requires import discipline (circular imports possible if misused)
- Slightly more verbose for trivial tasks

## Examples

Good — thin script:

```python
# scripts/02_run_analysis.py
from projects.template_code_project.src.optimizer import gradient_descent
from infrastructure.scientific.benchmarking import benchmark_function

result = gradient_descent(...)
report = benchmark_function(result, test_inputs=[result])
report.save(Path("output/report.json"))
```

Bad — logic in script (anti-pattern):

```python
# ANTI-PATTERN
def gradient_descent(initial_point, objective_func, ...):
    # Implementation here — WRONG
    ...

result = gradient_descent(...)  # This belongs in src/
```

## References

- [`docs/architecture/two-layer-architecture.md`](../two-layer-architecture.md) — Full two-layer architecture
- [`infrastructure/orchestration/pipeline_runner.py`](../../../infrastructure/orchestration/pipeline_runner.py) — Pipeline executor
- [`core/workflow.md`](../../core/workflow.md) — Development workflow
