"""Configuration for rendering module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast
from urllib.parse import urlsplit

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.security import RenderSecurityProfile

logger = get_logger(__name__)

if TYPE_CHECKING:
    from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy


_FORMAT_TOGGLES = {
    "pdf": ("enable_pdf", "ENABLE_PDF"),
    "html": ("enable_html", "ENABLE_HTML"),
    "slides": ("enable_slides", "ENABLE_SLIDES"),
    "docx": ("enable_docx", "ENABLE_DOCX"),
    "epub": ("enable_epub", "ENABLE_EPUB"),
}


def _strict_yaml_bool(value: Any, key: str) -> bool:
    """Return a YAML boolean, rejecting string truthiness traps."""
    if not isinstance(value, bool):
        raise ValueError(f"render.formats.{key} must be a YAML boolean, got {value!r}")
    return value


def _strict_slide_int(value: Any, key: str) -> int:
    """Return a strict slide-policy integer, rejecting booleans and floats."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"render.slides.{key} must be an integer, got {value!r}")
    return cast(int, value)


def _strict_slide_string(value: Any, key: str) -> str:
    """Return a non-empty slide-policy string without implicit coercion."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"render.slides.{key} must be a non-empty string, got {value!r}")
    return value


_SLIDE_YAML_FIELDS = {
    "profile": "slides_profile",
    "max_prose_words": "slides_max_prose_words",
    "max_table_rows": "slides_max_table_rows",
    "min_figure_area_percent": "slides_min_figure_area_percent",
    "title_font_pt": "slides_title_font_pt",
    "body_font_pt": "slides_body_font_pt",
    "figure_label_font_pt": "slides_figure_label_font_pt",
    "reader_href": "slides_reader_href",
}

_SLIDE_ENV_FIELDS = {
    "SLIDES_PROFILE": "slides_profile",
    "SLIDES_MAX_PROSE_WORDS": "slides_max_prose_words",
    "SLIDES_MAX_TABLE_ROWS": "slides_max_table_rows",
    "SLIDES_MIN_FIGURE_AREA_PERCENT": "slides_min_figure_area_percent",
    "SLIDES_TITLE_FONT_PT": "slides_title_font_pt",
    "SLIDES_BODY_FONT_PT": "slides_body_font_pt",
    "SLIDES_FIGURE_LABEL_FONT_PT": "slides_figure_label_font_pt",
    "SLIDES_READER_HREF": "slides_reader_href",
}


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

    # Presentation profiles are additive. ``archive`` preserves the historical
    # manuscript-to-Beamer/Reveal behavior. ``accessible`` composes both
    # writers from one semantic Pandoc AST and enforces projection-scale
    # density and typography floors before retaining an output.
    slides_profile: Literal["archive", "accessible"] = "archive"
    slides_max_prose_words: int = 80
    slides_max_table_rows: int = 8
    slides_min_figure_area_percent: int = 70
    slides_title_font_pt: int = 28
    slides_body_font_pt: int = 20
    slides_figure_label_font_pt: int = 16
    slides_reader_href: str = "../web/index.html"

    # Trusted local rendering remains the default. Callers handling external
    # submissions must opt into ``untrusted`` and provide a temporary root.
    security_profile: str = "trusted-local"
    untrusted_temp_root: str | None = None

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

    def __post_init__(self) -> None:
        """Validate the opt-in slide contract without changing legacy output."""

        if self.slides_profile not in {"archive", "accessible"}:
            raise ValueError("slides_profile must be 'archive' or 'accessible'")
        numeric_contract = (
            ("slides_max_prose_words", self.slides_max_prose_words, 1, 80),
            ("slides_max_table_rows", self.slides_max_table_rows, 1, 8),
            ("slides_min_figure_area_percent", self.slides_min_figure_area_percent, 70, 100),
            ("slides_title_font_pt", self.slides_title_font_pt, 28, 96),
            ("slides_body_font_pt", self.slides_body_font_pt, 20, 72),
            ("slides_figure_label_font_pt", self.slides_figure_label_font_pt, 16, 48),
        )
        for name, value, minimum, maximum in numeric_contract:
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}], got {value!r}")
        if (
            not isinstance(self.slides_reader_href, str)
            or not self.slides_reader_href.strip()
            or "\x00" in self.slides_reader_href
            or "\\" in self.slides_reader_href
        ):
            raise ValueError(
                "slides_reader_href must be a non-empty relative or https URL without backslashes"
            )
        parsed_reader = urlsplit(self.slides_reader_href)
        if (parsed_reader.scheme and parsed_reader.scheme != "https") or (
            not parsed_reader.scheme and self.slides_reader_href.startswith("/")
        ):
            raise ValueError(
                "slides_reader_href must be a non-empty relative or https URL without backslashes"
            )

    def accessible_slide_policy(self) -> AccessibleSlidePolicy:
        """Return the typed policy consumed by the semantic slide composer."""

        from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy

        return AccessibleSlidePolicy(
            max_prose_words=self.slides_max_prose_words,
            max_table_rows=self.slides_max_table_rows,
            min_figure_area_percent=self.slides_min_figure_area_percent,
            title_font_pt=self.slides_title_font_pt,
            body_font_pt=self.slides_body_font_pt,
            figure_label_font_pt=self.slides_figure_label_font_pt,
            reader_href=self.slides_reader_href,
        )

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> RenderingConfig:
        """Create configuration from environment variables.

        Supported environment variables:
        - MANUSCRIPT_DIR / FIGURES_DIR / OUTPUT_DIR
        - PDF_DIR / WEB_DIR / SLIDES_DIR / DOCX_DIR / EPUB_DIR
        - LATEX_COMPILER (default: xelatex)
        - PANDOC_PATH (path to pandoc)
        - TEMPLATE_DIR (templates directory)
        - SLIDE_THEME (default: metropolis)
        - WEB_THEME (default: simple)
        - ENABLE_PDF / ENABLE_HTML / ENABLE_SLIDES / ENABLE_DOCX / ENABLE_EPUB
          ("0"/"1", "false"/"true", "no"/"yes" — case-insensitive)
        - SLIDES_PROFILE and SLIDES_* density/typography policy values

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
            "DOCX_DIR": "docx_dir",
            "EPUB_DIR": "epub_dir",
            "LATEX_COMPILER": "latex_compiler",
            "PANDOC_PATH": "pandoc_path",
            "TEMPLATE_DIR": "template_dir",
            "SLIDE_THEME": "slide_theme",
            "WEB_THEME": "web_theme",
            "RENDER_SECURITY_PROFILE": "security_profile",
            "RENDER_UNTRUSTED_TEMP_ROOT": "untrusted_temp_root",
        }

        for env_var, config_key in env_mappings.items():
            value = env_vars.get(env_var)
            if value is not None:
                config_kwargs[config_key] = value

        for config_key, env_var in _FORMAT_TOGGLES.values():
            value = env_vars.get(env_var)
            if value is not None:
                config_kwargs[config_key] = value.strip().lower() in ("1", "true", "yes", "on")

        for env_var, config_key in _SLIDE_ENV_FIELDS.items():
            value = env_vars.get(env_var)
            if value is None:
                continue
            if config_key in {"slides_profile", "slides_reader_href"}:
                config_kwargs[config_key] = value
            else:
                try:
                    config_kwargs[config_key] = int(value)
                except ValueError as exc:
                    raise ValueError(f"{env_var} must be an integer, got {value!r}") from exc

        return cls(**config_kwargs)

    @classmethod
    def from_project_config(
        cls,
        project_config: dict[str, Any] | None,
        *,
        env: dict[str, str] | None = None,
    ) -> RenderingConfig:
        """Build a config from a project's ``manuscript/config.yaml`` mapping.

        Reads the optional ``render.formats`` and ``render.slides`` blocks:

        .. code-block:: yaml

            render:
              formats:
                pdf: true
                html: true
                slides: true
                docx: true
                epub: false
              slides:
                profile: accessible
                max_prose_words: 80
                max_table_rows: 8

        Env vars still override (call site: ``ENABLE_<FORMAT>=0/1``). Missing
        keys fall back to the dataclass default for that field.
        """
        import os

        env_vars = env if env is not None else os.environ
        base = cls.from_env(env=env)
        if not project_config:
            return base
        render_block = project_config.get("render") or {}
        if not isinstance(render_block, dict):
            return base
        formats = render_block.get("formats") or {}
        overrides: dict[str, Any] = {}
        if isinstance(formats, dict):
            for yaml_key, (attr, env_var) in _FORMAT_TOGGLES.items():
                if yaml_key in formats:
                    format_value = _strict_yaml_bool(formats[yaml_key], yaml_key)
                    if env_vars.get(env_var) is None:
                        overrides[attr] = format_value

        raw_slides = render_block.get("slides")
        slides = {} if raw_slides is None else raw_slides
        if not isinstance(slides, dict):
            raise ValueError("render.slides must be a mapping")
        unknown_slide_fields = sorted(set(slides) - set(_SLIDE_YAML_FIELDS))
        if unknown_slide_fields:
            raise ValueError(f"render.slides contains unknown fields: {unknown_slide_fields}")
        for yaml_key, attr in _SLIDE_YAML_FIELDS.items():
            if yaml_key not in slides:
                continue
            raw_value = slides[yaml_key]
            if attr in {"slides_profile", "slides_reader_href"}:
                slide_value: Any = _strict_slide_string(raw_value, yaml_key)
            else:
                slide_value = _strict_slide_int(raw_value, yaml_key)
            env_var = next(key for key, value in _SLIDE_ENV_FIELDS.items() if value == attr)
            if env_vars.get(env_var) is None:
                overrides[attr] = slide_value
        if not overrides:
            return base
        from dataclasses import replace

        return replace(base, **overrides)

    def security(self) -> RenderSecurityProfile:
        """Return the configured renderer subprocess security profile."""
        return RenderSecurityProfile(
            name=self.security_profile,
            temp_root=Path(self.untrusted_temp_root) if self.untrusted_temp_root else None,
        )
