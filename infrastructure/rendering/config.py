"""Configuration for rendering module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


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
    docx_dir: str = "output/docx"
    epub_dir: str = "output/epub"

    # Tools
    latex_compiler: str = "xelatex"
    pandoc_path: str = "pandoc"

    # Template settings
    template_dir: str = "infrastructure/rendering/templates"

    # Format specific
    slide_theme: str = "metropolis"
    web_theme: str = "simple"

    # Format on/off toggles. PDF/HTML/Slides default True (existing behavior);
    # DOCX/EPUB default False (opt-in — preserves current pipelines untouched).
    # The pipeline orchestrator reads these and skips the corresponding render
    # path when False. See docs/operational/logging/output-design.md for the
    # config.yaml `render.formats` block that drives these from project config.
    enable_pdf: bool = True
    enable_html: bool = True
    enable_slides: bool = True
    enable_docx: bool = False
    enable_epub: bool = False

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> RenderingConfig:
        """Create configuration from environment variables.

        Supported environment variables:
        - MANUSCRIPT_DIR / FIGURES_DIR / OUTPUT_DIR
        - PDF_DIR / WEB_DIR / SLIDES_DIR / POSTER_DIR / DOCX_DIR / EPUB_DIR
        - LATEX_COMPILER (default: xelatex)
        - PANDOC_PATH (path to pandoc)
        - TEMPLATE_DIR (templates directory)
        - SLIDE_THEME (default: metropolis)
        - WEB_THEME (default: simple)
        - ENABLE_PDF / ENABLE_HTML / ENABLE_SLIDES / ENABLE_DOCX / ENABLE_EPUB
          ("0"/"1", "false"/"true", "no"/"yes" — case-insensitive)

        Args:
            env: Optional dictionary to override or replace os.environ

        Returns:
            RenderingConfig with values from environment or defaults
        """
        import os

        config_kwargs: dict[str, Any] = {}
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
            "DOCX_DIR": "docx_dir",
            "EPUB_DIR": "epub_dir",
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

        bool_mappings = {
            "ENABLE_PDF": "enable_pdf",
            "ENABLE_HTML": "enable_html",
            "ENABLE_SLIDES": "enable_slides",
            "ENABLE_DOCX": "enable_docx",
            "ENABLE_EPUB": "enable_epub",
        }
        for env_var, config_key in bool_mappings.items():
            value = env_vars.get(env_var)
            if value is not None:
                config_kwargs[config_key] = value.strip().lower() in ("1", "true", "yes", "on")

        return cls(**config_kwargs)

    @classmethod
    def from_project_config(
        cls,
        project_config: dict[str, Any] | None,
        *,
        env: dict[str, str] | None = None,
    ) -> RenderingConfig:
        """Build a config from a project's ``manuscript/config.yaml`` mapping.

        Reads the optional ``render.formats`` block:

        .. code-block:: yaml

            render:
              formats:
                pdf: true
                html: true
                slides: true
                docx: true
                epub: false

        Env vars still override (call site: ``ENABLE_<FORMAT>=0/1``). Missing
        keys fall back to the dataclass default for that field.
        """
        base = cls.from_env(env=env)
        if not project_config:
            return base
        render_block = project_config.get("render") or {}
        formats = render_block.get("formats") or {}
        if not isinstance(formats, dict):
            return base
        overrides: dict[str, Any] = {}
        format_keys = {
            "pdf": "enable_pdf",
            "html": "enable_html",
            "slides": "enable_slides",
            "docx": "enable_docx",
            "epub": "enable_epub",
        }
        for yaml_key, attr in format_keys.items():
            if yaml_key in formats:
                overrides[attr] = bool(formats[yaml_key])
        if not overrides:
            return base
        from dataclasses import replace

        return replace(base, **overrides)
