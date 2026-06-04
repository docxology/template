# Advanced Modules Documentation

## Overview

Technical guide for `docs/modules/` — infrastructure module documentation and per-module usage guides.

## Files

| File | Purpose |
|------|---------|
| `modules-guide.md` | Overview table for infrastructure packages plus Telemetry, Config, and Docker; links into `guides/` plus hub AGENTS for package-specific docs |
| `scientific-simulation-guide.md` | Scientific simulation and analysis system |
| `pdf-validation.md` | PDF validation system documentation |
| `literature-search-and-references.md` | Literature search and reference management module |
| `guides/autoresearch-module.md` | Deterministic readiness planning module |
| `guides/benchmark-module.md` | Public exemplar benchmark manifests module |
| `guides/config-module.md` | Config schemas / templates module |
| `guides/core-module.md` | Core utilities module |
| `guides/docker-module.md` | Docker / compose module |
| `guides/documentation-module.md` | Documentation / figure / glossary module |
| `guides/integrity-module.md` | Integrity verification module |
| `guides/llm-module.md` | LLM integration module |
| `guides/methods-module.md` | Methods orchestration module |
| `guides/project-module.md` | Project discovery module plus local CodeGraph helpers |
| `guides/publishing-module.md` | Academic publishing module |
| `guides/rendering-module.md` | Multi-format rendering module |
| `guides/reporting-module.md` | Pipeline reporting module |
| `guides/scientific-module.md` | Scientific computing module |
| `guides/skills-module.md` | SKILL.md discovery / manifest |
| `guides/steganography-module.md` | Steganography / provenance module |
| `guides/validation-module.md` | Validation / QA module (PDF, markdown, CLI) |
| `guides/doctor-module.md` | Repository health diagnostics module |
| `guides/orchestration-module.md` | Pipeline CLI and menu delegation |
| `guides/prose-module.md` | Prose-manuscript analysis module |
| `guides/search-module.md` | Literature discovery module |
| `guides/sia-module.md` | SIA self-improvement harness module |
| `guides/reference-module.md` | Citation and reference management module |

Package-level `infrastructure/*/AGENTS.md` files remain the in-tree API reference when a guide defers to hub docs.

## Key Conventions

- Each per-module guide in `guides/` covers: purpose, API, usage examples, and testing
- All modules live in `infrastructure/` (Layer 1) and are project-agnostic; project-side examples use [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/), active list → [_generated/active_projects.md](../_generated/active_projects.md)
- Module development follows `../rules/infrastructure_modules.md` standards
- 60% minimum test coverage for infrastructure modules

## See Also

- [README.md](README.md) — Quick navigation
- [API Reference](../reference/api-reference.md) — Full API docs
- [Architecture](../architecture/two-layer-architecture.md) — Layer 1 vs Layer 2
