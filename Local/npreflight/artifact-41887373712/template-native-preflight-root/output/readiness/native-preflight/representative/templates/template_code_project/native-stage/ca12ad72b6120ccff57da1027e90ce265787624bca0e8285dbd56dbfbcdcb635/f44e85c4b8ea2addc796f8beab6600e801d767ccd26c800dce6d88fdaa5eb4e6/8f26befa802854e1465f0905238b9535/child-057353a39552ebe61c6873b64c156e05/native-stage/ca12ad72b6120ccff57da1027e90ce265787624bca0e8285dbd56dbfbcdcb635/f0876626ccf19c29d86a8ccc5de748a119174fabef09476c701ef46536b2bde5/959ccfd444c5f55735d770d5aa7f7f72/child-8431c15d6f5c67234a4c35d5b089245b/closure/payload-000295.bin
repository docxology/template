"""Documentation module - Documentation & figure management tools.

This module provides figure metadata persistence, generated-figure registries,
and source-derived documentation indexes. Manuscripts use Pandoc image syntax
and bracket-cite cross-references.

Modules:
    figure_manager: Figure metadata registration and persistence
    generated_figure_registry: Fail-closed registries for pipeline-generated figures
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
]
