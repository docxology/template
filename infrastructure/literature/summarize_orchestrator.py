"""Summarization workflow orchestration for literature processing."""
from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.library_index import LibraryEntry
from infrastructure.literature.sources import SearchResult

logger = get_logger(__name__)

MAX_PARALLEL_SUMMARIES = int(os.environ.get("MAX_PARALLEL_SUMMARIES", "1"))


def find_papers_needing_summary(library_entries: List[LibraryEntry]) -> List[Tuple[SearchResult, Path]]:
    """Find papers that need summaries (have PDF but no summary)."""
    papers_needing_summary = []
    
    for entry in library_entries:
        # Check if PDF exists
        pdf_path = None
        if entry.pdf_path:
            pdf_path = Path(entry.pdf_path)
            if not pdf_path.is_absolute():
                pdf_path = Path("literature") / pdf_path
            if not pdf_path.exists():
                pdf_path = None
        
        # Check expected location
        if not pdf_path:
            expected_pdf = Path("literature/pdfs") / f"{entry.citation_key}.pdf"
            if expected_pdf.exists():
                pdf_path = expected_pdf
        
        if not pdf_path or not pdf_path.exists():
            continue
        
        # Check if summary exists
        summary_path = Path("literature/summaries") / f"{entry.citation_key}_summary.md"
        if summary_path.exists():
            continue
        
        # Convert to search result
        # LibraryEntry doesn't have pdf_url, but we have the PDF file path
        # Extract pdf_url from metadata if available, otherwise use None
        pdf_url = entry.metadata.get("pdf_url") if entry.metadata else None
        
        search_result = SearchResult(
            title=entry.title,
            authors=entry.authors or [],
            year=entry.year,
            doi=entry.doi,
            url=entry.url,
            pdf_url=pdf_url,
            abstract=entry.abstract,
            source=entry.source or "library"
        )
        
        papers_needing_summary.append((search_result, pdf_path))
    
    return papers_needing_summary


def get_library_analysis(library_entries: List[LibraryEntry]) -> Dict[str, int]:
    """Analyze library state and return comprehensive statistics.
    
    Scans filesystem for PDFs and summaries, matches them with library entries,
    and categorizes all papers into detailed categories.
    
    Returns:
        Dictionary with comprehensive statistics including:
        - total_papers: Papers in bibliography
        - papers_with_pdf: Papers in bibliography with PDF
        - papers_with_summary: Papers in bibliography with summary
        - papers_needing_summary: Papers in bibliography with PDF but no summary
        - in_bibliography_no_pdf: Papers in bibliography but no PDF file
        - pdf_no_summary: PDF exists but no summary (in bibliography)
        - pdf_and_summary: Both PDF and summary exist (in bibliography)
        - summary_no_pdf: Summary exists but no PDF (in bibliography)
        - pdf_not_in_bibliography: PDF exists but not in library index (orphaned)
        - summary_not_in_bibliography: Summary exists but not in library index (orphaned)
        - total_pdfs_filesystem: Total PDFs found in filesystem
        - total_summaries_filesystem: Total summaries found in filesystem
    """
    # Scan filesystem for all PDFs and summaries
    pdfs_dir = Path("literature/pdfs")
    summaries_dir = Path("literature/summaries")
    
    # Get all PDF citation keys from filesystem
    pdf_keys_filesystem = set()
    if pdfs_dir.exists():
        for pdf_file in pdfs_dir.glob("*.pdf"):
            citation_key = pdf_file.stem
            pdf_keys_filesystem.add(citation_key)
    
    # Get all summary citation keys from filesystem
    summary_keys_filesystem = set()
    if summaries_dir.exists():
        for summary_file in summaries_dir.glob("*_summary.md"):
            citation_key = summary_file.stem.replace("_summary", "")
            summary_keys_filesystem.add(citation_key)
    
    # Create set of library entry citation keys
    library_keys = {entry.citation_key for entry in library_entries}
    
    # Initialize counters
    total_papers = len(library_entries)
    papers_with_pdf = 0
    papers_with_summary = 0
    papers_needing_summary = 0
    in_bibliography_no_pdf = 0
    pdf_no_summary = 0
    pdf_and_summary = 0
    summary_no_pdf = 0
    
    # Analyze library entries
    for entry in library_entries:
        citation_key = entry.citation_key
        
        # Check PDF
        pdf_path = None
        if entry.pdf_path:
            pdf_path = Path(entry.pdf_path)
            if not pdf_path.is_absolute():
                pdf_path = Path("literature") / pdf_path
            if not pdf_path.exists():
                pdf_path = None
        
        # Check expected location
        if not pdf_path:
            expected_pdf = Path("literature/pdfs") / f"{citation_key}.pdf"
            if expected_pdf.exists():
                pdf_path = expected_pdf
        
        has_pdf = pdf_path is not None and pdf_path.exists()
        has_summary = (Path("literature/summaries") / f"{citation_key}_summary.md").exists()
        
        # Categorize
        if has_pdf:
            papers_with_pdf += 1
            if has_summary:
                papers_with_summary += 1
                pdf_and_summary += 1
            else:
                papers_needing_summary += 1
                pdf_no_summary += 1
        else:
            if has_summary:
                summary_no_pdf += 1
            else:
                in_bibliography_no_pdf += 1
    
    # Find orphaned files (not in bibliography)
    pdf_not_in_bibliography = len(pdf_keys_filesystem - library_keys)
    summary_not_in_bibliography = len(summary_keys_filesystem - library_keys)
    
    # Log comprehensive statistics
    logger.info(f"Filesystem scan: {len(pdf_keys_filesystem)} PDFs, {len(summary_keys_filesystem)} summaries")
    logger.info(f"Bibliography: {total_papers} papers")
    logger.info(f"Matched: {papers_with_pdf} PDFs, {papers_with_summary} summaries")
    logger.info(f"Orphaned: {pdf_not_in_bibliography} PDFs, {summary_not_in_bibliography} summaries")
    logger.info(f"Categories: {in_bibliography_no_pdf} no PDF, {pdf_no_summary} PDF no summary, "
                f"{pdf_and_summary} PDF+summary, {summary_no_pdf} summary no PDF")
    
    return {
        'total_papers': total_papers,
        'papers_with_pdf': papers_with_pdf,
        'papers_with_summary': papers_with_summary,
        'papers_needing_summary': papers_needing_summary,
        'in_bibliography_no_pdf': in_bibliography_no_pdf,
        'pdf_no_summary': pdf_no_summary,
        'pdf_and_summary': pdf_and_summary,
        'summary_no_pdf': summary_no_pdf,
        'pdf_not_in_bibliography': pdf_not_in_bibliography,
        'summary_not_in_bibliography': summary_not_in_bibliography,
        'total_pdfs_filesystem': len(pdf_keys_filesystem),
        'total_summaries_filesystem': len(summary_keys_filesystem)
    }


def find_papers_needing_processing(
    library_entries: List[LibraryEntry]
) -> Dict[str, List[LibraryEntry]]:
    """Find papers needing different types of processing."""
    from infrastructure.literature.search_orchestrator import find_papers_needing_pdf
    
    return {
        'need_pdf': find_papers_needing_pdf(library_entries),
        'need_summary': [e for e in library_entries if e.pdf_path and not Path(f"literature/summaries/{e.citation_key}_summary.md").exists()]
    }


def run_summarize(workflow: LiteratureWorkflow) -> int:
    """Generate summaries for papers with PDFs (no downloading).

    Args:
        workflow: Configured LiteratureWorkflow instance.

    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("GENERATE SUMMARIES (FOR PAPERS WITH PDFs)")

    # Load library entries
    library_entries = workflow.literature_search.library_index.list_entries()

    if not library_entries:
        logger.warning("Library is empty. Use --search-only to find and add papers first.")
        print("\nLibrary is empty. Use --search-only to find and add papers first.")
        return 0

    # Get library analysis
    analysis = get_library_analysis(library_entries)

    # Display comprehensive statistics
    print(f"\n{'=' * 60}")
    print("LIBRARY ANALYSIS")
    print("=" * 60)
    print(f"\nBibliography:")
    print(f"  Total papers in bibliography: {analysis['total_papers']}")
    print(f"  Papers with PDFs: {analysis['papers_with_pdf']}")
    print(f"  Papers with summaries: {analysis['papers_with_summary']}")
    print(f"  Papers needing summaries: {analysis['papers_needing_summary']}")
    
    print(f"\nFilesystem:")
    print(f"  Total PDFs found: {analysis['total_pdfs_filesystem']}")
    print(f"  Total summaries found: {analysis['total_summaries_filesystem']}")
    
    print(f"\nCategories:")
    print(f"  In bibliography, no PDF: {analysis['in_bibliography_no_pdf']}")
    print(f"  PDF, no summary: {analysis['pdf_no_summary']}")
    print(f"  PDF and summary: {analysis['pdf_and_summary']}")
    print(f"  Summary, no PDF: {analysis['summary_no_pdf']}")
    print(f"  PDF not in bibliography (orphaned): {analysis['pdf_not_in_bibliography']}")
    print(f"  Summary not in bibliography (orphaned): {analysis['summary_not_in_bibliography']}")
    print("=" * 60)

    if analysis['papers_needing_summary'] == 0:
        print("\nAll papers with PDFs already have summaries. Nothing to do.")
        return 0

    # Find papers needing summaries
    papers_needing_summary = find_papers_needing_summary(library_entries)

    # Generate summaries
    log_header("GENERATING SUMMARIES")
    logger.info(f"Processing {len(papers_needing_summary)} papers")

    # Initialize progress tracking
    if not workflow.progress_tracker.current_progress:
        workflow.progress_tracker.start_new_run([], len(papers_needing_summary))

    for search_result, pdf_path in papers_needing_summary:
        citation_key = pdf_path.stem
        workflow.progress_tracker.add_paper(citation_key, str(pdf_path))
        workflow.progress_tracker.update_entry_status(citation_key, "downloaded")

    # Summarize papers
    summarization_results = workflow._summarize_papers_parallel(
        papers_needing_summary, MAX_PARALLEL_SUMMARIES
    )

    # Save progress
    if workflow.progress_tracker:
        workflow.progress_tracker.save_progress()

    # Display summary
    successful = sum(1 for r in summarization_results if r.success and not getattr(r, 'skipped', False))
    failed = sum(1 for r in summarization_results if not r.success)
    skipped = sum(1 for r in summarization_results if getattr(r, 'skipped', False))

    print(f"\n{'=' * 60}")
    print("SUMMARIZATION COMPLETED")
    print("=" * 60)
    print(f"Papers processed: {len(papers_needing_summary)}")
    print(f"Summaries generated: {successful}")
    if skipped > 0:
        print(f"Summaries skipped (already exist): {skipped}")
    print(f"Summary failures: {failed}")
    print(f"Success rate: {(successful / len(papers_needing_summary)) * 100:.1f}%")

    log_success("Summary generation complete!")
    return 0


