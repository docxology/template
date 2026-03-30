"""File inventory data model and size formatting.

Contains the FileInventoryEntry dataclass and the format_file_size utility
used across inventory and reporting code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def format_file_size(bytes_size: int) -> str:
    """Convert bytes to human-readable format.

    Args:
        bytes_size: Size in bytes

    Returns:
        Human-readable size string
    """
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{round(bytes_size / 1024)}KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{round(bytes_size / (1024 * 1024))}MB"
    else:
        return f"{round(bytes_size / (1024 * 1024 * 1024))}GB"


@dataclass
class FileInventoryEntry:
    """Entry in file inventory."""

    path: Path
    size: int
    category: str
    modified: float

    @property
    def size_formatted(self) -> str:
        """Get human-readable file size."""
        return format_file_size(self.size)
