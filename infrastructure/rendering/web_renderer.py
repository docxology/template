"""Web/HTML rendering module."""
from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)


class WebRenderer:
    """Handles HTML generation."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path) -> Path:
        """Render markdown to HTML."""
        output_dir = Path(self.config.web_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{source_file.stem}.html"
        
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t", "html5",
            "-o", str(output_file),
            "--standalone",
            "--mathjax"
        ]
        
        logger.info(f"Generating HTML from {source_file}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render HTML: {e.stderr}",
                context={"source": str(source_file)}
            )

