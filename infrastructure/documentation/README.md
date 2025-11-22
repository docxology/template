# Documentation Module - Quick Reference

Tools for managing figures, images, and markdown documentation.

## Quick Start

```python
from infrastructure.documentation import (
    FigureManager,
    ImageManager,
    MarkdownIntegration,
    build_api_index,
    generate_markdown_table
)

# Register a figure
fm = FigureManager()
fm.register_figure("plot.png", "Results", label="fig:results")

# Insert into markdown
im = ImageManager(fm)
im.insert_figure(Path("results.md"), "fig:results")

# Generate API docs
entries = build_api_index("src/")
markdown = generate_markdown_table(entries)
```

## Modules

- **figure_manager** - Automatic figure numbering and LaTeX generation
- **image_manager** - Image insertion and reference management
- **markdown_integration** - Markdown section detection and figure integration
- **glossary_gen** - API documentation generation from source code

## Key Classes

### FigureManager
- `register_figure()` - Register with automatic numbering
- `generate_latex_figure_block()` - LaTeX code generation
- `generate_reference()` - Cross-reference generation
- `get_all_figures()` - Retrieve registered figures

### ImageManager
- `insert_figure()` - Insert figure into markdown
- `insert_reference()` - Add figure reference
- `validate_figures()` - Check figure integrity
- `get_figure_list()` - Get referenced figures

### MarkdownIntegration
- `detect_sections()` - Find markdown sections
- `insert_figure_in_section()` - Insert figure in section
- `generate_table_of_figures()` - Create figure listing
- `update_all_references()` - Sync all references
- `validate_manuscript()` - Check document integrity

## Key Functions

### API Documentation
- `build_api_index(src_dir)` - Parse source for public APIs
- `generate_markdown_table(entries)` - Create Markdown table
- `inject_between_markers()` - Update content sections

## CLI

```bash
# Generate API documentation
python3 -m infrastructure.documentation generate-api src/

# Insert figures
python3 -m infrastructure.documentation insert-figures manuscript/

# Create figure list
python3 -m infrastructure.documentation create-figure-list manuscript/
```

## Testing

```bash
pytest tests/infrastructure/test_documentation/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).

