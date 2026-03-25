# Advanced Modules Documentation

## Overview

Technical guide for `docs/modules/` — infrastructure module documentation and per-module usage guides.

## Files

| File | Purpose |
|------|---------|
| `modules-guide.md` | Overview of all 12 infrastructure modules |
| `scientific-simulation-guide.md` | Scientific simulation and analysis system |
| `pdf-validation.md` | PDF validation system documentation |
| `guides/integrity-module.md` | Integrity verification module |
| `guides/llm-module.md` | LLM integration module |
| `guides/publishing-module.md` | Academic publishing module |
| `guides/rendering-module.md` | Multi-format rendering module |
| `guides/reporting-module.md` | Pipeline reporting module |
| `guides/scientific-module.md` | Scientific computing module |

## Key Conventions

- Each per-module guide in `guides/` covers: purpose, API, usage examples, and testing
- All modules live in `infrastructure/` (Layer 1) and are project-agnostic; project-side examples use [`projects/code_project/`](../../projects/code_project/), active list → [_generated/active_projects.md](../_generated/active_projects.md)
- Module development follows `../rules/infrastructure_modules.md` standards
- 60% minimum test coverage for infrastructure modules

## See Also

- [README.md](README.md) — Quick navigation
- [API Reference](../reference/api-reference.md) — Full API docs
- [Architecture](../architecture/two-layer-architecture.md) — Layer 1 vs Layer 2
