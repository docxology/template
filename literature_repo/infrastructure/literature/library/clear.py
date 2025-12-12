"""Clear operations for literature library management.

Provides functions to clear PDFs, summaries, and library index
with confirmation and safety checks.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.library.index import LibraryIndex
from infrastructure.literature.core.config import LiteratureConfig

logger = get_logger(__name__)


def clear_pdfs(confirm: bool = True, interactive: bool = False) -> Dict[str, Any]:
    """Clear all PDFs from the data/pdfs directory.
    
    Args:
        confirm: Whether to require confirmation (default: True).
        interactive: Whether in interactive mode (prompts user).
        
    Returns:
        Dictionary with operation results:
        - success: bool
        - files_removed: int
        - size_freed_mb: float
        - message: str
    """
    pdf_dir = Path("data/pdfs")
    
    if not pdf_dir.exists():
        return {
            "success": True,
            "files_removed": 0,
            "size_freed_mb": 0.0,
            "message": "PDF directory does not exist"
        }
    
    # Count files and size
    pdf_files = list(pdf_dir.glob("*.pdf"))
    total_size = sum(f.stat().st_size for f in pdf_files if f.is_file())
    file_count = len(pdf_files)
    
    if file_count == 0:
        return {
            "success": True,
            "files_removed": 0,
            "size_freed_mb": 0.0,
            "message": "No PDFs to clear"
        }
    
    # Confirmation
    if confirm:
        if interactive:
            print(f"\n⚠️  This will remove {file_count} PDF files ({total_size / (1024*1024):.1f} MB)")
            response = input("Clear all PDFs? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                return {
                    "success": False,
                    "files_removed": 0,
                    "size_freed_mb": 0.0,
                    "message": "Operation cancelled by user"
                }
        else:
            logger.warning(f"Clearing {file_count} PDF files ({total_size / (1024*1024):.1f} MB)")
    
    # Remove files
    removed = 0
    for pdf_file in pdf_files:
        try:
            pdf_file.unlink()
            removed += 1
        except Exception as e:
            logger.warning(f"Failed to remove {pdf_file}: {e}")
    
    # Update library index to remove PDF paths
    try:
        config = LiteratureConfig.from_env()
        library_index = LibraryIndex(config)
        entries = library_index.list_entries()
        updated = 0
        for entry in entries:
            if entry.pdf_path:
                library_index.update_pdf_path(entry.citation_key, None)
                updated += 1
        logger.info(f"Updated {updated} library entries to remove PDF paths")
    except Exception as e:
        logger.warning(f"Failed to update library index: {e}")
    
    size_mb = total_size / (1024 * 1024)
    logger.info(f"Cleared {removed} PDF files ({size_mb:.1f} MB)")
    
    return {
        "success": True,
        "files_removed": removed,
        "size_freed_mb": size_mb,
        "message": f"Cleared {removed} PDF files"
    }


def clear_summaries(confirm: bool = True, interactive: bool = False) -> Dict[str, Any]:
    """Clear all summaries from the data/summaries directory.
    
    Args:
        confirm: Whether to require confirmation (default: True).
        interactive: Whether in interactive mode (prompts user).
        
    Returns:
        Dictionary with operation results:
        - success: bool
        - files_removed: int
        - size_freed_mb: float
        - message: str
    """
    summaries_dir = Path("data/summaries")
    
    if not summaries_dir.exists():
        return {
            "success": True,
            "files_removed": 0,
            "size_freed_mb": 0.0,
            "message": "Summaries directory does not exist"
        }
    
    # Count files and size
    summary_files = list(summaries_dir.glob("*_summary.md"))
    total_size = sum(f.stat().st_size for f in summary_files if f.is_file())
    file_count = len(summary_files)
    
    if file_count == 0:
        return {
            "success": True,
            "files_removed": 0,
            "size_freed_mb": 0.0,
            "message": "No summaries to clear"
        }
    
    # Confirmation
    if confirm:
        if interactive:
            print(f"\n⚠️  This will remove {file_count} summary files ({total_size / (1024*1024):.1f} MB)")
            response = input("Clear all summaries? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                return {
                    "success": False,
                    "files_removed": 0,
                    "size_freed_mb": 0.0,
                    "message": "Operation cancelled by user"
                }
        else:
            logger.warning(f"Clearing {file_count} summary files ({total_size / (1024*1024):.1f} MB)")
    
    # Remove files
    removed = 0
    for summary_file in summary_files:
        try:
            summary_file.unlink()
            removed += 1
        except Exception as e:
            logger.warning(f"Failed to remove {summary_file}: {e}")
    
    size_mb = total_size / (1024 * 1024)
    logger.info(f"Cleared {removed} summary files ({size_mb:.1f} MB)")
    
    return {
        "success": True,
        "files_removed": removed,
        "size_freed_mb": size_mb,
        "message": f"Cleared {removed} summary files"
    }


def clear_library(confirm: bool = True, interactive: bool = False) -> Dict[str, Any]:
    """Clear the library completely (total clear).
    
    This performs a complete clear operation that removes:
    - Library index entries (data/library.json)
    - All PDFs (data/pdfs/)
    - All summaries (data/summaries/)
    - Progress file (literature/summarization_progress.json)
    - BibTeX file (data/references.bib)
    
    Args:
        confirm: Whether to require confirmation (default: True).
        interactive: Whether in interactive mode (prompts user).
        
    Returns:
        Dictionary with operation results:
        - success: bool
        - entries_removed: int
        - pdfs_removed: int
        - pdfs_size_mb: float
        - summaries_removed: int
        - summaries_size_mb: float
        - progress_file_removed: bool
        - bibtex_file_removed: bool
        - message: str
    """
    try:
        config = LiteratureConfig.from_env()
        library_index = LibraryIndex(config)
        entries = library_index.list_entries()
        entry_count = len(entries)
        
        # Count PDFs
        pdf_dir = Path("data/pdfs")
        pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
        pdf_count = len(pdf_files)
        pdf_size = sum(f.stat().st_size for f in pdf_files if f.is_file())
        pdf_size_mb = pdf_size / (1024 * 1024)
        
        # Count summaries
        summaries_dir = Path("data/summaries")
        summary_files = list(summaries_dir.glob("*_summary.md")) if summaries_dir.exists() else []
        summary_count = len(summary_files)
        summary_size = sum(f.stat().st_size for f in summary_files if f.is_file())
        summary_size_mb = summary_size / (1024 * 1024)
        
        # Check progress file
        progress_file = Path("literature/summarization_progress.json")
        progress_file_exists = progress_file.exists()
        
        # Check BibTeX file
        bibtex_file = Path("data/references.bib")
        bibtex_file_exists = bibtex_file.exists()
        if bibtex_file_exists:
            try:
                bibtex_size = bibtex_file.stat().st_size
                bibtex_size_mb = bibtex_size / (1024 * 1024)
            except Exception as e:
                logger.warning(f"Failed to get BibTeX file size: {e}")
                bibtex_size = 0
                bibtex_size_mb = 0.0
        else:
            bibtex_size = 0
            bibtex_size_mb = 0.0
        
        # Check if everything is already empty
        if entry_count == 0 and pdf_count == 0 and summary_count == 0 and not progress_file_exists and not bibtex_file_exists:
            return {
                "success": True,
                "entries_removed": 0,
                "pdfs_removed": 0,
                "pdfs_size_mb": 0.0,
                "summaries_removed": 0,
                "summaries_size_mb": 0.0,
                "progress_file_removed": False,
                "bibtex_file_removed": False,
                "message": "Library is already empty"
            }
        
        # Confirmation
        if confirm:
            if interactive:
                print(f"\n⚠️  WARNING: This will perform a TOTAL CLEAR of the literature library")
                print(f"   This will permanently delete:")
                print(f"   • {entry_count} library index entries")
                print(f"   • {pdf_count} PDF files ({pdf_size_mb:.1f} MB)")
                print(f"   • {summary_count} summary files ({summary_size_mb:.1f} MB)")
                if progress_file_exists:
                    print(f"   • Progress tracking file (summarization_progress.json)")
                if bibtex_file_exists:
                    print(f"   • BibTeX file (references.bib, {bibtex_size_mb:.1f} MB)")
                print(f"\n   This action cannot be undone!")
                response = input("Clear library completely? [y/N]: ").strip().lower()
                if response not in ('y', 'yes'):
                    return {
                        "success": False,
                        "entries_removed": 0,
                        "pdfs_removed": 0,
                        "pdfs_size_mb": 0.0,
                        "summaries_removed": 0,
                        "summaries_size_mb": 0.0,
                        "progress_file_removed": False,
                        "bibtex_file_removed": False,
                        "message": "Operation cancelled by user"
                    }
            else:
                logger.warning(
                    f"Clearing library completely: {entry_count} entries, "
                    f"{pdf_count} PDFs ({pdf_size_mb:.1f} MB), "
                    f"{summary_count} summaries ({summary_size_mb:.1f} MB)"
                )
        
        # Delete in order: PDFs, summaries, progress file, then library index
        
        # 1. Delete PDFs
        pdfs_removed = 0
        for pdf_file in pdf_files:
            try:
                pdf_file.unlink()
                pdfs_removed += 1
            except Exception as e:
                logger.warning(f"Failed to remove PDF {pdf_file}: {e}")
        
        # 2. Delete summaries
        summaries_removed = 0
        for summary_file in summary_files:
            try:
                summary_file.unlink()
                summaries_removed += 1
            except Exception as e:
                logger.warning(f"Failed to remove summary {summary_file}: {e}")
        
        # 3. Delete progress file
        progress_removed = False
        if progress_file_exists:
            try:
                progress_file.unlink()
                progress_removed = True
                logger.info("Removed summarization_progress.json")
            except Exception as e:
                logger.warning(f"Failed to remove progress file: {e}")
        
        # 4. Delete BibTeX file
        bibtex_removed = False
        if bibtex_file_exists:
            try:
                bibtex_file.unlink()
                bibtex_removed = True
                logger.info("Removed references.bib")
            except Exception as e:
                logger.warning(f"Failed to remove BibTeX file: {e}")
        
        # 5. Clear all library index entries
        entries_removed = 0
        for entry in entries:
            try:
                library_index.remove_entry(entry.citation_key)
                entries_removed += 1
            except Exception as e:
                logger.warning(f"Failed to remove entry {entry.citation_key}: {e}")
        
        # Log summary
        logger.info(
            f"Total clear completed: {entries_removed} entries, "
            f"{pdfs_removed} PDFs ({pdf_size_mb:.1f} MB), "
            f"{summaries_removed} summaries ({summary_size_mb:.1f} MB), "
            f"progress file: {'removed' if progress_removed else 'not found'}, "
            f"BibTeX file: {'removed' if bibtex_removed else 'not found'}"
        )
        
        return {
            "success": True,
            "entries_removed": entries_removed,
            "pdfs_removed": pdfs_removed,
            "pdfs_size_mb": pdf_size_mb,
            "summaries_removed": summaries_removed,
            "summaries_size_mb": summary_size_mb,
            "progress_file_removed": progress_removed,
            "bibtex_file_removed": bibtex_removed,
            "message": (
                f"Total clear: {entries_removed} entries, "
                f"{pdfs_removed} PDFs, {summaries_removed} summaries, "
                f"BibTeX: {'removed' if bibtex_removed else 'not found'}"
            )
        }
    except Exception as e:
        logger.error(f"Failed to clear library: {e}")
        return {
            "success": False,
            "entries_removed": 0,
            "pdfs_removed": 0,
            "pdfs_size_mb": 0.0,
            "summaries_removed": 0,
            "summaries_size_mb": 0.0,
            "progress_file_removed": False,
            "bibtex_file_removed": False,
            "message": f"Error: {e}"
        }

