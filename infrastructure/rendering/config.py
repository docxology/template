"""Configuration for rendering module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

@dataclass
class RenderingConfig:
    """Configuration for rendering output."""
    
    # Input paths
    manuscript_dir: str = "manuscript"
    figures_dir: str = "output/figures"
    
    # Output paths
    output_dir: str = "output"
    pdf_dir: str = "output/pdf"
    web_dir: str = "output/web"
    slides_dir: str = "output/slides"
    poster_dir: str = "output/posters"
    
    # Tools
    latex_compiler: str = "xelatex"
    pandoc_path: str = "pandoc"
    
    # Template settings
    template_dir: str = "infrastructure/rendering/templates"
    
    # Format specific
    slide_theme: str = "metropolis"
    web_theme: str = "simple"

    @classmethod
    def from_env(cls) -> RenderingConfig:
        """Create configuration from environment variables."""
        return cls()

