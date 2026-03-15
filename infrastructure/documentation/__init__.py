"""Documentation module - Documentation & figure management tools.

This module contains utilities for managing figures, images, and documentation
integration in research manuscripts.

Modules:
    figure_manager: Automatic figure numbering and cross-referencing
    image_manager: Image file management and insertion
    markdown_integration: Figure integration into markdown files
    glossary_gen: API documentation generation
"""

from __future__ import annotations

from .figure_manager import FigureManager, FigureMetadata
from .glossary_gen import ApiEntry, build_api_index, generate_markdown_table
from .image_manager import ImageManager
from .markdown_integration import MarkdownIntegration

__all__ = [
    "FigureManager",
    "FigureMetadata",
    "ApiEntry",
    "build_api_index",
    "generate_markdown_table",
    "ImageManager",
    "MarkdownIntegration",
]
