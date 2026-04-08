# Advanced Modules Documentation

## Overview

Technical guide for `docs/modules/` — infrastructure module documentation and per-module usage guides.

## Files

| File | Purpose |
|------|---------|
| [`modules-guide.md`](modules-guide.md) | Overview of all 14 named Layer 1 areas (see counting note in that file) |
| [`scientific-simulation-guide.md`](scientific-simulation-guide.md) | Scientific simulation and analysis system |
| [`pdf-validation.md`](pdf-validation.md) | PDF validation system documentation |
| [`guides/core-module.md`](guides/core-module.md) | Core utilities (logging, pipeline, telemetry, etc.) |
| [`guides/documentation-module.md`](guides/documentation-module.md) | Figure management, glossary, markdown integration |
| [`guides/integrity-module.md`](guides/integrity-module.md) | Integrity verification (paths under validation) |
| [`guides/llm-module.md`](guides/llm-module.md) | LLM integration module |
| [`guides/project-module.md`](guides/project-module.md) | Multi-project discovery and orchestration |
| [`guides/publishing-module.md`](guides/publishing-module.md) | Academic publishing module |
| [`guides/rendering-module.md`](guides/rendering-module.md) | Multi-format rendering module |
| [`guides/reporting-module.md`](guides/reporting-module.md) | Pipeline reporting module |
| [`guides/scientific-module.md`](guides/scientific-module.md) | Scientific computing module |
| [`guides/skills-module.md`](guides/skills-module.md) | SKILL.md discovery and manifest |
| [`guides/steganography-module.md`](guides/steganography-module.md) | Steganography / provenance module |
| [`guides/validation-module.md`](guides/validation-module.md) | Validation and quality assurance module |

## Key Conventions

- Each per-module guide in `guides/` covers: purpose, API, usage examples, and testing
- All modules live in `infrastructure/` (Layer 1) and are project-agnostic; project-side examples use [`projects/code_project/`](../../projects/code_project/), active list → [_generated/active_projects.md](../_generated/active_projects.md)
- Module development follows [`../rules/infrastructure_modules.md`](../rules/infrastructure_modules.md) standards
- 60% minimum test coverage for infrastructure modules

## See Also

- [README.md](README.md) — Quick navigation
- [API Reference](../reference/api-reference.md) — Full API docs
- [Architecture](../architecture/two-layer-architecture.md) — Layer 1 vs Layer 2
