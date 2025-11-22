"""Scientific poster rendering module."""
from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


class PosterRenderer:
    """Handles scientific poster generation."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path) -> Path:
        """Render poster from LaTeX."""
        return compile_latex(
            source_file,
            Path(self.config.poster_dir),
            compiler=self.config.latex_compiler
        )

