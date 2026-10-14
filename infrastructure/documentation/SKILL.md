---
name: infrastructure-documentation
description: Figure metadata, deterministic generated-figure registries, and source-derived API documentation. Use when publishing figure inventories, validating generated image files, or maintaining API glossaries.
---

# Documentation Module

Figure metadata, file-bound publication registries, and source-derived documentation.

## Generated figure registries (`generated_figure_registry.py`)

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

Label-indexed metadata registration and persistence:

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

## Manuscript figures

Author images and references in Pandoc form; pandoc-crossref assigns presentation
numbers during rendering:

```markdown
![Measured analysis results.](../output/figures/results.png){#fig:results width=80%}

[@fig:results] summarizes the analysis.
```

Bind captions and alt text to the same analysis outputs as the figure. Use
`publish_generated_figures` or `write_generated_figure_registry` to validate actual
files before publication; metadata registration alone does not validate them.

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

```
