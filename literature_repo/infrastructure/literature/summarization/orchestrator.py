"""Summarization workflow orchestration for literature processing."""
from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.literature.library.index import LibraryEntry
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.summarization.core import SummarizationEngine
from infrastructure.literature.summarization.extractor import TextExtractor

if TYPE_CHECKING:
    from infrastructure.literature.workflow.workflow import LiteratureWorkflow

logger = get_logger(__name__)

MAX_PARALLEL_SUMMARIES = int(os.environ.get("MAX_PARALLEL_SUMMARIES", "1"))


def find_papers_needing_extraction(library_entries: List[LibraryEntry]) -> List[Tuple[SearchResult, Path]]:
    """Find papers that need text extraction (have PDF but no extracted text).
    
    Returns:
        List of tuples (SearchResult, pdf_path) for papers needing extraction.
    """
    extractor = TextExtractor()
    papers_needing_extraction = []
    
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
            expected_pdf = Path("data/pdfs") / f"{entry.citation_key}.pdf"
            if expected_pdf.exists():
                pdf_path = expected_pdf
        
        if not pdf_path or not pdf_path.exists():
            continue
        
        # Check if extracted text already exists
        if extractor.has_extracted_text(entry.citation_key):
            continue
        
        # Convert to search result
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
        
        papers_needing_extraction.append((search_result, pdf_path))
    
    return papers_needing_extraction


def find_papers_needing_summary(library_entries: List[LibraryEntry]) -> List[Tuple[SearchResult, Path]]:
    """Find papers that need summaries (have PDF and extracted text but no summary)."""
    extractor = TextExtractor()
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
            expected_pdf = Path("data/pdfs") / f"{entry.citation_key}.pdf"
            if expected_pdf.exists():
                pdf_path = expected_pdf
        
        if not pdf_path or not pdf_path.exists():
            continue
        
        # Check if extracted text exists (required for summarization)
        if not extractor.has_extracted_text(entry.citation_key):
            logger.debug(
                f"[{entry.citation_key}] Skipping summarization - no extracted text found. "
                f"Run extraction step first."
            )
            continue
        
        # Check if summary exists
        summary_path = Path("data/summaries") / f"{entry.citation_key}_summary.md"
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
    # Scan filesystem for all PDFs, extracted texts, and summaries
    pdfs_dir = Path("data/pdfs")
    extracted_text_dir = Path("data/extracted_text")
    summaries_dir = Path("data/summaries")
    
    # Get all PDF citation keys from filesystem
    pdf_keys_filesystem = set()
    if pdfs_dir.exists():
        for pdf_file in pdfs_dir.glob("*.pdf"):
            citation_key = pdf_file.stem
            pdf_keys_filesystem.add(citation_key)
    
    # Get all extracted text citation keys from filesystem
    extracted_text_keys_filesystem = set()
    if extracted_text_dir.exists():
        for text_file in extracted_text_dir.glob("*.txt"):
            citation_key = text_file.stem
            extracted_text_keys_filesystem.add(citation_key)
    
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
    papers_with_extracted_text = 0
    papers_needing_extraction = 0
    papers_with_summary = 0
    papers_needing_summary = 0
    in_bibliography_no_pdf = 0
    pdf_no_extracted_text = 0
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
            expected_pdf = Path("data/pdfs") / f"{citation_key}.pdf"
            if expected_pdf.exists():
                pdf_path = expected_pdf
        
        has_pdf = pdf_path is not None and pdf_path.exists()
        has_extracted_text = (Path("data/extracted_text") / f"{citation_key}.txt").exists()
        has_summary = (Path("data/summaries") / f"{citation_key}_summary.md").exists()
        
        # Categorize
        if has_pdf:
            papers_with_pdf += 1
            if has_extracted_text:
                papers_with_extracted_text += 1
                if has_summary:
                    papers_with_summary += 1
                    pdf_and_summary += 1
                else:
                    papers_needing_summary += 1
                    pdf_no_summary += 1
            else:
                papers_needing_extraction += 1
                pdf_no_extracted_text += 1
        else:
            if has_summary:
                summary_no_pdf += 1
            else:
                in_bibliography_no_pdf += 1
    
    # Find orphaned files (not in bibliography)
    pdf_not_in_bibliography = len(pdf_keys_filesystem - library_keys)
    extracted_text_not_in_bibliography = len(extracted_text_keys_filesystem - library_keys)
    summary_not_in_bibliography = len(summary_keys_filesystem - library_keys)
    
    # Log comprehensive statistics
    logger.info(f"Filesystem scan: {len(pdf_keys_filesystem)} PDFs, {len(extracted_text_keys_filesystem)} extracted texts, {len(summary_keys_filesystem)} summaries")
    logger.info(f"Bibliography: {total_papers} papers")
    logger.info(f"Matched: {papers_with_pdf} PDFs, {papers_with_extracted_text} extracted texts, {papers_with_summary} summaries")
    logger.info(f"Orphaned: {pdf_not_in_bibliography} PDFs, {extracted_text_not_in_bibliography} extracted texts, {summary_not_in_bibliography} summaries")
    logger.info(f"Categories: {in_bibliography_no_pdf} no PDF, {pdf_no_extracted_text} PDF no extracted text, "
                f"{pdf_no_summary} PDF no summary, {pdf_and_summary} PDF+summary, {summary_no_pdf} summary no PDF")
    
    return {
        'total_papers': total_papers,
        'papers_with_pdf': papers_with_pdf,
        'papers_with_extracted_text': papers_with_extracted_text,
        'papers_needing_extraction': papers_needing_extraction,
        'papers_with_summary': papers_with_summary,
        'papers_needing_summary': papers_needing_summary,
        'in_bibliography_no_pdf': in_bibliography_no_pdf,
        'pdf_no_extracted_text': pdf_no_extracted_text,
        'pdf_no_summary': pdf_no_summary,
        'pdf_and_summary': pdf_and_summary,
        'summary_no_pdf': summary_no_pdf,
        'pdf_not_in_bibliography': pdf_not_in_bibliography,
        'extracted_text_not_in_bibliography': extracted_text_not_in_bibliography,
        'summary_not_in_bibliography': summary_not_in_bibliography,
        'total_pdfs_filesystem': len(pdf_keys_filesystem),
        'total_extracted_texts_filesystem': len(extracted_text_keys_filesystem),
        'total_summaries_filesystem': len(summary_keys_filesystem)
    }


def find_papers_needing_processing(
    library_entries: List[LibraryEntry]
) -> Dict[str, List[LibraryEntry]]:
    """Find papers needing different types of processing."""
    from infrastructure.literature.workflow.orchestrator import find_papers_needing_pdf
    extractor = TextExtractor()
    
    return {
        'need_pdf': find_papers_needing_pdf(library_entries),
        'need_extraction': [e for e in library_entries if e.pdf_path and not extractor.has_extracted_text(e.citation_key)],
        'need_summary': [e for e in library_entries if e.pdf_path and extractor.has_extracted_text(e.citation_key) and not Path(f"data/summaries/{e.citation_key}_summary.md").exists()]
    }


def run_extract_text(workflow: "LiteratureWorkflow") -> int:
    """Extract text from PDFs and save to extracted_text directory.

    Args:
        workflow: Configured LiteratureWorkflow instance.

    Returns:
        Exit code (0=success, 1=failure).
    """
    # Import here to avoid circular dependency
    from infrastructure.literature.workflow.workflow import LiteratureWorkflow
    
    log_header("EXTRACT TEXT FROM PDFs")
    
    # Load library entries
    library_entries = workflow.literature_search.library_index.list_entries()
    
    if not library_entries:
        logger.warning("Library is empty. Use --search-only to find and add papers first.")
        return 0
    
    # Get library analysis
    analysis = get_library_analysis(library_entries)
    
    # Display comprehensive statistics
    log_header("LIBRARY ANALYSIS")
    logger.info(f"\nBibliography:")
    logger.info(f"  Total papers in bibliography: {analysis['total_papers']}")
    logger.info(f"  Papers with PDFs: {analysis['papers_with_pdf']}")
    logger.info(f"  Papers with extracted text: {analysis['papers_with_extracted_text']}")
    logger.info(f"  Papers needing extraction: {analysis['papers_needing_extraction']}")
    
    logger.info(f"\nFilesystem:")
    logger.info(f"  Total PDFs found: {analysis['total_pdfs_filesystem']}")
    logger.info(f"  Total extracted texts found: {analysis['total_extracted_texts_filesystem']}")
    
    logger.info(f"\nCategories:")
    logger.info(f"  In bibliography, no PDF: {analysis['in_bibliography_no_pdf']}")
    logger.info(f"  PDF, no extracted text: {analysis['pdf_no_extracted_text']}")
    logger.info(f"  PDF and extracted text: {analysis['papers_with_extracted_text']}")
    logger.info(f"  Extracted text not in bibliography (orphaned): {analysis['extracted_text_not_in_bibliography']}")
    
    if analysis['papers_needing_extraction'] == 0:
        logger.info("All papers with PDFs already have extracted text. Nothing to do.")
        return 0
    
    # Find papers needing extraction
    papers_needing_extraction = find_papers_needing_extraction(library_entries)
    
    # Extract text
    log_header("EXTRACTING TEXT")
    logger.info(f"Processing {len(papers_needing_extraction)} papers")
    
    extractor = TextExtractor()
    successful = 0
    failed = 0
    skipped = 0
    
    for search_result, pdf_path in papers_needing_extraction:
        citation_key = pdf_path.stem
        extracted_path = Path("data/extracted_text") / f"{citation_key}.txt"
        
        success, error_msg, chars_extracted = extractor.extract_and_save(
            pdf_path=pdf_path,
            citation_key=citation_key,
            use_prioritization=False  # Extract full text, no truncation
        )
        
        if success:
            successful += 1
            # Enhanced success logging with absolute paths and file size
            abs_extracted_path = extracted_path.resolve()
            abs_pdf_path = pdf_path.resolve()
            file_size = abs_extracted_path.stat().st_size if abs_extracted_path.exists() else 0
            logger.info(f"✓ Extracted: {abs_extracted_path} ({file_size:,} bytes) from {abs_pdf_path}")
        elif error_msg and "already exists" in error_msg.lower():
            skipped += 1
            # Log skipped files with paths
            abs_extracted_path = extracted_path.resolve()
            abs_pdf_path = pdf_path.resolve()
            file_size = abs_extracted_path.stat().st_size if abs_extracted_path.exists() else 0
            logger.info(f"⊘ Skipped (already exists): {abs_extracted_path} ({file_size:,} bytes)")
        else:
            failed += 1
            # Enhanced failure logging with full context
            abs_pdf_path = pdf_path.resolve()
            abs_extracted_path = extracted_path.resolve()
            logger.error(f"✗ Extraction failed: {citation_key}")
            logger.error(f"  PDF source: {abs_pdf_path}")
            logger.error(f"  Expected output: {abs_extracted_path}")
            logger.error(f"  Error: {error_msg}")
    
    # Display summary
    log_header("EXTRACTION COMPLETED")
    logger.info(f"Papers processed: {len(papers_needing_extraction)}")
    logger.info(f"Texts extracted: {successful}")
    if skipped > 0:
        logger.info(f"Texts skipped (already exist): {skipped}")
    logger.info(f"Extraction failures: {failed}")
    if len(papers_needing_extraction) > 0:
        logger.info(f"Success rate: {(successful / len(papers_needing_extraction)) * 100:.1f}%")
    
    log_success("Text extraction complete!")
    return 0 if failed == 0 else 1


def run_summarize(workflow: "LiteratureWorkflow") -> int:
    """Generate summaries for papers with PDFs (no downloading).

    Args:
        workflow: Configured LiteratureWorkflow instance.

    Returns:
        Exit code (0=success, 1=failure).
    """
    # Import here to avoid circular dependency
    from infrastructure.literature.workflow.workflow import LiteratureWorkflow
    
    log_header("GENERATE SUMMARIES (FOR PAPERS WITH PDFs)")

    # Load library entries
    library_entries = workflow.literature_search.library_index.list_entries()

    if not library_entries:
        logger.warning("Library is empty. Use --search-only to find and add papers first.")
        logger.warning("Library is empty. Use --search-only to find and add papers first.")
        return 0

    # Get library analysis
    analysis = get_library_analysis(library_entries)

    # Display comprehensive statistics
    log_header("LIBRARY ANALYSIS")
    logger.info(f"\nBibliography:")
    logger.info(f"  Total papers in bibliography: {analysis['total_papers']}")
    logger.info(f"  Papers with PDFs: {analysis['papers_with_pdf']}")
    logger.info(f"  Papers with summaries: {analysis['papers_with_summary']}")
    logger.info(f"  Papers needing summaries: {analysis['papers_needing_summary']}")

    logger.info(f"\nFilesystem:")
    logger.info(f"  Total PDFs found: {analysis['total_pdfs_filesystem']}")
    logger.info(f"  Total extracted texts found: {analysis['total_extracted_texts_filesystem']}")
    logger.info(f"  Total summaries found: {analysis['total_summaries_filesystem']}")
    
    logger.info(f"\nCategories:")
    logger.info(f"  In bibliography, no PDF: {analysis['in_bibliography_no_pdf']}")
    logger.info(f"  PDF, no extracted text: {analysis['pdf_no_extracted_text']}")
    logger.info(f"  PDF, no summary: {analysis['pdf_no_summary']}")
    logger.info(f"  PDF and summary: {analysis['pdf_and_summary']}")
    logger.info(f"  Summary, no PDF: {analysis['summary_no_pdf']}")
    logger.info(f"  PDF not in bibliography (orphaned): {analysis['pdf_not_in_bibliography']}")
    logger.info(f"  Extracted text not in bibliography (orphaned): {analysis['extracted_text_not_in_bibliography']}")
    logger.info(f"  Summary not in bibliography (orphaned): {analysis['summary_not_in_bibliography']}")

    if analysis['papers_needing_summary'] == 0:
        logger.info("All papers with PDFs already have summaries. Nothing to do.")
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

    # Summarize papers (progress callback is integrated in workflow._summarize_papers_parallel)
    # Real-time progress updates will be displayed during summarization showing:
    # - Paper number and title
    # - PDF extraction progress
    # - Context extraction progress
    # - Draft generation progress
    # - Validation progress
    # - Refinement progress (if needed)
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

    log_header("SUMMARIZATION COMPLETED")
    logger.info(f"Papers processed: {len(papers_needing_summary)}")
    logger.info(f"Summaries generated: {successful}")
    if skipped > 0:
        logger.info(f"Summaries skipped (already exist): {skipped}")
    logger.info(f"Summary failures: {failed}")
    logger.info(f"Success rate: {(successful / len(papers_needing_summary)) * 100:.1f}%")

    log_success("Summary generation complete!")
    return 0


