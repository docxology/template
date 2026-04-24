# 🔬 Modules Guide

> **Guide** to Layer-1 infrastructure modules

**Quick Reference:** [API Reference](../reference/api-reference.md) | [Architecture](../core/architecture.md) | [Infrastructure Docs](../../infrastructure/AGENTS.md)

**Counting:** The overview table lists **14** named areas (including Skills and Telemetry as first-class). Other docs may say *13 subpackages* when telemetry is treated as part of `core/`—same tree, different grouping. See [`infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md) for the authoritative layout.

---

## Module Overview

| Module | Purpose | Key Features | Guide |
|--------|---------|--------------|-------|
| ⚙️ **Core** | Shared utilities | Logging, config, exceptions | [Details](guides/core-module.md) |
| 📄 **Documentation** | Doc generation | Figure management, API glossary | [Details](guides/documentation-module.md) |
| ✅ **Validation** | Output verification | File integrity, cross-reference validation | [Details](guides/validation-module.md) |
| 📚 **Publishing** | Academic workflows | DOI validation, citation generation | [Details](guides/publishing-module.md) |
| 🔬 **Scientific** | Research best practices | Numerical stability, benchmarking | [Details](guides/scientific-module.md) |
| 🤖 **LLM** | Local LLM & literature | Ollama integration, templates, literature search | [Details](guides/llm-module.md) |
| 🎨 **Rendering** | Multi-format output | PDF, slides, web, poster | [Details](guides/rendering-module.md) |
| 📊 **Reporting** | Pipeline reporting | Reports, error aggregation | [Details](guides/reporting-module.md) |
| 🔍 **Project** | Project discovery | Multi-project orchestration | [Details](guides/project-module.md) |
| 🔒 **Steganography** | Provenance & watermarking | Alpha-channel overlays, QR barcodes, PDF metadata | [Details](guides/steganography-module.md) |
| ⚙️ **Config** | Configuration schemas | Secure config, environment templates | [Details](guides/config-module.md) |
| 🐳 **Docker** | Containerization | Dockerfile, docker-compose | [Details](guides/docker-module.md) |
| 🔍 **Skills** | SKILL.md discovery | Cursor manifest, agent routing (`discover_skills`) | [Details](guides/skills-module.md) |
| 📡 **Telemetry** | Unified pipeline telemetry | Stage resource metrics, diagnostic aggregation, JSON/text reports | — |

All modules follow the thin orchestrator pattern with test coverage.

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

entries = build_api_index("projects/code_project/src/")
table_md = generate_markdown_table(entries)
print(f"API entries: {len(entries)}")
```

CLI: `uv run python -m infrastructure.documentation.generate_glossary_cli projects/code_project/src/ projects/code_project/manuscript/98_symbols_glossary.md` (second path is the markdown file to inject into; created if missing).

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
uv run python scripts/04_validate_output.py --project code_project

# Manual integrity check on final deliverables tree
uv run python -m infrastructure.validation.cli integrity output/code_project/
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

| Module | Dependencies | Test Coverage |
|--------|--------------|---------------|
| Core | pathlib, logging | 83% |
| Documentation | pathlib | 80% |
| Validation | hashlib, pathlib | 81% |
| Publishing | requests, bibtexparser | 86% |
| Scientific | numpy, time, psutil | 88% |
| LLM | requests, ollama | 91% |
| Rendering | pandoc, xelatex | 91% |
| Reporting | json, pathlib | 75% |
| Project | pathlib | 85% |
| Steganography | PIL/Pillow, qrcode, pypdf | 80% |
| Skills | pathlib | 85% |
| Telemetry | psutil, json, pathlib | 84% |

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
