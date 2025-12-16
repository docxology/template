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

## Troubleshooting

### Figure Registration Fails

**Issue**: `register_figure()` fails or doesn't persist figure data.

**Solutions**:
- Verify output directory is writable
- Check figure registry JSON file permissions
- Ensure figure file exists before registration
- Review JSON serialization for special characters
- Check disk space availability

### Image Insertion Errors

**Issue**: `insert_figure()` fails to insert figure into markdown.

**Solutions**:
- Verify markdown file exists and is writable
- Check section name matches exactly (case-sensitive)
- Ensure figure is registered before insertion
- Review markdown file structure for insertion points
- Check file encoding (UTF-8 required)

### Cross-Reference Generation Issues

**Issue**: Generated cross-references are incorrect or missing.

**Solutions**:
- Verify figure labels follow naming conventions
- Check LaTeX label syntax is correct
- Ensure figures are registered before reference generation
- Review reference format requirements
- Check for duplicate labels

### API Documentation Generation Fails

**Issue**: `build_api_index()` returns empty or incomplete index.

**Solutions**:
- Verify source directory path is correct
- Check Python files are parseable (no syntax errors)
- Ensure functions have docstrings
- Review AST parsing for complex code
- Check file permissions for source files

### Markdown Integration Errors

**Issue**: `MarkdownIntegration` methods fail or produce incorrect results.

**Solutions**:
- Verify manuscript directory path is correct
- Check markdown file structure is valid
- Ensure sections are properly formatted
- Review section detection logic
- Check file encoding and line endings

## Best Practices

### Figure Management

- **Register Early**: Register figures immediately after generation
- **Consistent Labels**: Use consistent label naming conventions
- **Persistent Registry**: Keep figure registry in version control
- **Validate References**: Check all references before final rendering

### Image Handling

- **Relative Paths**: Use relative paths for portability
- **Validate Existence**: Check images exist before insertion
- **Consistent Formatting**: Use consistent image formatting
- **Optimize Images**: Optimize images for publication quality

### Cross-Reference Management

- **Unique Labels**: Ensure all labels are unique
- **Consistent Format**: Use consistent reference formats
- **Validate References**: Check references before rendering
- **Document Patterns**: Document reference patterns for team

### API Documentation

- **Complete Docstrings**: Write comprehensive docstrings
- **Type Hints**: Include type hints for better documentation
- **Examples**: Provide usage examples in docstrings
- **Keep Current**: Update documentation with code changes

### Markdown Integration

- **Structured Sections**: Use consistent section structure
- **Clear Markers**: Use clear markers for insertion points
- **Validate Structure**: Validate markdown structure before processing
- **Test Integration**: Test integration with actual manuscript files

### Documentation Workflow

- **Automate**: Integrate documentation generation into build pipeline
- **Version Control**: Track documentation changes
- **Review Regularly**: Review documentation for accuracy
- **Update Promptly**: Update documentation when code changes

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance

