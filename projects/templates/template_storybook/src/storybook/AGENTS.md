# AGENTS - `template_storybook/src/storybook`

This package owns the storybook exemplar's domain logic.

- `characters.py` validates and constructs symbolic shape-family characters.
- `story.py` loads `content/story.yaml` and produces manifest metadata.
- `illustration.py` renders full-page raster scenes and text overlays.
- `rendering.py` writes page PNGs, the storybook PDF, and summary artifacts.

Keep page-specific choices in `content/story.yaml` or thin scripts; keep reusable
rendering behavior here.
