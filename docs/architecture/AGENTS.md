# Architecture Documentation

## Overview

Technical guide for `docs/architecture/` — system architecture, design patterns, and code placement decisions.

## Files

| File | Purpose |
|------|---------|
| `two-layer-architecture.md` | Comprehensive Layer 1 (Infrastructure) vs Layer 2 (Project) guide |
| `thin-orchestrator-summary.md` | Thin orchestrator pattern implementation |
| `decision-tree.md` | Decision tree for code placement |

## Key Conventions

- **Layer 1** (`infrastructure/`): Generic, reusable tools — 60% test coverage minimum
- **Layer 2** (`projects/{name}/`): Project-specific code — 90% test coverage minimum
- **Thin orchestrator**: Scripts import and use `src/` methods, never implement algorithms
- Use `decision-tree.md` to determine where new code belongs

## See Also

- [README.md](README.md) — Quick navigation
- [Core Architecture](../core/architecture.md) — Concise overview
- [Best Practices](../best-practices/best-practices.md) — Code organization patterns
