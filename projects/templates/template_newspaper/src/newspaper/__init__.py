"""The Triplicate — a ReportLab newspaper layout engine.

A small, pure-Python toolkit that renders a structured *edition* (masthead +
ordered pages of stories, boxes and figures, all defined as YAML data) into a
print-ready, large-format newspaper PDF. The engine separates four concerns:

- :mod:`newspaper.geometry`   — pure page/column arithmetic (no ReportLab).
- :mod:`newspaper.typography` — font registration + the paragraph stylesheet.
- :mod:`newspaper.content`    — the typed content model + YAML loaders.
- :mod:`newspaper.config`     — strict render configuration.
- :mod:`newspaper.components` — flowables (stories, boxes, drop caps, figures).
- :mod:`newspaper.furniture`  — canvas-drawn nameplate/bands/folios/rules.
- :mod:`newspaper.layout`     — frame construction + content flow.
- :mod:`newspaper.engine`     — the top-level render entry point.

Swapping editions is a pure data edit under ``content/``; the engine is content
agnostic.
"""

from __future__ import annotations

from .config import NewspaperConfig, load_newspaper_config
from .content import Edition, load_edition
from .engine import RenderResult, build_and_render, render_edition

__all__ = [
    "NewspaperConfig",
    "load_newspaper_config",
    "Edition",
    "load_edition",
    "RenderResult",
    "render_edition",
    "build_and_render",
]

__version__ = "1.0.0"
