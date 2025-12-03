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
from infrastructure.literature.paper_selector import PaperSelector
from infrastructure.literature.llm_operations import LiteratureLLMOperations
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


def get_pdf_path_for_entry(entry: LibraryEntry) -> Optional[Path]:
    """Get the PDF path for a library entry, checking both metadata and filesystem.

    Args:
        entry: Library entry to check.

    Returns:
        Path to PDF if it exists, None otherwise.
    """
    # Check if PDF path in entry metadata
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

    return pdf_path


def find_papers_needing_pdf(library_entries: List[LibraryEntry]) -> List[LibraryEntry]:
    """Find papers that need PDF download.

    Args:
        library_entries: List of all library entries.

    Returns:
        List of entries that need PDF download.
    """
    papers_needing_pdf = []

    for entry in library_entries:
        pdf_path = get_pdf_path_for_entry(entry)
        if not pdf_path or not pdf_path.exists():
            papers_needing_pdf.append(entry)

    return papers_needing_pdf


def find_papers_needing_summary(library_entries: List[LibraryEntry]) -> List[Tuple[LibraryEntry, Path]]:
    """Find papers that have PDFs but need summaries.

    Args:
        library_entries: List of all library entries.

    Returns:
        List of (entry, pdf_path) tuples for papers needing summaries.
    """
    papers_needing_summary = []

    for entry in library_entries:
        pdf_path = get_pdf_path_for_entry(entry)

        # Only consider papers that have PDFs
        if pdf_path and pdf_path.exists():
            # Check if summary exists
            summary_path = Path("literature/summaries") / f"{entry.citation_key}_summary.md"
            if not summary_path.exists():
                papers_needing_summary.append((entry, pdf_path))

    return papers_needing_summary


def get_library_analysis(library_entries: List[LibraryEntry]) -> Dict[str, int]:
    """Analyze the current state of the library.

    Args:
        library_entries: List of all library entries.

    Returns:
        Dictionary with analysis statistics.
    """
    total_papers = len(library_entries)
    papers_with_pdf = 0
    papers_with_summary = 0
    papers_complete = 0  # Have both PDF and summary

    for entry in library_entries:
        pdf_path = get_pdf_path_for_entry(entry)
        has_pdf = pdf_path is not None and pdf_path.exists()

        summary_path = Path("literature/summaries") / f"{entry.citation_key}_summary.md"
        has_summary = summary_path.exists()

        if has_pdf:
            papers_with_pdf += 1
        if has_summary:
            papers_with_summary += 1
        if has_pdf and has_summary:
            papers_complete += 1

    return {
        "total_papers": total_papers,
        "papers_with_pdf": papers_with_pdf,
        "papers_with_summary": papers_with_summary,
        "papers_complete": papers_complete,
        "papers_needing_pdf": total_papers - papers_with_pdf,
        "papers_needing_summary": papers_with_pdf - papers_complete,
    }


def find_papers_needing_processing(
    library_entries: List[LibraryEntry]
) -> Tuple[List[LibraryEntry], List[Tuple[LibraryEntry, Path]]]:
    """Analyze library and find papers needing processing.

    Args:
        library_entries: List of all library entries.

    Returns:
        Tuple of (papers_needing_pdf, papers_needing_summary).
    """
    papers_needing_pdf = find_papers_needing_pdf(library_entries)
    papers_needing_summary = find_papers_needing_summary(library_entries)

    return papers_needing_pdf, papers_needing_summary


def run_search_only(
    workflow: LiteratureWorkflow,
    keywords: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> int:
    """Execute literature search only (add to bibliography).

    Args:
        workflow: Configured LiteratureWorkflow instance.
        keywords: Optional keywords list (prompts if not provided).
        limit: Optional limit per keyword (prompts if not provided).

    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("LITERATURE SEARCH (ADD TO BIBLIOGRAPHY)")

    print("\nThis will:")
    print("  1. Search arXiv and Semantic Scholar for papers")
    print("  2. Add papers to bibliography (no download or summarization)")
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

    # Execute search only
    log_header("SEARCHING FOR PAPERS")
    logger.info(f"Search keywords: {', '.join(keywords)}")
    logger.info(f"Results per keyword: {limit}")

    try:
        # Search for papers
        search_results = workflow._search_papers(keywords, limit)
        papers_found = len(search_results)

        if not search_results:
            logger.warning("No papers found for the given keywords")
            return 1

        # Add all results to library
        log_header("ADDING TO BIBLIOGRAPHY")
        added_count = 0
        already_existed_count = 0

        for result in search_results:
            try:
                citation_key = workflow.literature_search.add_to_library(result)
                added_count += 1
                logger.info(f"Added: {citation_key}")
            except Exception as e:
                already_existed_count += 1
                logger.debug(f"Already exists: {result.title[:50]}...")

        # Display results
        print(f"\n{'=' * 60}")
        print("SEARCH COMPLETED")
        print("=" * 60)
        print(f"Keywords searched: {', '.join(keywords)}")
        print(f"Papers found: {papers_found}")
        print(f"Papers added to bibliography: {added_count}")
        if already_existed_count > 0:
            print(f"Papers already in bibliography: {already_existed_count}")
        print(f"Success rate: {(added_count / papers_found) * 100:.1f}%")

        display_file_locations()

        log_success("Literature search complete!")
        return 0

    except Exception as e:
        logger.error(f"Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_download_only(workflow: LiteratureWorkflow) -> int:
    """Download PDFs for existing bibliography entries.

    Args:
        workflow: Configured LiteratureWorkflow instance.

    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("DOWNLOAD PDFs (FOR BIBLIOGRAPHY ENTRIES)")

    # Load library entries
    library_entries = workflow.literature_search.library_index.list_entries()

    if not library_entries:
        logger.warning("Library is empty. Use --search-only to find and add papers first.")
        print("\nLibrary is empty. Use --search-only to find and add papers first.")
        return 0

    # Find entries needing PDFs
    papers_needing_pdf = []
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

        if not pdf_path or not pdf_path.exists():
            papers_needing_pdf.append(entry)

    print(f"\nLibrary contains {len(library_entries)} papers")
    print(f"Papers needing PDF download: {len(papers_needing_pdf)}")

    if not papers_needing_pdf:
        print("\nAll papers in bibliography already have PDFs. Nothing to download.")
        return 0

    # Download PDFs
    log_header("DOWNLOADING PDFs")
    print(f"Attempting to download {len(papers_needing_pdf)} PDFs...")

    downloaded_count = 0
    failed_count = 0

    for i, entry in enumerate(papers_needing_pdf, 1):
        logger.info(f"[{i}/{len(papers_needing_pdf)}] Processing: {entry.title[:60]}...")

        search_result = library_entry_to_search_result(entry)
        download_result = workflow.literature_search.download_paper_with_result(search_result)

        if download_result.success and download_result.pdf_path:
            file_size = "?"
            try:
                if download_result.pdf_path.exists():
                    size_bytes = download_result.pdf_path.stat().st_size
                    file_size = f"{size_bytes:,}B"
            except Exception:
                pass

            if download_result.already_existed:
                logger.info(f"✓ Already exists: {download_result.pdf_path.name} ({file_size})")
            else:
                log_success(f"✓ Downloaded: {download_result.pdf_path.name} ({file_size})")
            downloaded_count += 1
        else:
            error_msg = download_result.failure_message or "Unknown error"
            if len(error_msg) > 200:
                error_msg = error_msg[:197] + "..."
            logger.error(f"✗ Failed: {error_msg}")
            failed_count += 1

    # Display summary
    print(f"\n{'=' * 60}")
    print("PDF DOWNLOAD COMPLETED")
    print("=" * 60)
    print(f"Papers processed: {len(papers_needing_pdf)}")
    print(f"PDFs downloaded: {downloaded_count}")
    if failed_count > 0:
        print(f"Download failures: {failed_count}")
    print(f"Success rate: {(downloaded_count / len(papers_needing_pdf)) * 100:.1f}%")

    display_file_locations()

    if downloaded_count > 0:
        log_success("PDF download complete!")
    else:
        logger.warning("No PDFs were downloaded")

    return 0 if downloaded_count > 0 else 1


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


def run_cleanup(workflow: LiteratureWorkflow) -> int:
    """Clean up library by removing papers without PDFs.

    Args:
        workflow: Configured LiteratureWorkflow instance.

    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("CLEANUP LIBRARY (REMOVE PAPERS WITHOUT PDFs)")

    # Get library entries
    library_entries = workflow.literature_search.library_index.list_entries()

    if not library_entries:
        logger.warning("Library is empty. Nothing to clean up.")
        print("\nLibrary is empty. Nothing to clean up.")
        return 0

    # Find entries without PDFs
    entries_without_pdf = workflow.literature_search.library_index.get_entries_without_pdf()

    print(f"\nLibrary contains {len(library_entries)} papers")
    print(f"Papers with PDFs: {len(library_entries) - len(entries_without_pdf)}")
    print(f"Papers without PDFs: {len(entries_without_pdf)}")

    if not entries_without_pdf:
        print("\nAll papers in the library have PDFs. Nothing to clean up.")
        return 0

    # Show details of papers to be removed
    print(f"\nPapers to be removed ({len(entries_without_pdf)}):")
    for i, entry in enumerate(entries_without_pdf, 1):
        year = entry.year or "n/d"
        authors = entry.authors[0] if entry.authors else "Unknown"
        if len(entry.authors or []) > 1:
            authors += " et al."
        print(f"  {i}. {entry.citation_key} - {authors} ({year}): {entry.title[:60]}...")

    # Ask for confirmation
    print(f"\nThis will permanently remove {len(entries_without_pdf)} papers from the library.")
    print("This action cannot be undone.")
    try:
        confirmation = input("\nProceed with cleanup? [y/N]: ").strip().lower()
    except KeyboardInterrupt:
        print("\n\nCleanup cancelled by user.")
        return 1

    if confirmation not in ('y', 'yes'):
        print("Cleanup cancelled.")
        return 0

    # Perform cleanup
    log_header("REMOVING PAPERS WITHOUT PDFs")
    print(f"Removing {len(entries_without_pdf)} papers...")

    removed_count = 0
    for entry in entries_without_pdf:
        try:
            if workflow.literature_search.remove_paper(entry.citation_key):
                removed_count += 1
                print(f"  ✓ Removed: {entry.citation_key}")
            else:
                logger.warning(f"Failed to remove: {entry.citation_key}")
        except Exception as e:
            logger.error(f"Error removing {entry.citation_key}: {e}")
            continue

    # Show results
    remaining_count = len(library_entries) - removed_count
    print(f"\n{'=' * 60}")
    print("CLEANUP COMPLETED")
    print("=" * 60)
    print(f"Papers removed: {removed_count}")
    print(f"Papers remaining: {remaining_count}")
    print(f"Success rate: {(removed_count / len(entries_without_pdf)) * 100:.1f}%")

    display_file_locations()

    log_success("Library cleanup complete!")
    return 0


def run_llm_operation(workflow: LiteratureWorkflow, operation: str, paper_config_path: Optional[str] = None) -> int:
    """Execute advanced LLM operation on selected papers.

    Args:
        workflow: Configured LiteratureWorkflow instance.
        operation: Type of operation ("review", "communication", "compare", "gaps", "network").
        paper_config_path: Path to paper selection config file.

    Returns:
        Exit code (0=success, 1=failure).
    """
    # Map operation names to display names
    operation_names = {
        "review": "Literature Review Synthesis",
        "communication": "Science Communication Narrative",
        "compare": "Comparative Analysis",
        "gaps": "Research Gap Identification",
        "network": "Citation Network Analysis"
    }

    operation_display = operation_names.get(operation, operation.title())
    log_header(f"ADVANCED LLM OPERATION: {operation_display.upper()}")

    # Initialize LLM operations
    llm_operations = LiteratureLLMOperations(workflow.summarizer.llm_client)

    # Load paper selection config
    config_path = Path(paper_config_path) if paper_config_path else Path("literature/paper_selection.yaml")

    try:
        selector = PaperSelector.from_config(config_path)
        logger.info(f"Loaded paper selection config from {config_path}")
    except FileNotFoundError:
        logger.warning(f"Paper selection config not found: {config_path}")
        logger.info("Using all papers in library (create literature/paper_selection.yaml to filter)")

        # Create a selector that selects all papers
        from infrastructure.literature.paper_selector import PaperSelectionConfig
        selector = PaperSelector(PaperSelectionConfig())

    # Get library entries and apply selection
    library_entries = workflow.literature_search.library_index.list_entries()

    if not library_entries:
        logger.warning("Library is empty. Nothing to analyze.")
        print("\nLibrary is empty. Add papers first using --search-only.")
        return 1

    selected_papers = selector.select_papers(library_entries)

    if not selected_papers:
        logger.warning("No papers match the selection criteria.")
        print(f"\nNo papers match the selection criteria in {config_path}")
        print("Check your paper_selection.yaml configuration.")
        return 1

    # Display selection summary
    selection_stats = selector.get_selection_summary(selected_papers, len(library_entries))
    print(f"\nSelected {selection_stats['selected_papers']} papers from {selection_stats['total_papers']} total")
    print("Papers to analyze:")
    for i, paper in enumerate(selected_papers, 1):
        year = paper.year or "n/d"
        authors = paper.authors[0] if paper.authors else "Unknown"
        if len(paper.authors or []) > 1:
            authors += " et al."
        print(f"  {i}. {paper.citation_key} - {authors} ({year}): {paper.title[:60]}...")

    # Execute the operation
    log_header(f"EXECUTING {operation_display.upper()}")

    try:
        start_time = time.time()

        if operation == "review":
            result = llm_operations.generate_literature_review(selected_papers, focus="general")
        elif operation == "communication":
            result = llm_operations.generate_science_communication(selected_papers)
        elif operation == "compare":
            result = llm_operations.generate_comparative_analysis(selected_papers, aspect="methods")
        elif operation == "gaps":
            result = llm_operations.generate_research_gaps(selected_papers, domain="general")
        elif operation == "network":
            result = llm_operations.analyze_citation_network(selected_papers)

        # Save result
        output_dir = Path("literature/llm_outputs") / f"{operation}_outputs"
        output_path = llm_operations.save_result(result, output_dir)

        total_time = time.time() - start_time

        # Display results
        print(f"\n{'=' * 70}")
        print(f"{operation_display.upper()} COMPLETED")
        print("=" * 70)
        print(f"Papers analyzed: {result.papers_used}")
        print(f"Generation time: {result.generation_time:.1f}s")
        print(f"Estimated tokens: {result.tokens_estimated}")
        print(f"Output saved to: {output_path}")
        print(f"Total operation time: {total_time:.1f}s")

        display_file_locations()

        log_success(f"{operation_display} complete!")
        return 0

    except Exception as e:
        logger.error(f"LLM operation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


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
  # Search and add to bibliography only
  python3 scripts/07_literature_search.py --search-only
  python3 scripts/07_literature_search.py --search-only --keywords "machine learning,optimization"

  # Download PDFs for existing bibliography entries
  python3 scripts/07_literature_search.py --download-only

  # Generate summaries for papers with PDFs
  python3 scripts/07_literature_search.py --summarize

  # Clean up library by removing papers without PDFs
  python3 scripts/07_literature_search.py --cleanup

  # Advanced LLM operations (literature review, science communication, etc.)
  python3 scripts/07_literature_search.py --llm-operation review
  python3 scripts/07_literature_search.py --llm-operation communication --paper-config my_papers.yaml
  python3 scripts/07_literature_search.py --llm-operation compare

  # Combined operations (legacy - use separate operations instead)
  python3 scripts/07_literature_search.py --search --limit 50 --keywords "AI"
  python3 scripts/07_literature_search.py --search --summarize
"""
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Search for papers, download PDFs, and generate summaries"
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Search for papers and add to bibliography only (no download or summarize)"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download PDFs for existing bibliography entries (no search or summarize)"
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate summaries for papers with PDFs (no search or download)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up library by removing papers without PDFs"
    )
    parser.add_argument(
        "--llm-operation",
        choices=["review", "communication", "compare", "gaps", "network"],
        help="Perform advanced LLM operation on selected papers"
    )
    parser.add_argument(
        "--paper-config",
        type=str,
        help="Path to YAML config file for paper selection (default: literature/paper_selection.yaml)"
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
    if not args.search and not args.search_only and not args.download_only and not args.summarize and not args.cleanup and not args.llm_operation:
        parser.print_help()
        print("\nError: Must specify one of --search, --search-only, --download-only, --summarize, --cleanup, or --llm-operation")
        return 1

    # Check for conflicting operations
    operation_count = sum([args.search, args.search_only, args.download_only, args.summarize, args.cleanup, bool(args.llm_operation)])
    if operation_count > 1:
        parser.print_help()
        print("\nError: Can only specify one operation at a time")
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

        # Run appropriate operation
        if args.search_only:
            exit_code = run_search_only(workflow, keywords=keywords, limit=args.limit)
        elif args.download_only:
            exit_code = run_download_only(workflow)
        elif args.search:
            exit_code = run_search(workflow, keywords=keywords, limit=args.limit)
        elif args.summarize:
            exit_code = run_summarize(workflow)
        elif args.cleanup:
            exit_code = run_cleanup(workflow)
        elif args.llm_operation:
            exit_code = run_llm_operation(workflow, args.llm_operation, args.paper_config)

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

