"""Core file utilities with stable, on-demand public providers.

Leaf readers do not initialize unrelated cleanup, inventory, or copy helpers.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infrastructure.core.files.cleanup import clean_final_output_directory, clean_output_directories
    from infrastructure.core.files.inventory import FileInventoryEntry, FileInventoryManager
    from infrastructure.core.files.operations import CopyStats, calculate_file_hash, copy_final_deliverables
    from infrastructure.core.files.pdf_locator import find_combined_pdf, find_last_output_segment_index

_EXPORTS = {
    "CopyStats": (".operations", "CopyStats"),
    "FileInventoryEntry": (".inventory", "FileInventoryEntry"),
    "FileInventoryManager": (".inventory", "FileInventoryManager"),
    "calculate_file_hash": (".operations", "calculate_file_hash"),
    "clean_final_output_directory": (".cleanup", "clean_final_output_directory"),
    "clean_output_directories": (".cleanup", "clean_output_directories"),
    "copy_final_deliverables": (".operations", "copy_final_deliverables"),
    "find_combined_pdf": (".pdf_locator", "find_combined_pdf"),
    "find_last_output_segment_index": (".pdf_locator", "find_last_output_segment_index"),
}

__all__ = [
    "CopyStats",
    "FileInventoryEntry",
    "FileInventoryManager",
    "calculate_file_hash",
    "clean_final_output_directory",
    "clean_output_directories",
    "copy_final_deliverables",
    "find_combined_pdf",
    "find_last_output_segment_index",
]


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXPORTS.keys())
