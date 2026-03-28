"""Scientific poster rendering module."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


class PosterRenderer:
    """Render scientific posters from LaTeX source files.

    Outputs to config.poster_dir (not pdf_dir), distinguishing poster
    artifacts from regular PDF article outputs.
    """

    def __init__(self, config: RenderingConfig) -> None:
        self.config = config

    def render(self, source_file: Path) -> Path:
        """Render a scientific poster from a LaTeX source file."""
        return compile_latex(
            source_file,
            Path(self.config.poster_dir),
            compiler=self.config.latex_compiler,
        )


def render_poster(source_file: Path, config: RenderingConfig) -> Path:
    """Render a scientific poster from a LaTeX source file.

    Thin wrapper around PosterRenderer for backwards compatibility.
    """
    return PosterRenderer(config).render(source_file)
