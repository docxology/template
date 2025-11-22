# Documentation Module

## Purpose

The Documentation module provides comprehensive tools for managing figures, images, and markdown integration in research manuscripts. It enables automatic figure numbering, cross-reference management, and API documentation generation.

## Architecture

### Core Components

**figure_manager.py**
- Automatic figure numbering and registry management
- LaTeX figure block generation
- Cross-reference generation
- Figure list and table of figures generation
- Persistent figure registry in JSON format

**image_manager.py**
- Image file insertion into markdown
- Figure reference creation
- Image validation in markdown files
- Figure list extraction
- Insertion point detection and management

**markdown_integration.py**
- Markdown section detection
- Figure insertion into specific sections
- Table of figures generation
- Reference updates across documents
- Manuscript validation
- Figure statistics collection

**glossary_gen.py**
- API index building from source code via AST
- Markdown table generation from API entries
- Marker-based content injection

## Key Features

### Figure Management
```python
from infrastructure.documentation import FigureManager

fm = FigureManager()
metadata = fm.register_figure(
    filename="result.png",
    caption="Results visualization",
    label="fig:results",
    section="Results"
)
latex_block = fm.generate_latex_figure_block("fig:results")
```

### Image Management
```python
from infrastructure.documentation import ImageManager

im = ImageManager()
success = im.insert_figure(
    Path("manuscript/03_results.md"),
    "fig:results",
    section="Results"
)
```

### Markdown Integration
```python
from infrastructure.documentation import MarkdownIntegration

mi = MarkdownIntegration(manuscript_dir=Path("manuscript"))
sections = mi.detect_sections(Path("manuscript/intro.md"))
mi.insert_figure_in_section(Path("manuscript/results.md"), "fig:results", "Results")
```

### API Documentation
```python
from infrastructure.documentation import build_api_index, generate_markdown_table

entries = build_api_index("src/")
markdown = generate_markdown_table(entries)
```

## Testing

Run documentation tests with:
```bash
pytest tests/infrastructure/test_documentation/
```

## Configuration

No specific configuration required. Figure registry stored in `output/figures/figure_registry.json`.

## Integration

Documentation module is used by:
- Manuscript generation pipeline
- Figure numbering workflows
- API reference generation
- Cross-reference systems

## See Also

- [`validation/`](../validation/) - Validation & quality assurance
- [`build/`](../build/) - Build & reproducibility tools

