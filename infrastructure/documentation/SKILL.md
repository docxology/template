---
name: infrastructure-documentation
description: Skill for the documentation infrastructure module providing figure management, image handling, markdown integration, and API glossary generation. Use when managing research figures, inserting images into manuscripts, auto-numbering figures, or generating API documentation.
---

# Documentation Module

Figure management, image handling, and documentation integration for research manuscripts.

## FigureManager (`figure_manager.py`)

Automatic figure numbering, cross-referencing, and metadata tracking:

```python
from infrastructure.documentation import FigureManager, FigureMetadata

manager = FigureManager()

# Register a figure
manager.register(
    name="results_plot",
    path="figures/results.png",
    caption="Experimental results showing...",
)

# Get figure metadata
meta = manager.get("results_plot")  # Returns FigureMetadata
```

## ImageManager (`image_manager.py`)

Image file management and processing:

```python
from infrastructure.documentation import ImageManager

img_manager = ImageManager()

# Manage images in a project
img_manager.scan(figures_dir)
img_manager.get_image_path("results.png")
```

## MarkdownIntegration (`markdown_integration.py`)

Auto-insertion of figures and content into markdown manuscripts:

```python
from infrastructure.documentation import MarkdownIntegration

integrator = MarkdownIntegration()

# Insert figure references into markdown
integrator.insert_figures(manuscript_path, figure_manager)
```

## Glossary & API Documentation (`glossary_gen.py`)

Generate API documentation and glossaries from source code:

```python
from infrastructure.documentation import (
    build_api_index, generate_markdown_table,
    inject_between_markers, ApiEntry,
)

# Build API index from source
api_entries = build_api_index(source_dir)

# Generate markdown table
table = generate_markdown_table(api_entries)

# Inject between markers in a markdown file
inject_between_markers(
    file_path,
    start_marker="<!-- API_START -->",
    end_marker="<!-- API_END -->",
    content=table,
)
```

**CLI:**

```bash
python3 -m infrastructure.documentation.generate_glossary_cli --project {name}
```
