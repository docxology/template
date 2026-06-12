# Modules Guide

Reference for Layer-1 infrastructure modules.

**Quick Reference:** [API Reference](../reference/api-reference.md) | [Architecture](../core/architecture.md) | [Infrastructure Docs](../../infrastructure/AGENTS.md)

**Counting:** overview rows below include importable Python packages under `infrastructure/` plus **Telemetry** (a subpackage of `core/`, shown separately for discoverability) and **Config** / **Docker** (configuration directories, not Python packages). Use [COUNTS.md](../_generated/COUNTS.md) for measured counts instead of copying literals. Nested package docs live alongside their parents: `core/telemetry/`, `reference/citation/`, `reference/verification/`, `search/literature/`, and `search/exa/`.

**Exemplar-support tier:** modules tagged _(exemplar-support tier)_ live in `infrastructure/` (Layer-1 location) but are imported only by their own exemplar project — they are intentionally not generic-reach across the infrastructure and are not dead code.

---

## Module Overview

| Module | Purpose | Key Features | Guide |
|--------|---------|--------------|-------|
| **Core** | Shared utilities | Logging, config, exceptions, telemetry | [Details](guides/core-module.md) |
| **AutoResearch** | Deterministic research loops | Plan/evidence/readiness reports, stage contracts | [`infrastructure/autoresearch/AGENTS.md`](../../infrastructure/autoresearch/AGENTS.md) |
| **SIA** _(exemplar-support tier)_ | Self-improvement harness | Task layout, fixture replay, evaluation runner | [Details](guides/sia-module.md) |
| **Benchmark** | Deterministic manifest scoring of public exemplar outputs | Rubric scoring (`rubrics.py`), manifest-based template harness (`template_harness.py`) | [`infrastructure/benchmark/AGENTS.md`](../../infrastructure/benchmark/AGENTS.md) |
| **Documentation** | Doc generation | Figure management, API glossary | [Details](guides/documentation-module.md) |
| **Doctor** | Repository health diagnostics | Environment and repository checks | [Details](guides/doctor-module.md) |
| **Validation** | Output verification | File integrity, cross-reference validation | [Details](guides/validation-module.md) |
| **Publishing** | Academic workflows | DOI validation, citation generation | [Details](guides/publishing-module.md) |
| **Scientific** _(exemplar-support tier)_ | Research best practices | Numerical stability, benchmarking | [Details](guides/scientific-module.md) |
| **LLM** | Local LLM & literature | Ollama integration, templates, literature search | [Details](guides/llm-module.md) |
| **Methods** | Methods orchestration | DAG contracts, methods prose, artifacts, evidence | [Details](guides/methods-module.md) |
| **Rendering** | Multi-format output | PDF, HTML, slides, poster, DOCX, EPUB (opt-in) | [Details](guides/rendering-module.md) |
| **Reporting** | Pipeline reporting | Reports, error aggregation | [Details](guides/reporting-module.md) |
| **Search** | Literature backends | Discovery, caches, full-text helpers, Exa web API | [`infrastructure/search/AGENTS.md`](../../infrastructure/search/AGENTS.md) |
| **Reference** | Bibliographic utilities | BibTeX models, parser/writer, verification | [`infrastructure/reference/AGENTS.md`](../../infrastructure/reference/AGENTS.md) |
| **Project** | Project discovery | Multi-project orchestration | [Details](guides/project-module.md) |
| **Steganography** | Provenance & watermarking | Alpha-channel overlays, QR barcodes, PDF metadata | [Details](guides/steganography-module.md) |
| **Config** | Configuration schemas | Secure config, environment templates | [Details](guides/config-module.md) |
| **Docker** | Containerization | Dockerfile, docker-compose | [Details](guides/docker-module.md) |
| **Skills** | SKILL.md discovery | Cursor manifest, agent routing (`discover_skills`) | [Details](guides/skills-module.md) |
| **Telemetry** | Unified pipeline telemetry | Stage resource metrics, diagnostic aggregation, JSON/text reports | — |
| **Prose** | Manuscript prose analytics | Readability metrics, outline, editorial flags, JSON reports | [`infrastructure/prose/AGENTS.md`](../../infrastructure/prose/AGENTS.md) |
| **Orchestration** | Pipeline CLI / menus | Thin shell over `PipelineExecutor`, slug validation, stage logs | [`infrastructure/orchestration/AGENTS.md`](../../infrastructure/orchestration/AGENTS.md) |

---

## Quick Start

### Integrity Checking

```python
from pathlib import Path

from infrastructure.validation.integrity import verify_output_integrity

report = verify_output_integrity(Path("output"))
if report.overall_integrity:
    print("All checks passed")
```

### Documentation Generation

```python
from infrastructure.documentation.glossary_gen import build_api_index, generate_markdown_table

entries = build_api_index("projects/templates/template_code_project/src/")
table_md = generate_markdown_table(entries)
print(f"API entries: {len(entries)}")
```

CLI: `uv run python -m infrastructure.documentation.generate_glossary_cli projects/templates/template_code_project/src/ projects/templates/template_code_project/manuscript/98_symbols_glossary.md` (second path is the markdown file to inject into; created if missing).

### LLM Assistance

```python
from infrastructure.llm import LLMClient

client = LLMClient()
response = client.query("Summarize the key findings")
```

### PDF Rendering

```python
from infrastructure.rendering import RenderManager

manager = RenderManager()
pdf_path = manager.render_pdf(Path("manuscript/main.tex"))
```

---

## Integration with Build Pipeline

```bash
# Validate outputs for a project (after render / copy)
uv run python scripts/04_validate_output.py --project template_code_project

# Manual integrity check on final deliverables tree
uv run python -m infrastructure.validation.cli integrity output/template_code_project/
```

---

## Integration Patterns

### Using Multiple Modules Together

```python
from pathlib import Path

from infrastructure.publishing import extract_publication_metadata
from infrastructure.validation.integrity import verify_output_integrity


def comprehensive_validation(output_dir: Path, manuscript_files: list[Path]) -> dict:
    """Run validation suite."""
    return {
        "integrity": verify_output_integrity(output_dir),
        "publishing": extract_publication_metadata(manuscript_files),
    }
```

---

## Module Dependencies

| Module | Dependencies | Measured coverage |
|--------|--------------|-------------------|
| Core | pathlib, logging | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Documentation | pathlib | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Validation | hashlib, pathlib | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Publishing | requests, bibtexparser | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Scientific | numpy, time, psutil | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| LLM | requests, ollama | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Rendering | pandoc, xelatex | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Reporting | json, pathlib | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Project | pathlib | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Steganography | PIL/Pillow, qrcode, pypdf | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Skills | pathlib | See [`coverage-gaps.md`](../development/coverage-gaps.md) |
| Telemetry | psutil, json, pathlib | See [`coverage-gaps.md`](../development/coverage-gaps.md) |

All modules work independently or together with minimal coupling.

---

## Best Practices

1. **Integrate Early** - Include modules in your workflow from the beginning
2. **Automate Validation** - Set up automated checks in your build pipeline
3. **Monitor Performance** - Track algorithm performance over time

---

## See Also

- **[API Reference](../reference/api-reference.md)** - Full API documentation
- **[Infrastructure Guide](../../infrastructure/AGENTS.md)** - Module architecture
- **[Pipeline Orchestration](../RUN_GUIDE.md)** - Build pipeline integration

---

**The modules provide enterprise-grade capabilities while maintaining simplicity. Each can be used independently or integrated into validation workflows.**
