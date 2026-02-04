# 🔬 Modules Guide

> **Guide** to the 7 infrastructure modules

**Quick Reference:** [API Reference](../reference/API_REFERENCE.md) | [Architecture](../core/ARCHITECTURE.md) | [Infrastructure Docs](../../infrastructure/AGENTS.md)

---

## Module Overview

| Module | Purpose | Key Features | Guide |
|--------|---------|--------------|-------|
| ✅ **Integrity** | Output verification | File integrity, cross-reference validation | [Details](guides/INTEGRITY_MODULE.md) |
| 📚 **Publishing** | Academic workflows | DOI validation, citation generation | [Details](guides/PUBLISHING_MODULE.md) |
| 🔬 **Scientific** | Research best practices | Numerical stability, benchmarking | [Details](guides/SCIENTIFIC_MODULE.md) |
| 📚 **Literature** | Literature management | Multi-source search, BibTeX | [Details](guides/LITERATURE_MODULE.md) |
| 🤖 **LLM** | Local LLM assistance | Ollama integration, templates | [Details](guides/LLM_MODULE.md) |
| 🎨 **Rendering** | Multi-format output | PDF, slides, web, poster | [Details](guides/RENDERING_MODULE.md) |
| 📊 **Reporting** | Pipeline reporting | Reports, error aggregation | [Details](guides/REPORTING_MODULE.md) |

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

### Literature Search

```python
from infrastructure.literature import LiteratureSearch

searcher = LiteratureSearch()
papers = searcher.search("machine learning", limit=10)
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
python3 scripts/04_validate_output.py

# Manual verification
python3 -m infrastructure.validation.cli integrity output/
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
| Integrity | hashlib, pathlib | 81% |
| Publishing | requests, bibtexparser | 86% |
| Scientific | numpy, time, psutil | 88% |
| Literature | requests, bibtexparser | 91% |
| LLM | requests, ollama | 91% |
| Rendering | pandoc, xelatex | 91% |
| Reporting | json, pathlib | 0% (pending) |

All modules work independently or together with minimal coupling.

---

## Best Practices

1. **Integrate Early** - Include modules in your workflow from the beginning
2. **Automate Validation** - Set up automated checks in your build pipeline
3. **Monitor Performance** - Track algorithm performance over time

---

## See Also

- **[API Reference](../reference/API_REFERENCE.md)** - Full API documentation
- **[Infrastructure Guide](../../infrastructure/AGENTS.md)** - Module architecture
- **[Build System](../operational/BUILD_SYSTEM.md)** - Build pipeline integration

---

**The modules provide enterprise-grade capabilities while maintaining simplicity. Each can be used independently or integrated into validation workflows.**
