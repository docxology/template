# Architecture Documentation

## Overview

Technical guide for `docs/architecture/` — system architecture, design patterns, and code placement decisions.

## Files

| File | Purpose |
|------|---------|
| `two-layer-architecture.md` | Comprehensive Layer 1 (Infrastructure) vs Layer 2 (Project) guide |
| `thin-orchestrator-summary.md` | Thin orchestrator pattern implementation |
| `decision-tree.md` | Decision tree for code placement |
| `migration-from-flat.md` | Migration guide from flat project structure |
| `testing-strategy.md` | Testing strategy and coverage architecture |

## Key Conventions

- **Project examples in prose**: default to [`projects/code_project/`](../../projects/code_project/); active `projects/` names → [_generated/active_projects.md](../_generated/active_projects.md).
- **Layer 1** (`infrastructure/`): Generic, reusable tools — 60% test coverage minimum
- **Layer 2** (`projects/{name}/`): Project-specific code — 90% test coverage minimum
- **Thin orchestrator**: Scripts import `infrastructure/` and `projects/{name}/src/` modules; they do not implement core algorithms
- Use `decision-tree.md` to determine where new code belongs

## See Also

- [README.md](README.md) — Quick navigation
- [Core Architecture](../core/architecture.md) — Concise overview
- [Best Practices](../best-practices/best-practices.md) — Code organization patterns
