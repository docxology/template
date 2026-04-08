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

## Core pipeline (orchestrated DAG)

- **`./run.sh` progress UI:** **Clean** is shown as **[0/9]**; the following **nine** steps are **[1/9]–[9/9]** (through copy outputs). Optional LLM stages run when enabled in full pipeline mode.
- **`scripts/execute_pipeline.py --core-only`:** Runs **clean** plus the script chain (setup, tests, analysis, render, validate, copy—see stage keys in that file) without LLM steps. Full pipeline adds optional LLM and executive-report stages.

Authoritative stage names, flags (`--skip-infra`, `--resume`), and menu mapping: **[RUN_GUIDE.md](../RUN_GUIDE.md)**.

Run core path: `uv run python scripts/execute_pipeline.py --project {name} --core-only`

## Key Principles

1. **Single Source of Truth** — `infrastructure/` and `projects/{name}/src/` hold business logic
2. **Thin Orchestrators** — Root and project `scripts/` import those modules; they do not reimplement algorithms
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
| Pipeline orchestration | [RUN_GUIDE.md](../RUN_GUIDE.md) |
| API reference | [api-reference.md](../reference/api-reference.md) |

## Development Rules

- **[`docs/rules/AGENTS.md`](../rules/AGENTS.md)** — Development standards
- **[`docs/rules/infrastructure_modules.md`](../rules/infrastructure_modules.md)** — Infrastructure module development
- **[`docs/rules/README.md`](../rules/README.md)** — Quick reference and patterns

---

## Troubleshooting

### Layer Violation

**Symptom**: `ModuleNotFoundError` when infrastructure imports project code

**Solution**: Refactor - infrastructure must not depend on project code. Move shared logic to infrastructure.

### Import Errors

**Symptom**: Scripts fail with import errors

**Solution**:
- Use `uv run python` for proper environment
- Ensure conftest.py adds src/ to path
- Check thin orchestrator pattern: scripts import from src/, not implement

---

**Quick Reference**: [Troubleshooting Guide](../operational/troubleshooting/README.md)
