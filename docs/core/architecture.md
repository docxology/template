# 🏗️ System Architecture Overview

> Concise overview of the template's design — see linked documents for details

**Quick Reference:** [How To Use](how-to-use.md) | [Two-Layer Architecture](../architecture/two-layer-architecture.md) | [Workflow](workflow.md) | [Thin Orchestrator](../architecture/thin-orchestrator-summary.md)

## Architecture Summary

The Research Project Template uses a **Two-Layer Architecture** with a **Thin Orchestrator** pattern:

- **Layer 1 — Infrastructure** (`infrastructure/`): Generic, reusable build, validation, rendering, and reporting tools
- **Layer 2 — Projects** (`projects/{name}/`): Project-specific code, manuscripts, and outputs
- **Scripts** (`scripts/`, `projects/{name}/scripts/`): Thin orchestrators that import and use `src/` methods — never implement algorithms

For the complete architecture guide, see **[Two-Layer Architecture](../architecture/two-layer-architecture.md)**.

## Core Components

```mermaid
graph TB
    subgraph "Template Repository"
        INFRA[Infrastructure<br/>infrastructure/] --> |"provides tools"| PROJECT
        PROJECT[Project Code<br/>projects/*/src/] --> |"imported by"| SCRIPTS[Scripts<br/>projects/*/scripts/]
        SCRIPTS --> |"generate"| OUTPUTS[Outputs<br/>output/]
        TESTS[Tests<br/>tests/ & projects/*/tests/] --> |"validate"| PROJECT
        MANUSCRIPT[Manuscript<br/>projects/*/manuscript/] --> |"references"| OUTPUTS
    end

    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#e65100,stroke-width:2px
    class INFRA,PROJECT,SCRIPTS,TESTS,MANUSCRIPT core
    class OUTPUTS output
```

## Build Pipeline (8 Stages)

| Stage | Name | Purpose |
|-------|------|---------|
| 00 | Setup | Environment validation |
| 01 | Tests | Run test suite (90% project, 60% infra coverage) |
| 02 | Analysis | Execute generation scripts |
| 03 | Render | PDF generation via pandoc/LaTeX |
| 04 | Validate | Output integrity checks |
| 05 | Copy | Consolidate deliverables |
| 06 | LLM Review | Optional manuscript review |
| 07 | Report | Executive summary generation |

Run with: `uv run python scripts/execute_pipeline.py --core-only`

## Key Principles

1. **Single Source of Truth** — `src/` is the authoritative implementation
2. **Thin Orchestrators** — Scripts import `src/` methods, never duplicate logic
3. **Test-Driven** — Tests validate before implementation
4. **Reproducible** — Deterministic RNG, fixed seeds, headless plotting
5. **Automated Validation** — All components checked for coherence

## Detailed Documentation

| Topic | Document |
|-------|----------|
| Full architecture guide | [two-layer-architecture.md](../architecture/two-layer-architecture.md) |
| Thin orchestrator pattern | [thin-orchestrator-summary.md](../architecture/thin-orchestrator-summary.md) |
| Code placement decisions | [decision-tree.md](../architecture/decision-tree.md) |
| Development workflow | [workflow.md](workflow.md) |
| Build system details | [build-system.md](../operational/build/build-system.md) |
| API reference | [api-reference.md](../reference/api-reference.md) |

## Development Rules

- **[`.cursorrules/AGENTS.md`](../../.cursorrules/AGENTS.md)** — Development standards
- **[`.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md)** — Infrastructure module development
- **[`.cursorrules/README.md`](../../.cursorrules/README.md)** — Quick reference and patterns
