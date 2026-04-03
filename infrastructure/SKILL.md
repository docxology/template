---
name: infrastructure-overview
description: Top-level skill for the research template infrastructure layer. Use in Cursor, Claude Code, or similar agents when editing or importing anything under infrastructure/, understanding the two-layer architecture, or wiring build/validation/rendering/publishing. Covers module discovery, import patterns, thin orchestrators, per-subpackage SKILL.md paths, and .cursor/skill_manifest.json (see infrastructure.skills).
---

# Infrastructure Layer

The `infrastructure/` package provides generic, reusable functionality for research projects. All business logic resides here (Layer 1) or in project-specific `src/` (Layer 2). Scripts are thin orchestrators that coordinate these modules.

## Finding skills (Cursor and other agents)

- **Hub:** This file lists every subpackage skill and a module map.
- **Manifest:** `.cursor/skill_manifest.json` lists every skill (`name`, `description`, `path`); regenerate with `uv run python -m infrastructure.skills write`.
- **Search:** `infrastructure/**/SKILL.md` (15 files: hub `infrastructure/SKILL.md` + 13 top-level subpackage skills + `infrastructure/core/telemetry/SKILL.md`).
- **In Cursor:** `@infrastructure/SKILL.md` or `@infrastructure/<module>/SKILL.md` to load context; pair with the matching `AGENTS.md` for API tables.
- **Frontmatter:** Each `SKILL.md` has YAML `name` and `description` for routing (see also the table in `infrastructure/README.md`).

## Module Map

| Module | Purpose | Key Imports |
|--------|---------|-------------|
| `config/` | Repo defaults (`.env.template`, `secure_config.yaml`) | (YAML/dotenv; use `core.config_loader`) |
| `core/` | Logging, config, exceptions, pipeline, progress, retry, security | `get_logger`, `load_config`, `PipelineExecutor` |
| `docker/` | `Dockerfile`, `docker-compose.yml` for container runs | (CLI / `docs/CLOUD_DEPLOY.md`) |
| `validation/` | PDF/Markdown/output validation, link checking, audits | `validate_pdf_rendering`, `validate_markdown`, `verify_output_integrity` |
| `rendering/` | Multi-format output (PDF, HTML, slides) | `RenderManager`, `RenderingConfig` |
| `documentation/` | Figure/image management, markdown integration, glossary | `FigureManager`, `ImageManager`, `MarkdownIntegration` |
| `llm/` | Local LLM integration via Ollama | `LLMClient`, `OllamaClientConfig`, `OutputValidator` |
| `publishing/` | Academic publishing (DOI, citations, Zenodo, arXiv) | `publish_to_zenodo`, `generate_citation_bibtex` |
| `reporting/` | Pipeline reports, error aggregation, dashboards | `generate_pipeline_report`, `get_error_aggregator` |
| `scientific/` | Benchmarking, numerical stability, scientific templates | `benchmark_function`, `check_numerical_stability` |
| `project/` | Multi-project discovery and validation | `discover_projects`, `validate_project_structure` |
| `skills/` | Enumerate and parse `SKILL.md`; maintain Cursor manifest | `discover_skills`, `write_skill_manifest` |
| `steganography/` | Cryptographic PDF watermarking and verification | `SteganographyProcessor`, `StegoParams` |
| `core/telemetry/` | Unified pipeline telemetry (stage resources + diagnostics, JSON/text reports) | `TelemetryCollector`, `TelemetryConfig` |

## Import Patterns

```python
# Convenience imports (exported on infrastructure package root)
from infrastructure import get_logger, load_config, TemplateError

# Direct submodule imports (recommended for clarity)
from infrastructure.core import CheckpointManager
from infrastructure.core.pipeline import PipelineExecutor
from infrastructure.rendering import RenderManager
from infrastructure.llm.core.client import LLMClient
from infrastructure.validation import validate_markdown, validate_pdf_rendering
from infrastructure.skills import discover_skills

# In project scripts (thin orchestrator pattern)
from infrastructure.core.logging.utils import get_logger
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
python3 scripts/execute_pipeline.py --project code_project --core-only
```

### Validating Outputs

```bash
python3 -m infrastructure.validation.cli.main markdown projects/code_project/manuscript/
python3 -m infrastructure.validation.cli.main pdf output/code_project/pdf/
```

## Submodule Skills

Each subpackage has a `SKILL.md` (YAML frontmatter + body) for agent discovery—search the repo for `infrastructure/**/SKILL.md` or open paths below:

- `infrastructure/config/SKILL.md` — Repo configuration templates and secure defaults
- `infrastructure/core/SKILL.md` — Foundation utilities
- `infrastructure/docker/SKILL.md` — Container build and compose
- `infrastructure/documentation/SKILL.md` — Figure and doc management
- `infrastructure/llm/SKILL.md` — LLM integration
- `infrastructure/project/SKILL.md` — Project discovery and validation
- `infrastructure/publishing/SKILL.md` — Academic publishing
- `infrastructure/rendering/SKILL.md` — Output generation
- `infrastructure/reporting/SKILL.md` — Pipeline reporting
- `infrastructure/scientific/SKILL.md` — Scientific computing
- `infrastructure/skills/SKILL.md` — Programmatic skill discovery and manifest I/O
- `infrastructure/steganography/SKILL.md` — Secure PDF post-processing
- `infrastructure/core/telemetry/SKILL.md` — Unified pipeline telemetry (nested under `core/`)
- `infrastructure/validation/SKILL.md` — Quality assurance
