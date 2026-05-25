# modules/ - Advanced Modules

> **Advanced infrastructure modules** documentation

**Quick Reference:** [Modules Guide](modules-guide.md) | [Scientific Simulation](scientific-simulation-guide.md) | [PDF Validation](pdf-validation.md) | [Per-Module Guides](guides/)

## Purpose

The `modules/` directory contains documentation for the advanced infrastructure modules that extend the Research Project Template with enterprise-grade capabilities.

## Contents

| File | Purpose | Audience |
|------|---------|----------|
| [`modules-guide.md`](modules-guide.md) | Guide for infrastructure modules | Developers |
| [`scientific-simulation-guide.md`](scientific-simulation-guide.md) | Scientific simulation and analysis system | Researchers |
| [`pdf-validation.md`](pdf-validation.md) | PDF validation system documentation | Developers |

### Per-Module Guides (`guides/`)

| Module | Guide | Focus |
|--------|-------|-------|
| AutoResearch | [`guides/autoresearch-module.md`](guides/autoresearch-module.md) | Deterministic readiness plans, evidence, artifacts |
| Benchmark | [`guides/benchmark-module.md`](guides/benchmark-module.md) | Public exemplar benchmark manifests and rubrics |
| Config | [`guides/config-module.md`](guides/config-module.md) | Configuration schemas, templates |
| Core | [`guides/core-module.md`](guides/core-module.md) | Logging, config, exceptions, pipeline, telemetry |
| Docker | [`guides/docker-module.md`](guides/docker-module.md) | Dockerfile, compose |
| Documentation | [`guides/documentation-module.md`](guides/documentation-module.md) | Figure management, API glossary |
| Integrity | [`guides/integrity-module.md`](guides/integrity-module.md) | File integrity, cross-reference validation |
| LLM | [`guides/llm-module.md`](guides/llm-module.md) | Ollama integration, research templates |
| Methods | [`guides/methods-module.md`](guides/methods-module.md) | Methods orchestration plans |
| Project | [`guides/project-module.md`](guides/project-module.md) | Multi-project discovery, validation |
| Publishing | [`guides/publishing-module.md`](guides/publishing-module.md) | DOI validation, citation generation |
| Rendering | [`guides/rendering-module.md`](guides/rendering-module.md) | PDF, slides, web output |
| Reporting | [`guides/reporting-module.md`](guides/reporting-module.md) | Pipeline reports, error aggregation |
| Scientific | [`guides/scientific-module.md`](guides/scientific-module.md) | Numerical stability, benchmarking |
| Skills | [`guides/skills-module.md`](guides/skills-module.md) | SKILL.md discovery, manifest generation |
| Steganography | [`guides/steganography-module.md`](guides/steganography-module.md) | PDF watermarking, provenance |
| Validation | [`guides/validation-module.md`](guides/validation-module.md) | PDF/Markdown validation, auditing |
| Doctor | [`guides/doctor-module.md`](guides/doctor-module.md) | Repository health diagnostics |
| Orchestration | [`guides/orchestration-module.md`](guides/orchestration-module.md) | Pipeline CLI and menus |
| Prose | [`guides/prose-module.md`](guides/prose-module.md) | Readability metrics, editorial heuristics |
| Search | [`guides/search-module.md`](guides/search-module.md) | Literature discovery and indexing |
| Reference | [`guides/reference-module.md`](guides/reference-module.md) | BibTeX and citation utilities |

## Quick Navigation

### Understanding Advanced Modules

→ Read **[Modules Guide](modules-guide.md)** - Modules guide

### Scientific Computing

→ Study **[Scientific Simulation Guide](scientific-simulation-guide.md)** - Simulation system

### PDF Quality

→ Reference **[PDF Validation](pdf-validation.md)** - Validation system

## Available Modules

Importable package names and counts are tracked in [canonical_facts.md](../_generated/canonical_facts.md). Per-module deep dives live in [guides/](guides/); `config/` and `docker/` are configuration directories rather than Python packages.

## Related Documentation

- **[`../reference/api-reference.md`](../reference/api-reference.md)** - API documentation
- **[`../RUN_GUIDE.md`](../RUN_GUIDE.md)** - Pipeline integration
- **[`../core/architecture.md`](../core/architecture.md)** - System architecture

## See Also

- [`../documentation-index.md`](../documentation-index.md) - documentation index
- [`../README.md`](../README.md) - Documentation hub overview
