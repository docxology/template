"""Slides rendering module."""
from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)


class SlidesRenderer:
    """Handles slide generation (Beamer/Reveal.js)."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path, format: str = "beamer") -> Path:
        """Render slides from markdown."""
        output_dir = Path(self.config.slides_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_ext = "pdf" if format == "beamer" else "html"
        output_file = output_dir / f"{source_file.stem}_slides.{output_ext}"
        
        to_format = "beamer" if format == "beamer" else "revealjs"
        
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t", to_format,
            "-o", str(output_file),
            "--standalone"
        ]
        
        if format == "revealjs":
            cmd.extend(["-V", f"theme={self.config.slide_theme}"])
            
        logger.info(f"Generating slides ({format}) from {source_file}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render slides: {e.stderr}",
                context={"source": str(source_file), "format": format}
            )

