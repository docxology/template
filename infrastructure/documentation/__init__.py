"""Documentation module - Documentation & figure management tools.

This module contains utilities for managing figures, images, and documentation
integration in research manuscripts.

Modules:
    figure_manager: Automatic figure numbering and cross-referencing
    generated_figure_registry: Fail-closed registries for pipeline-generated figures
    image_manager: Image file management and insertion
    markdown_integration: Figure integration into markdown files
    glossary_gen: API documentation generation
"""

from .figure_manager import FigureManager, FigureMetadata
from .generated_figure_registry import (
    FigureRegistryError,
    FigureSpecLike,
    build_generated_figure_registry,
    publish_generated_figures,
    write_generated_figure_registry,
)
from .glossary_gen import ApiEntry, build_api_index, generate_markdown_table
from .image_manager import ImageManager
from .markdown_integration import MarkdownIntegration

__all__ = [
    "FigureManager",
    "FigureMetadata",
    "FigureRegistryError",
    "FigureSpecLike",
    "build_generated_figure_registry",
    "publish_generated_figures",
    "write_generated_figure_registry",
    "ApiEntry",
    "build_api_index",
    "generate_markdown_table",
    "ImageManager",
    "MarkdownIntegration",
]
