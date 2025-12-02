#!/usr/bin/env python3
"""Literature Search and Summarization orchestrator script.

This thin orchestrator coordinates literature processing workflows:
1. Search mode: Search for papers with configurable keywords and limits
2. Summarize mode: Generate summaries for existing PDFs in library

All business logic is implemented in infrastructure/literature/ modules.

Usage:
    # Search for papers (interactive keyword input)
    python3 scripts/07_literature_search.py --search
    
    # Search with specific keywords
    python3 scripts/07_literature_search.py --search --keywords "machine learning,deep learning"
    
    # Search with custom limit per keyword
    python3 scripts/07_literature_search.py --search --limit 50 --keywords "optimization"
    
    # Generate summaries for existing PDFs
    python3 scripts/07_literature_search.py --summarize
    
    # Both operations (search then summarize)
    python3 scripts/07_literature_search.py --search --summarize

Output Structure:
    literature/
    ├── references.bib        # BibTeX entries
    ├── library.json          # JSON index
    ├── summarization_progress.json  # Progress tracking
    ├── pdfs/                 # Downloaded PDFs
    ├── summaries/            # AI-generated summaries
    │   └── {citation_key}_summary.md
    └── failed_downloads.json # Failed downloads (if any)

Environment Variables:
    LITERATURE_DEFAULT_LIMIT: Results per source per keyword (default: 25)
    MAX_PARALLEL_SUMMARIES: Parallel summarization workers (default: 1)
    LLM_SUMMARIZATION_TIMEOUT: Timeout for paper summarization (default: 600)
    LOG_LEVEL: Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)

Stage 7 of the pipeline orchestration - literature management.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.literature import LiteratureSearch, LiteratureConfig
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.progress import ProgressTracker
from infrastructure.literature.summarizer import PaperSummarizer, SummaryQualityValidator
from infrastructure.literature.api import SearchResult
from infrastructure.literature.library_index import LibraryEntry
from infrastructure.llm import (
    LLMClient,
    LLMConfig,
    is_ollama_running,
    select_best_model,
)

# Output paths
PROGRESS_FILE = Path("literature/summarization_progress.json")
SUMMARIES_DIR = Path("literature/summaries")

logger = get_logger(__name__)

# Default configuration
DEFAULT_LIMIT_PER_KEYWORD = int(os.environ.get("LITERATURE_DEFAULT_LIMIT", "25"))
MAX_PARALLEL_SUMMARIES = int(os.environ.get("MAX_PARALLEL_SUMMARIES", "1"))


def setup_infrastructure() -> Optional[LiteratureWorkflow]:
    """Set up all infrastructure components for literature processing.

    Returns:
        Configured LiteratureWorkflow instance, or None if setup fails.
    """
    # Check Ollama availability
    log_header("Checking LLM Availability")
    if not is_ollama_running():
        logger.error("Ollama is not running. Please start Ollama first:")
        logger.error("  $ ollama serve")
        return None

    # Select best model
    try:
        model = select_best_model()
        logger.info(f"Using model: {model}")
    except Exception as e:
        logger.error(f"No suitable model found: {e}")
        return None

    # Initialize literature search
    lit_config = LiteratureConfig.from_env()
    logger.info(f"Search limit: {lit_config.default_limit} results per source per keyword")

    # Log Unpaywall status
    if lit_config.use_unpaywall:
        if lit_config.unpaywall_email and lit_config.unpaywall_email != "research@4dresearch.com":
            logger.info(f"Unpaywall enabled with email: {lit_config.unpaywall_email}")
        else:
            logger.info("Unpaywall enabled with default email")

    literature_search = LiteratureSearch(lit_config)

    # Initialize LLM client with extended timeout for paper summarization
    llm_config = LLMConfig.from_env()
    llm_config.default_model = model
    llm_config.timeout = float(os.environ.get("LLM_SUMMARIZATION_TIMEOUT", "600"))

    system_prompt = (
        "You are an expert research paper analyst specializing in scientific literature. "
        "Your task is to provide accurate, evidence-based summaries of academic papers. "
        "You must ONLY use information explicitly stated in the provided paper text. "
        "Never add external knowledge, assumptions, or invented details. "
        "Focus on concrete methods, measurements, and findings mentioned in the paper. "
        "Maintain scientific accuracy and avoid speculation."
    )
    llm_config.system_prompt = system_prompt

    llm_client = LLMClient(llm_config)

    # Initialize summarizer
    quality_validator = SummaryQualityValidator()
    summarizer = PaperSummarizer(llm_client, quality_validator)

    # Initialize progress tracker
    progress_tracker = ProgressTracker(PROGRESS_FILE)

    # Create workflow orchestrator
    workflow = LiteratureWorkflow(literature_search)
    workflow.set_summarizer(summarizer)
    workflow.set_progress_tracker(progress_tracker)

    return workflow


def get_keywords_input() -> List[str]:
    """Prompt user for comma-separated keywords.
    
    Returns:
        List of cleaned keyword strings.
    """
    print("\nEnter search keywords (comma-separated):")
    user_input = input("> ").strip()
    
    if not user_input:
        logger.warning("No keywords provided")
        return []
    
    keywords = [kw.strip() for kw in user_input.split(",") if kw.strip()]
    logger.info(f"Parsed {len(keywords)} keyword(s): {keywords}")
    return keywords


def get_limit_input(default: int = DEFAULT_LIMIT_PER_KEYWORD) -> int:
    """Prompt user for paper limit per keyword.
    
    Args:
        default: Default limit value.
        
    Returns:
        Integer limit value.
    """
    print(f"\nHow many papers per keyword? [{default}]:")
    user_input = input("> ").strip()
    
    if not user_input:
        return default
    
    try:
        limit = int(user_input)
        if limit > 0:
            return limit
        print("Limit must be a positive integer. Using default.")
        return default
    except ValueError:
        print("Invalid number. Using default.")
        return default


def library_entry_to_search_result(entry: LibraryEntry) -> SearchResult:
    """Convert LibraryEntry to SearchResult for processing.
    
    Args:
        entry: Library entry to convert.
        
    Returns:
        SearchResult object.
    """
    return SearchResult(
        title=entry.title,
        authors=entry.authors,
        year=entry.year,
        abstract=entry.abstract or "",
        url=entry.url or "",
        doi=entry.doi,
        source=entry.source,
        pdf_url=entry.metadata.get("pdf_url"),
        venue=entry.venue,
        citation_count=entry.citation_count
    )


def find_papers_needing_processing(
    library_entries: List[LibraryEntry]
) -> Tuple[List[LibraryEntry], List[Tuple[LibraryEntry, Path]]]:
    """Analyze library and find papers needing processing.
    
    Args:
        library_entries: List of all library entries.
        
    Returns:
        Tuple of (papers_needing_pdf, papers_needing_summary).
    """
    papers_needing_pdf = []
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
        
        # If no PDF path in entry, check if PDF exists in expected location
        if not pdf_path:
            expected_pdf = Path("literature/pdfs") / f"{entry.citation_key}.pdf"
            if expected_pdf.exists():
                pdf_path = expected_pdf
        
        # Check if summary exists
        summary_path = Path("literature/summaries") / f"{entry.citation_key}_summary.md"
        has_summary = summary_path.exists()
        
        if not pdf_path or not pdf_path.exists():
            papers_needing_pdf.append(entry)
        elif pdf_path.exists() and not has_summary:
            papers_needing_summary.append((entry, pdf_path))
    
    return papers_needing_pdf, papers_needing_summary


def run_search(
    workflow: LiteratureWorkflow,
    keywords: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> int:
    """Execute literature search workflow.
    
    Args:
        workflow: Configured LiteratureWorkflow instance.
        keywords: Optional keywords list (prompts if not provided).
        limit: Optional limit per keyword (prompts if not provided).
        
    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("Literature Search and PDF Download")
    
    print("\nThis will:")
    print("  1. Search arXiv and Semantic Scholar for papers")
    print("  2. Download PDFs and add to BibTeX library")
    print("  3. Generate AI summaries for each paper")
    print(f"  4. Process up to {MAX_PARALLEL_SUMMARIES} papers in parallel")
    print()
    
    # Get limit if not provided
    if limit is None:
        limit = get_limit_input()
    
    # Get keywords if not provided
    if keywords is None:
        keywords = get_keywords_input()
        if not keywords:
            logger.info("No keywords provided. Exiting.")
            return 1
    
    # Execute search and summarization
    log_header("Executing Literature Search")
    logger.info(f"Search keywords: {', '.join(keywords)}")
    logger.info(f"Results per keyword: {limit}")
    logger.info(f"Max parallel summaries: {MAX_PARALLEL_SUMMARIES}")
    
    try:
        result = workflow.execute_search_and_summarize(
            keywords=keywords,
            limit_per_keyword=limit,
            max_parallel_summaries=MAX_PARALLEL_SUMMARIES,
            resume_existing=True,
            interactive=True
        )
        
        # Display results
        stats = workflow.get_workflow_stats(result)
        
        print(f"\n{'=' * 60}")
        print("SEARCH COMPLETED")
        print("=" * 60)
        print(f"Keywords searched: {', '.join(keywords)}")
        print(f"Papers found: {stats['search']['papers_found']}")
        print(f"Papers already downloaded: {result.papers_already_existed}")
        print(f"Papers newly downloaded: {result.papers_newly_downloaded}")
        print(f"Download failures: {result.papers_failed_download}")
        print(f"Papers summarized: {stats['summarization']['successful']}")
        if result.summaries_skipped > 0:
            print(f"Summaries skipped (already exist): {result.summaries_skipped}")
        print(f"Summary failures: {result.summaries_failed}")
        print(f"Success rate: {result.success_rate:.1f}%")
        
        display_file_locations()
        
        log_success("Literature search complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_summarize(workflow: LiteratureWorkflow) -> int:
    """Generate summaries for existing PDFs in library.
    
    Args:
        workflow: Configured LiteratureWorkflow instance.
        
    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("Generate Summaries for Downloaded PDFs")
    
    # Load library entries
    library_entries = workflow.literature_search.library_index.list_entries()
    
    if not library_entries:
        logger.warning("Library is empty. No papers to summarize.")
        print("\nLibrary is empty. Use --search to find and download papers first.")
        return 0
    
    logger.info(f"Found {len(library_entries)} papers in library")
    
    # Find papers needing processing
    papers_needing_pdf, papers_needing_summary = find_papers_needing_processing(library_entries)
    
    print("\nLibrary Analysis:")
    print(f"  Total papers in library: {len(library_entries)}")
    print(f"  Papers needing PDF download: {len(papers_needing_pdf)}")
    print(f"  Papers needing summaries: {len(papers_needing_summary)}")
    
    if not papers_needing_pdf and not papers_needing_summary:
        print("\nAll papers in library have PDFs and summaries. Nothing to do.")
        return 0
    
    # Process papers needing PDFs
    downloaded_papers = []
    if papers_needing_pdf:
        log_header("Downloading Missing PDFs")
        print(f"Attempting to download {len(papers_needing_pdf)} missing PDFs...")
        
        for i, entry in enumerate(papers_needing_pdf, 1):
            logger.info(f"[{i}/{len(papers_needing_pdf)}] {entry.title[:60]}...")
            
            search_result = library_entry_to_search_result(entry)
            download_result = workflow.literature_search.download_paper_with_result(search_result)
            
            if download_result.success and download_result.pdf_path:
                logger.info(f"Downloaded: {download_result.pdf_path.name}")
                downloaded_papers.append((search_result, download_result.pdf_path))
            else:
                logger.warning(f"Failed to download PDF for: {entry.title[:50]}...")
    
    # Combine downloaded papers with papers needing summaries
    papers_to_summarize = []
    papers_to_summarize.extend(downloaded_papers)
    
    for entry, pdf_path in papers_needing_summary:
        search_result = library_entry_to_search_result(entry)
        papers_to_summarize.append((search_result, pdf_path))
    
    if not papers_to_summarize:
        print("\nNo papers need summarization.")
        return 0
    
    # Generate summaries
    log_header("Generating Summaries")
    logger.info(f"Processing {len(papers_to_summarize)} papers")
    
    # Initialize progress tracking
    if not workflow.progress_tracker.current_progress:
        workflow.progress_tracker.start_new_run([], len(papers_to_summarize))
    
    for search_result, pdf_path in papers_to_summarize:
        citation_key = pdf_path.stem
        workflow.progress_tracker.add_paper(citation_key, str(pdf_path))
        workflow.progress_tracker.update_entry_status(citation_key, "downloaded")
    
    # Summarize papers
    summarization_results = workflow._summarize_papers_parallel(
        papers_to_summarize, MAX_PARALLEL_SUMMARIES
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
    print(f"Papers processed: {len(papers_to_summarize)}")
    print(f"PDFs downloaded: {len(downloaded_papers)}")
    print(f"Summaries generated: {successful}")
    if skipped > 0:
        print(f"Summaries skipped (already exist): {skipped}")
    print(f"Summary failures: {failed}")
    
    display_file_locations()
    
    log_success("Summary generation complete!")
    return 0


def display_file_locations() -> None:
    """Display file location summary."""
    print("\nOutput files:")
    print("- literature/references.bib (BibTeX references)")
    
    try:
        with open("literature/library.json", "r") as f:
            library_data = json.load(f)
            entry_count = library_data.get("count", 0)
        print(f"- literature/library.json (JSON index with {entry_count} papers)")
    except Exception:
        print("- literature/library.json (JSON index)")
    
    try:
        pdf_count = len(list(Path("literature/pdfs").glob("*.pdf")))
        pdf_dir = Path("literature/pdfs")
        total_pdf_size = sum(f.stat().st_size for f in pdf_dir.glob("*.pdf") if f.is_file())
        print(f"- literature/pdfs/ ({pdf_count} PDFs, {total_pdf_size:,} bytes total)")
    except Exception:
        print("- literature/pdfs/ (downloaded PDFs)")
    
    try:
        summary_count = len(list(Path("literature/summaries").glob("*.md")))
        summary_dir = Path("literature/summaries")
        total_summary_size = sum(f.stat().st_size for f in summary_dir.glob("*.md") if f.is_file())
        print(f"- literature/summaries/ ({summary_count} summaries, {total_summary_size:,} bytes total)")
    except Exception:
        print("- literature/summaries/ (AI-generated summaries)")
    
    print("- literature/summarization_progress.json (progress tracking)")


def main() -> int:
    """Main entry point for literature search and summarization.
    
    Returns:
        Exit code (0=success, 1=failure, 2=skipped).
    """
    parser = argparse.ArgumentParser(
        description="Literature search and summarization tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/07_literature_search.py --search
  python3 scripts/07_literature_search.py --search --keywords "machine learning,optimization"
  python3 scripts/07_literature_search.py --search --limit 50 --keywords "AI"
  python3 scripts/07_literature_search.py --summarize
  python3 scripts/07_literature_search.py --search --summarize
"""
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Search for papers and download PDFs"
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate summaries for existing PDFs"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        help="Comma-separated keywords for search (prompts if not provided)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=f"Papers per keyword (default: {DEFAULT_LIMIT_PER_KEYWORD})"
    )
    
    args = parser.parse_args()
    
    # Require at least one action
    if not args.search and not args.summarize:
        parser.print_help()
        print("\nError: Must specify --search and/or --summarize")
        return 1
    
    # Parse keywords if provided
    keywords = None
    if args.keywords:
        keywords = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]
        if not keywords:
            logger.error("No valid keywords provided")
            return 1
    
    try:
        # Set up infrastructure
        log_header("Setting up Literature Processing Infrastructure")
        workflow = setup_infrastructure()
        
        if workflow is None:
            logger.error("Failed to initialize infrastructure")
            return 2  # Skip code - Ollama not available
        
        exit_code = 0
        
        # Run search if requested
        if args.search:
            exit_code = run_search(workflow, keywords=keywords, limit=args.limit)
            if exit_code != 0:
                return exit_code
        
        # Run summarize if requested
        if args.summarize:
            exit_code = run_summarize(workflow)
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        return 1
    except Exception as e:
        logger.error(f"Error during literature processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

