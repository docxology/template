---
name: infrastructure-overview
description: Top-level skill for the research template infrastructure layer. Use when working with any infrastructure module, understanding the two-layer architecture, or importing reusable build/validation/rendering/publishing tools. Covers module discovery, import patterns, and the thin orchestrator pattern.
---

# Infrastructure Layer

The `infrastructure/` package provides generic, reusable functionality for research projects. All business logic resides here (Layer 1) or in project-specific `src/` (Layer 2). Scripts are thin orchestrators that coordinate these modules.

## Module Map

| Module | Purpose | Key Imports |
|--------|---------|-------------|
| `core/` | Logging, config, exceptions, pipeline, progress, retry, security | `get_logger`, `load_config`, `PipelineExecutor` |
| `validation/` | PDF/Markdown/output validation, link checking, audits | `validate_pdf_rendering`, `validate_markdown`, `verify_output_integrity` |
| `rendering/` | Multi-format output (PDF, HTML, slides) | `RenderManager`, `RenderingConfig` |
| `documentation/` | Figure/image management, markdown integration, glossary | `FigureManager`, `ImageManager`, `MarkdownIntegration` |
| `llm/` | Local LLM integration via Ollama | `LLMClient`, `LLMConfig`, `OutputValidator` |
| `publishing/` | Academic publishing (DOI, citations, Zenodo, arXiv) | `publish_to_zenodo`, `generate_citation_bibtex` |
| `reporting/` | Pipeline reports, error aggregation, dashboards | `generate_pipeline_report`, `get_error_aggregator` |
| `scientific/` | Benchmarking, numerical stability, scientific templates | `benchmark_function`, `check_numerical_stability` |
| `project/` | Multi-project discovery and validation | `discover_projects`, `validate_project_structure` |

## Import Patterns

```python
# Convenience imports (most common items)
from infrastructure import get_logger, load_config, validate_markdown

# Direct submodule imports (recommended for clarity)
from infrastructure.core import PipelineExecutor, CheckpointManager
from infrastructure.rendering import RenderManager
from infrastructure.llm.core.client import LLMClient

# In project scripts (thin orchestrator pattern)
from infrastructure.core.logging_utils import get_logger
from infrastructure.validation import validate_pdf_rendering
```

## Architecture Principles

1. **Thin Orchestrator Pattern** — Scripts import from infrastructure; never implement business logic
2. **No Mocks Policy** — All tests use real data and computations
3. **Test Coverage** — Infrastructure requires 60%+ coverage
4. **Exception Hierarchy** — All errors extend `TemplateError` from `infrastructure.core.exceptions`
5. **Unified Logging** — Always use `get_logger(__name__)` for consistent output

## Common Workflows

### Running Infrastructure Tests

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60
```

### Using the Pipeline

```bash
python3 scripts/execute_pipeline.py --project {name} --core-only
```

### Validating Outputs

```bash
python3 -m infrastructure.validation.cli markdown projects/{name}/manuscript/
python3 -m infrastructure.validation.cli pdf output/{name}/pdf/
```

## Submodule Skills

Each submodule has its own SKILL.md with detailed API documentation:

- `infrastructure/core/SKILL.md` — Foundation utilities
- `infrastructure/validation/SKILL.md` — Quality assurance
- `infrastructure/rendering/SKILL.md` — Output generation
- `infrastructure/documentation/SKILL.md` — Figure & doc management
- `infrastructure/llm/SKILL.md` — LLM integration
- `infrastructure/publishing/SKILL.md` — Academic publishing
- `infrastructure/reporting/SKILL.md` — Pipeline reporting
- `infrastructure/scientific/SKILL.md` — Scientific computing
- `infrastructure/project/SKILL.md` — Project management
