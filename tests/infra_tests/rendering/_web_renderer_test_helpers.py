"""Shared helpers for web renderer test modules."""

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer


def _make_renderer(tmp_path):
    """Create a WebRenderer with config pointing to tmp_path."""
    config = RenderingConfig(
        pandoc_path="pandoc",
        web_dir=str(tmp_path / "web"),
    )
    return WebRenderer(config)
