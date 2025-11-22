# Rendering Module

Multi-format output generation for research.

## Features

- **Consolidated Pipeline**: Single entry point for all formats.
- **Multiple Outputs**: PDF, Slides (Beamer/HTML), Web, Posters.
- **Quality Control**: Automated compilation checks and logging.

## Quick Start

```python
from infrastructure.rendering import RenderManager
from pathlib import Path

manager = RenderManager()
manager.render_pdf(Path("manuscript/paper.tex"))
```

