"""Scientific poster rendering module."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


def render_poster(source_file: Path, config: RenderingConfig) -> Path:
    """Render a scientific poster from a LaTeX source file.

<<<<<<< HEAD
    def __init__(self, config: RenderingConfig):
        """Initialize the poster renderer with configuration."""
        self.config = config

    def render(self, source_file: Path) -> Path:
        """Render poster from LaTeX."""
        return compile_latex(
            source_file,
            Path(self.config.poster_dir),
            compiler=self.config.latex_compiler,
        )
=======
    Policy: directs output to config.poster_dir (not pdf_dir), distinguishing
    poster artifacts from regular PDF article outputs.
    """
    return compile_latex(
        source_file,
        Path(config.poster_dir),
        compiler=config.latex_compiler,
    )
>>>>>>> desloppify/code-health
