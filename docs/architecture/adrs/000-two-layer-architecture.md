# ADR 000: Two-Layer Architecture

## Status

Accepted

## Context

The repository needs a clear separation between reusable infrastructure code and project-specific research logic. Without this boundary, projects become tightly coupled to infrastructure internals, making them hard to test, reuse, or replace independently.

## Decision

Adopt a **two-layer architecture**:

| Layer | Location | Purpose |
|-------|----------|---------|
| **Layer 1: Infrastructure** | `infrastructure/` | Generic, reusable tools — pipeline, validation, rendering, publishing, LLM integration |
| **Layer 2: Projects** | `projects/{name}/` | Self-contained workspaces with `src/` (business logic), `tests/`, `scripts/` (thin orchestrators), `manuscript/`, and `docs/` |

### Key Principles

- **`infrastructure/`** is reusable across projects — never imports from `projects/`
- **`projects/{name}/src/`** contains project-specific algorithms — never imports from other projects
- **`projects/{name}/scripts/`** are thin orchestrators that import from `infrastructure/` or `src/`
- **Scripts contain no business logic** — they orchestrate calls to reusable modules

### Reusability

- Infrastructure modules serve any project
- Projects can validate independently; no cross-project dependencies
- Clear code placement; easy to locate implementations
- Projects can be swapped without affecting infrastructure
- Agent routing via SKILL.md manifests maps skills to actual modules

## Consequences

### Positive

- Single source of truth for each algorithm
- Scripts become simple — their only job is to orchestrate
- Faster onboarding: new contributors know where to look
- Testability: algorithms in `src/` can be unit tested directly

### Negative

- Initial overhead: requires discipline to keep scripts thin
- Import path management: need correct PYTHONPATH during development vs installed mode

## Alternatives Considered

| Option | Reason for Rejection |
|--------|---------------------|
| Monolithic repo with all projects in one `src/` | No isolation; tight coupling between projects |
| Scripts containing business logic | Duplicated logic, hard to test, violates separation of concerns |

## References

- [`docs/architecture/thin-orchestrator-summary.md`](../thin-orchestrator-summary.md) — Pattern implementation details
- [`docs/architecture/decision-tree.md`](../decision-tree.md) — Code placement decision tree
- [`infrastructure/core/pipeline/dag.py`](../../../infrastructure/core/pipeline/dag.py) — DAG engine
