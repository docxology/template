# Infrastructure Layer - Quick Reference

Generic build, validation, and document management tools.

## What's Here

Build orchestration, PDF validation, figure management, and academic publishing support.

**Not research-specific.** Reusable across any project using this template.

## Quick Start

### Using Infrastructure Modules

```python
# Register and manage figures
from infrastructure.figure_manager import FigureManager

fm = FigureManager()
fm.register_figure("result.png", label="fig:results")
latex_code = fm.generate_latex_figure_block("fig:results")

# Validate document integrity
from infrastructure.integrity import verify_cross_references

issues = verify_cross_references(markdown_dir)
if issues:
    print(f"Found {len(issues)} reference problems")

# Generate API documentation
from infrastructure.glossary_gen import build_api_index, generate_markdown_table

api_docs = build_api_index("src/")
table = generate_markdown_table(api_docs)
```

## Modules

| Module | Purpose |
|--------|---------|
| `build_verifier.py` | Verify build artifacts and reproducibility |
| `integrity.py` | Check file integrity and cross-references |
| `quality_checker.py` | Analyze document quality |
| `reproducibility.py` | Track build reproducibility |
| `publishing.py` | Academic publishing support (DOI, citations) |
| `pdf_validator.py` | Validate PDF rendering |
| `glossary_gen.py` | Auto-generate API documentation |
| `markdown_integration.py` | Integrate figures into markdown |
| `figure_manager.py` | Manage figure numbering and references |
| `image_manager.py` | Manage image files |

## Key Concepts

### Layer 1 Architecture

This is **Layer 1** of the two-layer design:
- **Build and validation tools** (this layer)
- **Scientific algorithms** (scientific/ layer)

Infrastructure is **generic** and **project-independent**.

### 100% Tested

All modules have 100% test coverage. No code ships without tests.

## File Organization

```
src/infrastructure/
├── __init__.py                    # Package initialization
├── AGENTS.md                      # Detailed documentation (you are here)
├── README.md                      # This file
├── build_verifier.py              # Build artifact verification
├── integrity.py                   # Integrity checking
├── quality_checker.py             # Quality analysis
├── reproducibility.py             # Reproducibility tracking
├── publishing.py                  # Publishing support
├── pdf_validator.py               # PDF validation
├── glossary_gen.py                # API documentation
├── markdown_integration.py         # Figure integration
├── figure_manager.py              # Figure management
└── image_manager.py               # Image management
```

## Testing

```bash
# Test infrastructure layer
pytest tests/infrastructure/ --cov=src/infrastructure

# All tests with coverage
pytest tests/ --cov=src
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../scientific/README.md`](../scientific/README.md) - Scientific layer
- [`../../docs/TWO_LAYER_ARCHITECTURE.md`](../../docs/TWO_LAYER_ARCHITECTURE.md) - Architecture guide
- [`../../docs/DECISION_TREE.md`](../../docs/DECISION_TREE.md) - Code placement guide

## Quick Facts

- **Generic** across projects ✅
- **100% test coverage** ✅
- **No domain assumptions** ✅
- **Well-tested** ✅
- **Reusable** ✅

