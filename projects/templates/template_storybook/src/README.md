# Storybook Source

`storybook/` loads `content/story.yaml`, validates the cast and page list,
generates symbolic cube/tetrahedron characters, renders full-page PNG
illustrations, and assembles the final PDF.

The important modules are:

- `characters.py` - character generation and cast validation
- `models.py` - frozen dataclasses shared across the package (`Character`, `PageSpec`, `StorybookSpec`, `RenderResult`)
- `story.py` - YAML loading, trim sizes, and metadata payloads
- `illustration.py` - procedural full-page scene drawing
- `text_layout.py` - deterministic font selection, wrapping, and text overlays
- `rendering.py` - page rendering and PDF assembly
