---
name: infrastructure-overview
description: Top-level skill for the research template infrastructure layer. Use in Cursor, Claude Code, or similar agents when editing or importing anything under infrastructure/, understanding the two-layer architecture, or wiring build/validation/rendering/publishing. Covers module discovery, import patterns, thin orchestrators, per-subpackage SKILL.md paths, and .cursor/skill_manifest.json (see infrastructure.skills).
---

# Infrastructure Layer

The `infrastructure/` package provides generic, reusable functionality for research projects. All business logic resides here (Layer 1) or in project-specific `src/` (Layer 2). Scripts are thin orchestrators that coordinate these modules.

## Finding skills (Cursor and other agents)

- **Hub:** This file lists every subpackage skill and a module map.
- **Manifest:** `.cursor/skill_manifest.json` lists every discovered first-party skill (`name`, `description`, `path`); regenerate with `uv run python -m infrastructure.skills write`.
- **Search:** default discovery covers `infrastructure/**/SKILL.md`, `scripts/**/SKILL.md`, public `projects/templates/**/SKILL.md` including `.agents/skills`, public resource-pool template skills under `fonds/templates/`, `rules/templates/`, and `tools/templates/`, plus `.cursor/skills/`.
- **In Cursor:** `@infrastructure/SKILL.md` or `@infrastructure/<module>/SKILL.md` to load context; pair with the matching `AGENTS.md` for API tables.
- **Frontmatter:** Each `SKILL.md` has YAML `name` and `description` for routing (see also the table in `infrastructure/README.md`).

## Module Map

| Module | Purpose | Key Imports |
|--------|---------|-------------|
| `autoresearch/` | Deterministic research plans, stage-gate readiness, artifact/evidence reports | `build_autoresearch_plan`, `validate_autoresearch_plan` |
| `benchmark/` | Deterministic benchmark manifests and public exemplar readiness scoring | `run_benchmark_manifest`, `score_project_against_manifest` |
| `config/` | Repo defaults (`.env.template`, `secure_config.yaml`) | (YAML/dotenv; use `core.config_loader`) |
| `core/` | Logging, config, exceptions, pipeline, progress, retry, security | `get_logger`, `load_config`, `PipelineExecutor` |
| `docker/` | `Dockerfile`, `docker-compose.yml` for container runs | (CLI / `docs/CLOUD_DEPLOY.md`) |
| `validation/` | PDF/Markdown/output validation, link checking, audits | `validate_pdf_rendering`, `validate_markdown`, `verify_output_integrity` |
| `rendering/` | Multi-format output (PDF, HTML, slides) | `RenderManager`, `RenderingConfig` |
| `documentation/` | Figure/image management, markdown integration, glossary | `FigureManager`, `ImageManager`, `MarkdownIntegration` |
| `llm/` | Local LLM integration via Ollama | `LLMClient`, `OllamaClientConfig`, `detect_repetition`, `check_format_compliance` |
| `methods/` | Methods orchestration plans over DAG, manuscript methods, artifacts, and evidence | `build_methods_orchestration_plan`, `validate_methods_orchestration_plan` |
| `orchestration/` | Pipeline CLI, menu, project discovery, stage logging, secure-run wrapper (backs `run.sh`/`secure_run.sh`) | `build_parser`, `PipelineRunner`, `validate_project_slug`, `run_secure_pipeline` |
| `publishing/` | Academic publishing (DOI, citations, Zenodo, arXiv) | `publish_to_zenodo`, `generate_citation_bibtex` |
| `reference/` | BibTeX I/O (read / write / convert) matching `references.bib` syntax | `parse_bibfile`, `render_database`, `paper_to_bibentry` |
| `search/` | Paperclip-style multi-source literature search (arXiv, Crossref, local, Paperclip) | `LiteratureClient`, `SearchQuery`, `ArxivBackend`, `CrossrefBackend` |
| `prose/` | Prose analysis (readability, structure, editorial quality, manuscript reports) | `analyze_manuscript`, `compute_metrics`, `analyze_structure`, `analyze_quality` |
| `reporting/` | Pipeline reports, error aggregation, dashboards | `generate_pipeline_report`, `get_error_aggregator` |
| `scientific/` | Benchmarking, numerical stability, scientific templates | `benchmark_function`, `check_numerical_stability` |
| `sia/` | SIA harness: task layout, fixture replay loop, evaluation runner | `validate_task_dir`, `run_sia_loop`, `run_evaluation` |
| `project/` | Multi-project discovery and validation | `discover_projects`, `validate_project_structure` |
| `skills/` | Enumerate and parse `SKILL.md`; maintain Cursor manifest | `discover_skills`, `write_skill_manifest` |
| `steganography/` | Cryptographic PDF watermarking and verification | `SteganographyProcessor`, `SteganographyConfig`, `embed_steganography` |
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
from infrastructure.methods import build_methods_orchestration_plan
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
uv run python scripts/runner/execute_pipeline.py --project template_code_project --core-only
```

### Validating Outputs

```bash
uv run python -m infrastructure.validation.cli.main markdown projects/templates/template_code_project/manuscript/
uv run python -m infrastructure.validation.cli.main pdf output/templates/template_code_project/pdf/
```

## Submodule Skills

Each subpackage has a `SKILL.md` (YAML frontmatter + body) for agent discovery—search the repo for `infrastructure/**/SKILL.md` or open paths below:

- `infrastructure/config/SKILL.md` — Repo configuration templates and secure defaults
- `infrastructure/autoresearch/SKILL.md` — Deterministic AutoResearch readiness planning
- `infrastructure/benchmark/SKILL.md` — Deterministic public exemplar benchmark harnesses
- `infrastructure/core/SKILL.md` — Foundation utilities
- `infrastructure/docker/SKILL.md` — Container build and compose
- `infrastructure/doctor/SKILL.md` — Repository diagnostics and audited repairs
- `infrastructure/documentation/SKILL.md` — Figure and doc management
- `infrastructure/llm/SKILL.md` — LLM integration
- `infrastructure/methods/SKILL.md` — Methods orchestration plans
- `infrastructure/orchestration/SKILL.md` — Pipeline CLI, menu, and runner orchestration
- `infrastructure/prose/SKILL.md` — Manuscript prose quality analysis
- `infrastructure/project/SKILL.md` — Project discovery and validation
- `infrastructure/publishing/SKILL.md` — Academic publishing
- `infrastructure/reference/SKILL.md` — Bibliographic reference workflows
- `infrastructure/reference/citation/SKILL.md` — BibTeX read/write/convert subpackage
- `infrastructure/rendering/SKILL.md` — Output generation
- `infrastructure/reporting/SKILL.md` — Pipeline reporting
- `infrastructure/scientific/SKILL.md` — Scientific computing
- `infrastructure/search/SKILL.md` — Literature discovery and search workflows
- `infrastructure/search/literature/SKILL.md` — Academic literature-search subpackage
- `infrastructure/sia/SKILL.md` — Self-Improvement Agent harness contracts
- `infrastructure/skills/SKILL.md` — Programmatic skill discovery and manifest I/O
- `infrastructure/steganography/SKILL.md` — Secure PDF post-processing
- `infrastructure/core/telemetry/SKILL.md` — Unified pipeline telemetry (nested under `core/`)
- `infrastructure/reference/verification/SKILL.md` — Reference-existence verification gate
- `infrastructure/validation/SKILL.md` — Quality assurance
