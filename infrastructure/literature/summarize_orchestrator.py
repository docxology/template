"""Summarization workflow orchestration for literature processing."""
from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.library_index import LibraryEntry
from infrastructure.literature.api import SearchResult

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
        search_result = SearchResult(
            title=entry.title,
            authors=entry.authors or [],
            year=entry.year,
            doi=entry.doi,
            url=entry.url,
            pdf_url=entry.pdf_url,
            abstract=entry.abstract,
            source=entry.source or "library"
        )
        
        papers_needing_summary.append((search_result, pdf_path))
    
    return papers_needing_summary


def get_library_analysis(library_entries: List[LibraryEntry]) -> Dict[str, int]:
    """Analyze library state and return statistics."""
    total_papers = len(library_entries)
    papers_with_pdf = 0
    papers_with_summary = 0
    papers_needing_summary = 0
    
    for entry in library_entries:
        # Check PDF
        pdf_path = None
        if entry.pdf_path:
            pdf_path = Path(entry.pdf_path)
            if not pdf_path.is_absolute():
                pdf_path = Path("literature") / pdf_path
            if pdf_path.exists():
                papers_with_pdf += 1
        else:
            expected_pdf = Path("literature/pdfs") / f"{entry.citation_key}.pdf"
            if expected_pdf.exists():
                papers_with_pdf += 1
                pdf_path = expected_pdf
        
        # Check summary (only if PDF exists)
        if pdf_path and pdf_path.exists():
            summary_path = Path("literature/summaries") / f"{entry.citation_key}_summary.md"
            if summary_path.exists():
                papers_with_summary += 1
            else:
                papers_needing_summary += 1
    
    return {
        'total_papers': total_papers,
        'papers_with_pdf': papers_with_pdf,
        'papers_with_summary': papers_with_summary,
        'papers_needing_summary': papers_needing_summary
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

    print(f"\nLibrary contains {analysis['total_papers']} papers")
    print(f"Papers with PDFs: {analysis['papers_with_pdf']}")
    print(f"Papers with summaries: {analysis['papers_with_summary']}")
    print(f"Papers needing summaries: {analysis['papers_needing_summary']}")

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

