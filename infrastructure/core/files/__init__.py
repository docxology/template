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
from infrastructure.core.files.pdf_locator import (
    find_combined_pdf,
    find_last_output_segment_index,
)

__all__ = [
    "CopyStats",
    "FileInventoryEntry",
    "FileInventoryManager",
    "calculate_file_hash",
    "clean_output_directories",
    "copy_final_deliverables",
    "find_combined_pdf",
    "find_last_output_segment_index",
]
