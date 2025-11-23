# Image Management Guide

## Overview

This guide covers automatic image insertion, captioning, and cross-referencing in markdown files.

## Image Manager

The `ImageManager` class handles automatic insertion of figures into markdown files:

```python
from infrastructure.documentation import ImageManager, FigureManager

figure_manager = FigureManager()
image_manager = ImageManager(figure_manager)
```

### Inserting Figures

```python
markdown_file = Path("manuscript/04_experimental_results.md")
image_manager.insert_figure(
    markdown_file,
    figure_label="fig:convergence",
    section="Experimental Results",
    position="after_section"
)
```

### Inserting References

```python
image_manager.insert_reference(
    markdown_file,
    figure_label="fig:convergence",
    text="As shown in"
)
```

### Validating Figures

```python
errors = image_manager.validate_figures(markdown_file)
for label, error in errors:
    print(f"{label}: {error}")
```

## Markdown Integration

The `MarkdownIntegration` class provides high-level integration:

```python
from markdown_integration import MarkdownIntegration

integration = MarkdownIntegration(manuscript_dir="manuscript")
```

### Detecting Sections

```python
sections = integration.detect_sections(markdown_file)
for section in sections:
    print(f"{section['name']} (level {section['level']})")
```

### Inserting Figures in Sections

```python
integration.insert_figure_in_section(
    markdown_file,
    figure_label="fig:convergence",
    section_name="Results",
    position="after"
)
```

### Validating Manuscript

```python
validation_results = integration.validate_manuscript()
for file_path, errors in validation_results.items():
    print(f"{file_path}: {len(errors)} errors")
```

### Getting Statistics

```python
stats = integration.get_figure_statistics()
print(f"Total figures: {stats['total_figures']}")
print(f"By section: {stats['figures_by_section']}")
```

## Workflow

1. **Generate figures** using visualization modules
2. **Register figures** with FigureManager
3. **Insert figures** into markdown using ImageManager
4. **Update references** automatically
5. **Validate** all figures and references

## Best Practices

1. **Register before inserting** - Always register figures first
2. **Use descriptive labels** - Use meaningful figure labels
3. **Validate regularly** - Check figures after insertion
4. **Maintain registry** - Keep figure registry up to date
5. **Check paths** - Ensure relative paths are correct

