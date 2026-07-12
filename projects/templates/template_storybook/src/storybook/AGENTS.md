# AGENTS - `template_storybook/src/storybook`

This package owns the storybook exemplar's domain logic.

- `models.py` declares the frozen dataclasses shared across the package:
  `Character`, `PageSpec`, `StorybookSpec`, `RenderResult`.
- `characters.py` validates and constructs symbolic shape-family characters.
- `story.py` loads `content/story.yaml` and produces manifest metadata.
- `illustration.py` renders full-page raster scenes and composes them with text.
- `text_layout.py` owns font selection, wrapping, contrast boxes, and publication/page text overlays.
- `rendering.py` writes page PNGs, the storybook PDF, and summary artifacts.

Keep page-specific choices in `content/story.yaml` or thin scripts; keep reusable
rendering behavior here.
