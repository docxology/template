---
name: infrastructure-documentation
description: Skill for the documentation infrastructure module providing figure management, image handling, markdown integration, and API glossary generation. Use when managing research figures, inserting images into manuscripts, auto-numbering figures, or generating API documentation.
---

# Documentation Module

Figure management, image handling, and documentation integration for research manuscripts.

## GeneratedFigureRegistry (`generated_figure_registry.py`)

Use the fail-closed writer for deterministic project pipelines. Figure labels,
filenames, captions, and qualified generator names remain project-owned; the
shared writer verifies that every declared file exists before atomically
writing `output/figures/figure_registry.json`.

```python
from infrastructure.documentation import publish_generated_figures

written = publish_generated_figures(
    output_dir,
    PROJECT_FIGURE_SPECS,
    generated_paths,
    schema_version="my-project-figure-registry-v1",
)
```

## FigureManager (`figure_manager.py`)

Automatic figure numbering, cross-referencing, and metadata tracking:

```python
from infrastructure.documentation import FigureManager, FigureMetadata

manager = FigureManager()

# Register a figure (label auto-generated from filename if omitted)
manager.register_figure(
    filename="results.png",
    caption="Experimental results showing...",
    label="fig:results",
    section="Results",
)

# Get figure metadata by label
meta = manager.get_figure("fig:results")  # Returns FigureMetadata | None
```

## ImageManager (`image_manager.py`)

Image file management and processing:

```python
from pathlib import Path
from infrastructure.documentation import ImageManager, FigureManager

img_manager = ImageManager(FigureManager())

# Insert a registered figure into a markdown file under a section
img_manager.insert_figure(Path("manuscript/01_intro.md"), "fig:results", section="Results")

# Validate that referenced figures exist and labels are registered
errors = img_manager.validate_figures(Path("manuscript/01_intro.md"))  # list[(label, error)]
```

## MarkdownIntegration (`markdown_integration.py`)

Auto-insertion of figures and content into markdown manuscripts:

```python
from pathlib import Path
from infrastructure.documentation import MarkdownIntegration, FigureManager

integrator = MarkdownIntegration(Path("manuscript"), FigureManager())

# Insert a figure into a named section of a markdown file
integrator.insert_figure_in_section(Path("manuscript/01_intro.md"), "fig:results", "Results")
```

## Glossary & API Documentation (`glossary_gen.py`)

Generate API documentation and glossaries from source code:

```python
from infrastructure.documentation import build_api_index, generate_markdown_table, ApiEntry
from infrastructure.documentation.glossary_gen import inject_between_markers

# Build API index from source
api_entries = build_api_index(source_dir)

# Generate markdown table
table = generate_markdown_table(api_entries)

# Inject between markers in a markdown file (operates on text, not a file path)
updated_text = inject_between_markers(
    text=original_text,
    begin_marker="<!-- API_START -->",
    end_marker="<!-- API_END -->",
    content=table,
)
```

**CLI:**

```bash
# Positional args: SRC_DIR GLOSSARY_MD (no --project flag)
uv run python -m infrastructure.documentation.generate_glossary_cli \
  projects/{name}/src projects/{name}/manuscript/98_symbols_glossary.md

# With no args, defaults to <repo>/project/src and <repo>/project/manuscript/98_symbols_glossary.md
```
