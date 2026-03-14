"""Scientific poster rendering module."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


def render_poster(source_file: Path, config: RenderingConfig) -> Path:
    """Render a scientific poster from a LaTeX source file."""
    return compile_latex(
        source_file,
        Path(config.poster_dir),
        compiler=config.latex_compiler,
    )
