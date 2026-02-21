"""Configuration for rendering module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


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
    def from_env(cls, env: Optional[Dict[str, str]] = None) -> RenderingConfig:
        """Create configuration from environment variables.

        Supported environment variables:
        - MANUSCRIPT_DIR: Input manuscript directory
        - FIGURES_DIR: Input figures directory
        - OUTPUT_DIR: Base output directory
        - PDF_DIR: PDF output directory
        - WEB_DIR: Web output directory
        - SLIDES_DIR: Slides output directory
        - POSTER_DIR: Poster output directory
        - LATEX_COMPILER: LaTeX compiler (default: xelatex)
        - PANDOC_PATH: Path to pandoc executable
        - TEMPLATE_DIR: Directory containing templates
        - SLIDE_THEME: Theme for slides (default: metropolis)
        - WEB_THEME: Theme for web output (default: simple)

        Args:
            env: Optional dictionary to override or replace os.environ

        Returns:
            RenderingConfig with values from environment or defaults
        """
        import os

        config_kwargs: Dict[str, Any] = {}
        env_vars = env if env is not None else os.environ

        # Map environment variables to config fields
        env_mappings = {
            "MANUSCRIPT_DIR": "manuscript_dir",
            "FIGURES_DIR": "figures_dir",
            "OUTPUT_DIR": "output_dir",
            "PDF_DIR": "pdf_dir",
            "WEB_DIR": "web_dir",
            "SLIDES_DIR": "slides_dir",
            "POSTER_DIR": "poster_dir",
            "LATEX_COMPILER": "latex_compiler",
            "PANDOC_PATH": "pandoc_path",
            "TEMPLATE_DIR": "template_dir",
            "SLIDE_THEME": "slide_theme",
            "WEB_THEME": "web_theme",
        }

        for env_var, config_key in env_mappings.items():
            value = env_vars.get(env_var)
            if value is not None:
                config_kwargs[config_key] = value

        return cls(**config_kwargs)
