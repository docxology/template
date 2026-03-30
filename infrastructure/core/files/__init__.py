"""Core files subpackage — file operations, cleanup, and inventory.

Re-exports primary symbols for ``from infrastructure.core.files import …`` usage.
"""

from __future__ import annotations

from infrastructure.core.files.cleanup import clean_output_directories
from infrastructure.core.files.inventory import FileInventoryEntry, FileInventoryManager
from infrastructure.core.files.operations import (
    CopyStats,
    calculate_file_hash,
    copy_final_deliverables,
)

__all__ = [
    "CopyStats",
    "FileInventoryEntry",
    "FileInventoryManager",
    "calculate_file_hash",
    "clean_output_directories",
    "copy_final_deliverables",
]
