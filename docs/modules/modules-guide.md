# 🔬 Modules Guide

> **Guide** to the 12 infrastructure modules

**Quick Reference:** [API Reference](../reference/api-reference.md) | [Architecture](../core/architecture.md) | [Infrastructure Docs](../../infrastructure/AGENTS.md)

---

## Module Overview

| Module | Purpose | Key Features | Guide |
|--------|---------|--------------|-------|
| ⚙️ **Core** | Shared utilities | Logging, config, exceptions | — |
| 📄 **Documentation** | Doc generation | Figure management, API glossary | — |
| ✅ **Validation** | Output verification | File integrity, cross-reference validation | [Details](guides/integrity-module.md) |
| 📚 **Publishing** | Academic workflows | DOI validation, citation generation | [Details](guides/publishing-module.md) |
| 🔬 **Scientific** | Research best practices | Numerical stability, benchmarking | [Details](guides/scientific-module.md) |
| 🤖 **LLM** | Local LLM & literature | Ollama integration, templates, literature search | [Details](guides/llm-module.md) |
| 🎨 **Rendering** | Multi-format output | PDF, slides, web, poster | [Details](guides/rendering-module.md) |
| 📊 **Reporting** | Pipeline reporting | Reports, error aggregation | [Details](guides/reporting-module.md) |
| 🔍 **Project** | Project discovery | Multi-project orchestration | — |
| 🔒 **Steganography** | Provenance & watermarking | Alpha-channel overlays, QR barcodes, PDF metadata | — |
| ⚙️ **Config** | Configuration schemas | Secure config, environment templates | — |
| 🐳 **Docker** | Containerization | Dockerfile, docker-compose | — |

All modules follow the thin orchestrator pattern with test coverage.

---

## Quick Start

### Integrity Checking

```python
from infrastructure.validation.integrity import verify_output_integrity

report = verify_output_integrity("output/")
if report.overall_integrity:
    print("✅ All checks passed")
```

### Documentation Generation

```python
from infrastructure.documentation.glossary_gen import generate_glossary

glossary = generate_glossary("projects/code_project/src/")
print(f"Generated {len(glossary)} entries")
```

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
# Automatic build verification
uv run python scripts/04_validate_output.py

# Manual verification
uv run python -m infrastructure.validation.cli integrity output/
```

---

## Integration Patterns

### Using Multiple Modules Together

```python
from infrastructure.validation.integrity import verify_output_integrity
from infrastructure.publishing.core import extract_publication_metadata

def comprehensive_validation(output_dir, manuscript_files):
    """Run validation suite."""
    results = {}
    results['integrity'] = verify_output_integrity(output_dir)
    results['publishing'] = extract_publication_metadata(manuscript_files)
    return results
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
