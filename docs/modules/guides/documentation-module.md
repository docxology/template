# Documentation Module

> **Figure management, image handling, and API glossary generation**

**Location:** `infrastructure/documentation/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **Figure Management**: Automatic figure numbering, cross-referencing, and metadata tracking via `FigureManager`
- **Image Handling**: Image file management and manuscript insertion via `ImageManager`
- **Markdown Integration**: Figure integration into markdown manuscripts via `MarkdownIntegration`
- **API Glossary**: Automated API documentation extraction from Python source via `build_api_index`

---

## Usage Examples

### Figure Management

```python
from infrastructure.documentation import FigureManager, FigureMetadata

manager = FigureManager()

# Register a generated figure
metadata = manager.register_figure(
    filename="output/figures/architecture_overview.png",
    caption="Two-Layer Architecture Overview",
    label="fig:architecture",
)

# Get all registered figures
figures = manager.get_all_figures()
```

### API Glossary Generation

```python
from infrastructure.documentation import build_api_index, generate_markdown_table

# Scan source directory for public APIs
entries = build_api_index("projects/templates/template_code_project/src/")

# Generate markdown table
table = generate_markdown_table(entries)
print(f"Found {len(entries)} API entries")
```

**CLI Usage:**

```bash
uv run python -m infrastructure.documentation.generate_glossary_cli \
    projects/templates/template_code_project/src/ \
    projects/templates/template_code_project/manuscript/98_symbols_glossary.md
```

### Image Integration

```python
from pathlib import Path

from infrastructure.documentation import ImageManager

img_mgr = ImageManager()
img_mgr.insert_figure(
    markdown_file=Path("manuscript/03_results.md"),
    figure_label="fig:results",
)
```

---

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| `FigureManager` | Class | Figure registry with auto-numbering |
| `FigureMetadata` | Dataclass | Figure metadata container |
| `ImageManager` | Class | Image file management |
| `MarkdownIntegration` | Class | Markdown figure insertion |
| `ApiEntry` | Dataclass | API entry container |
| `build_api_index` | Function | Scan source for public APIs |
| `generate_markdown_table` | Function | Format API entries as markdown |

---

## Related Documentation

- **[Modules Guide](../modules-guide.md)** — Module overview
- **[Figures Guide](../../guides/figures-and-analysis.md)** — Figure generation workflow
- **[Infrastructure AGENTS.md](../../../infrastructure/documentation/AGENTS.md)** — Machine-readable API spec
