"""Core literature search functionality."""
from infrastructure.literature.core.core import (
    LiteratureSearch,
    DownloadResult,
    SearchStatistics,
    SourceStatistics,
)
from infrastructure.literature.core.config import LiteratureConfig, BROWSER_USER_AGENTS
from infrastructure.literature.core.cli import main as cli_main
# Export cli module for direct import
from infrastructure.literature.core import cli

__all__ = [
    "LiteratureSearch",
    "DownloadResult",
    "SearchStatistics",
    "SourceStatistics",
    "LiteratureConfig",
    "BROWSER_USER_AGENTS",
    "cli_main",
    "cli",
]


