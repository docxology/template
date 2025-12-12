"""Search workflow orchestration for literature processing."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.literature.workflow.workflow import LiteratureWorkflow
from infrastructure.literature.library.index import LibraryEntry
from infrastructure.literature.sources import SearchResult

logger = get_logger(__name__)

DEFAULT_LIMIT_PER_KEYWORD = int(os.environ.get("LITERATURE_DEFAULT_LIMIT", "25"))


def get_keywords_input() -> List[str]:
    """Prompt user for comma-separated keywords.
    
    Multi-word terms are automatically quoted (e.g., "free energy principle").
    Users don't need to type quotes themselves.
    
    Returns:
        List of keyword strings, with multi-word terms automatically quoted.
    """
    try:
        keywords_str = input("Enter keywords (comma-separated, multi-word terms auto-quoted): ").strip()
        if not keywords_str:
            return []
        
        # Split by comma and process each keyword
        keywords = []
        for k in keywords_str.split(','):
            k = k.strip()
            if not k:
                continue
            
            # Remove existing quotes if user added them (we'll add our own)
            k = k.strip('"\'')
            
            # If keyword contains spaces, wrap it in quotes
            if ' ' in k:
                k = f'"{k}"'
            
            keywords.append(k)
        
        return keywords
    except (EOFError, KeyboardInterrupt):
        return []


def get_limit_input(default: int = DEFAULT_LIMIT_PER_KEYWORD) -> int:
    """Prompt user for search limit."""
    try:
        limit_str = input(f"Results per keyword [{default}]: ").strip()
        if not limit_str:
            return default
        return int(limit_str)
    except (ValueError, EOFError, KeyboardInterrupt):
        return default


def get_clear_options_input() -> tuple:
    """Prompt user for clear options.
    
    Returns:
        Tuple of (clear_pdfs, clear_summaries, clear_library).
    """
    try:
        print("\nClear options (default: No - incremental/additive behavior):")
        clear_pdfs_str = input("  Clear PDFs before download? [y/N]: ").strip().lower()
        clear_pdfs = clear_pdfs_str in ('y', 'yes')
        
        clear_summaries_str = input("  Clear summaries before generation? [y/N]: ").strip().lower()
        clear_summaries = clear_summaries_str in ('y', 'yes')
        
        print("  ⚠️  WARNING: Total clear will delete library index, PDFs, summaries, and progress file")
        clear_library_str = input("  Clear library completely (total clear)? [y/N]: ").strip().lower()
        clear_library = clear_library_str in ('y', 'yes')
        
        return (clear_pdfs, clear_summaries, clear_library)
    except (EOFError, KeyboardInterrupt):
        return (False, False, False)


def library_entry_to_search_result(entry: LibraryEntry) -> SearchResult:
    """Convert library entry to search result for processing."""
    return SearchResult(
        title=entry.title,
        authors=entry.authors or [],
        year=entry.year,
        doi=entry.doi,
        url=entry.url,
        pdf_url=entry.metadata.get("pdf_url"),
        abstract=entry.abstract,
        source=entry.source or "library"
    )


def get_pdf_path_for_entry(entry: LibraryEntry) -> Optional[Path]:
    """Get PDF path for a library entry."""
    if entry.pdf_path:
        pdf_path = Path(entry.pdf_path)
        if not pdf_path.is_absolute():
            pdf_path = Path("literature") / pdf_path
        if pdf_path.exists():
            return pdf_path

    # Check expected location
    expected_pdf = Path("literature/pdfs") / f"{entry.citation_key}.pdf"
    if expected_pdf.exists():
        return expected_pdf

    return None


def find_papers_needing_pdf(library_entries: List[LibraryEntry]) -> List[LibraryEntry]:
    """Find library entries that need PDF downloads."""
    papers_needing_pdf = []
    for entry in library_entries:
        pdf_path = get_pdf_path_for_entry(entry)
        if not pdf_path or not pdf_path.exists():
            papers_needing_pdf.append(entry)
    return papers_needing_pdf


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

    # Get enabled sources
    enabled_sources = list(workflow.literature_search.sources.keys())
    # Filter out sources that don't support search (like unpaywall)
    searchable_sources = [s for s in enabled_sources 
                         if hasattr(workflow.literature_search.sources[s], 'search')]
    
    # Format sources display
    if not searchable_sources:
        sources_display = "no sources"
    elif len(searchable_sources) <= 8:
        # Show all sources if 8 or fewer
        sources_display = ', '.join(searchable_sources)
    else:
        # For many sources, show first few and count
        sources_display = f"{', '.join(searchable_sources[:5])}, and {len(searchable_sources) - 5} more"

    logger.info("\nThis will:")
    logger.info(f"  1. Search {sources_display} for papers")
    logger.info("  2. Add papers to bibliography (no download or summarization)")
    logger.info("")

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

        # Get source information
        source_health = workflow.literature_search.get_source_health_status()
        enabled_sources = list(workflow.literature_search.sources.keys())
        
        # Display results
        logger.info(f"\n{'=' * 60}")
        logger.info("SEARCH COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Keywords searched: {', '.join(keywords)}")
        logger.info(f"Sources used: {', '.join(enabled_sources)}")
        logger.info(f"Papers found: {papers_found}")
        logger.info(f"Papers added to bibliography: {added_count}")
        if already_existed_count > 0:
            logger.info(f"Papers already in bibliography: {already_existed_count}")
        logger.info(f"Success rate: {(added_count / papers_found) * 100:.1f}%")
        
        # Display source health status
        unhealthy_sources = [name for name, status in source_health.items() 
                          if not status.get('healthy', True)]
        if unhealthy_sources:
            logger.warning(f"\n⚠️  Note: Some sources had issues: {', '.join(unhealthy_sources)}")
        
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
        return 0

    # Find entries needing PDFs
    papers_needing_pdf = find_papers_needing_pdf(library_entries)

    logger.info(f"\nLibrary contains {len(library_entries)} papers")
    logger.info(f"Papers needing PDF download: {len(papers_needing_pdf)}")

    if not papers_needing_pdf:
        logger.info("\nAll papers in bibliography already have PDFs. Nothing to download.")
        return 0

    # Download PDFs
    log_header("DOWNLOADING PDFs")
    logger.info(f"Attempting to download {len(papers_needing_pdf)} PDFs...")

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
    logger.info(f"\n{'=' * 60}")
    logger.info("PDF DOWNLOAD COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Papers processed: {len(papers_needing_pdf)}")
    logger.info(f"PDFs downloaded: {downloaded_count}")
    if failed_count > 0:
        logger.warning(f"Download failures: {failed_count}")
    logger.info(f"Success rate: {(downloaded_count / len(papers_needing_pdf)) * 100:.1f}%")

    if downloaded_count > 0:
        log_success("PDF download complete!")
    else:
        logger.warning("No PDFs were downloaded")

    return 0 if downloaded_count > 0 else 1


def run_search(
    workflow: LiteratureWorkflow,
    keywords: Optional[List[str]] = None,
    limit: Optional[int] = None,
    max_parallel_summaries: int = 1,
    clear_pdfs: bool = False,
    clear_summaries: bool = False,
    clear_library: bool = False,
    interactive: bool = True,
) -> int:
    """Execute literature search workflow.
    
    Args:
        workflow: Configured LiteratureWorkflow instance.
        keywords: Optional keywords list (prompts if not provided).
        limit: Optional limit per keyword (prompts if not provided).
        max_parallel_summaries: Maximum parallel summarization workers.
        clear_pdfs: Clear PDFs before download (default: False).
        clear_summaries: Clear summaries before generation (default: False).
        clear_library: Perform total clear (library index, PDFs, summaries, progress file) 
                      before operations (default: False). If True, skips individual clear operations.
        interactive: Whether in interactive mode.
        
    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("Literature Search and PDF Download")
    
    # Handle clear operations
    from infrastructure.literature.library.clear import clear_pdfs, clear_summaries, clear_library
    
    # If clear_library is True, it performs a total clear (library, PDFs, summaries, progress)
    # So we skip individual clear operations to avoid redundancy
    if clear_library:
        result = clear_library(confirm=True, interactive=interactive)
        if not result["success"]:
            logger.info("Library clear cancelled")
            return 1
        logger.info(f"Total clear completed: {result['message']}")
        # Skip individual clears since total clear already did everything
        clear_pdfs = False
        clear_summaries = False
    else:
        # Individual clear operations (only if not doing total clear)
        if clear_pdfs:
            result = clear_pdfs(confirm=True, interactive=interactive)
            if not result["success"]:
                logger.info("PDF clear cancelled")
                return 1
            logger.info(f"Cleared PDFs: {result['message']}")
        
        if clear_summaries:
            result = clear_summaries(confirm=True, interactive=interactive)
            if not result["success"]:
                logger.info("Summary clear cancelled")
                return 1
            logger.info(f"Cleared summaries: {result['message']}")
    
    # Get enabled sources
    enabled_sources = list(workflow.literature_search.sources.keys())
    # Filter out sources that don't support search (like unpaywall)
    searchable_sources = [s for s in enabled_sources 
                         if hasattr(workflow.literature_search.sources[s], 'search')]
    
    # Format sources display
    if not searchable_sources:
        sources_display = "no sources"
    elif len(searchable_sources) <= 8:
        # Show all sources if 8 or fewer
        sources_display = ', '.join(searchable_sources)
    else:
        # For many sources, show first few and count
        sources_display = f"{', '.join(searchable_sources[:5])}, and {len(searchable_sources) - 5} more"

    logger.info("\nThis will:")
    logger.info(f"  1. Search {sources_display} for papers")
    logger.info("  2. Download PDFs and add to BibTeX library")
    logger.info("  3. Generate AI summaries for each paper")
    logger.info(f"  4. Process up to {max_parallel_summaries} papers in parallel")
    logger.info("")
    
    # Get limit if not provided
    if limit is None:
        limit = get_limit_input()
    
    # Get keywords if not provided
    if keywords is None:
        keywords = get_keywords_input()
        if not keywords:
            logger.info("No keywords provided. Exiting.")
            return 1
    
    # Get clear options if in interactive mode
    if interactive and not (clear_pdfs or clear_summaries or clear_library):
        clear_pdfs, clear_summaries, clear_library = get_clear_options_input()
    
    # Execute search and summarization
    log_header("Executing Literature Search")
    logger.info(f"Search keywords: {', '.join(keywords)}")
    logger.info(f"Results per keyword: {limit}")
    logger.info(f"Max parallel summaries: {max_parallel_summaries}")
    
    try:
        result = workflow.execute_search_and_summarize(
            keywords=keywords,
            limit_per_keyword=limit,
            max_parallel_summaries=max_parallel_summaries,
            resume_existing=True,
            interactive=True
        )
        
        # Display results
        stats = workflow.get_workflow_stats(result)
        
        # Get source information
        source_health = workflow.literature_search.get_source_health_status()
        enabled_sources = list(workflow.literature_search.sources.keys())
        
        logger.info(f"\n{'=' * 60}")
        logger.info("SEARCH COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Keywords searched: {', '.join(keywords)}")
        logger.info(f"Sources used: {', '.join(enabled_sources)}")
        logger.info(f"Papers found: {stats['search']['papers_found']}")
        logger.info(f"Papers already downloaded: {result.papers_already_existed}")
        logger.info(f"Papers newly downloaded: {result.papers_newly_downloaded}")
        logger.info(f"Download failures: {result.papers_failed_download}")
        logger.info(f"Papers summarized: {stats['summarization']['successful']}")
        if result.summaries_skipped > 0:
            logger.info(f"Summaries skipped (already exist): {result.summaries_skipped}")
        logger.info(f"Summary failures: {result.summaries_failed}")
        logger.info(f"Success rate: {result.success_rate:.1f}%")
        
        # Display source health status
        unhealthy_sources = [name for name, status in source_health.items() 
                          if not status.get('healthy', True)]
        if unhealthy_sources:
            logger.warning(f"\n⚠️  Note: Some sources had issues: {', '.join(unhealthy_sources)}")
        
        log_success("Literature search complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def display_file_locations() -> None:
    """Display file location summary."""
    import json
    
    logger.info("\nOutput files:")
    logger.info("- literature/references.bib (BibTeX references)")
    
    try:
        with open("literature/library.json", "r") as f:
            library_data = json.load(f)
            entry_count = library_data.get("count", 0)
        logger.info(f"- literature/library.json (JSON index with {entry_count} papers)")
    except Exception:
        logger.info("- literature/library.json (JSON index)")
    
    try:
        pdf_count = len(list(Path("literature/pdfs").glob("*.pdf")))
        pdf_dir = Path("literature/pdfs")
        total_pdf_size = sum(f.stat().st_size for f in pdf_dir.glob("*.pdf") if f.is_file())
        logger.info(f"- literature/pdfs/ ({pdf_count} PDFs, {total_pdf_size:,} bytes total)")
    except Exception:
        logger.info("- literature/pdfs/ (downloaded PDFs)")
    
    try:
        summary_count = len(list(Path("literature/summaries").glob("*.md")))
        summary_dir = Path("literature/summaries")
        total_summary_size = sum(f.stat().st_size for f in summary_dir.glob("*.md") if f.is_file())
        logger.info(f"- literature/summaries/ ({summary_count} summaries, {total_summary_size:,} bytes total)")
    except Exception:
        logger.info("- literature/summaries/ (AI-generated summaries)")
    
    logger.info("- literature/summarization_progress.json (progress tracking)")


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
        return 0

    # Find entries without PDFs
    entries_without_pdf = workflow.literature_search.library_index.get_entries_without_pdf()

    logger.info(f"\nLibrary contains {len(library_entries)} papers")
    logger.info(f"Papers with PDFs: {len(library_entries) - len(entries_without_pdf)}")
    logger.info(f"Papers without PDFs: {len(entries_without_pdf)}")

    if not entries_without_pdf:
        logger.info("\nAll papers in the library have PDFs. Nothing to clean up.")
        return 0

    # Show details of papers to be removed
    logger.info(f"\nPapers to be removed ({len(entries_without_pdf)}):")
    for i, entry in enumerate(entries_without_pdf, 1):
        year = entry.year or "n/d"
        authors = entry.authors[0] if entry.authors else "Unknown"
        if len(entry.authors or []) > 1:
            authors += " et al."
        logger.info(f"  {i}. {entry.citation_key} - {authors} ({year}): {entry.title[:60]}...")

    # Ask for confirmation
    logger.info(f"\nThis will permanently remove {len(entries_without_pdf)} papers from the library.")
    logger.info("This action cannot be undone.")
    try:
        confirmation = input("\nProceed with cleanup? [y/N]: ").strip().lower()
    except KeyboardInterrupt:
        logger.info("\n\nCleanup cancelled by user.")
        return 1

    if confirmation not in ('y', 'yes'):
        logger.info("Cleanup cancelled.")
        return 0

    # Perform cleanup
    log_header("REMOVING PAPERS WITHOUT PDFs")
    logger.info(f"Removing {len(entries_without_pdf)} papers...")

    removed_count = 0
    for entry in entries_without_pdf:
        try:
            if workflow.literature_search.remove_paper(entry.citation_key):
                removed_count += 1
                logger.info(f"  ✓ Removed: {entry.citation_key}")
            else:
                logger.warning(f"Failed to remove: {entry.citation_key}")
        except Exception as e:
            logger.error(f"Error removing {entry.citation_key}: {e}")
            continue

    # Show results
    remaining_count = len(library_entries) - removed_count
    logger.info(f"\n{'=' * 60}")
    logger.info("CLEANUP COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Papers removed: {removed_count}")
    logger.info(f"Papers remaining: {remaining_count}")
    logger.info(f"Success rate: {(removed_count / len(entries_without_pdf)) * 100:.1f}%")

    display_file_locations()

    log_success("Library cleanup complete!")
    return 0


def run_meta_analysis(
    workflow: LiteratureWorkflow,
    keywords: Optional[List[str]] = None,
    limit: Optional[int] = None,
    clear_pdfs: bool = False,
    clear_library: bool = False,
    interactive: bool = True,
) -> int:
    """Execute literature search workflow with meta-analysis.
    
    Runs search → download → extract → meta-analysis pipeline.
    Performs PCA analysis, keyword analysis, author analysis, and visualizations.
    
    Args:
        workflow: Configured LiteratureWorkflow instance.
        keywords: Optional keywords list (prompts if not provided).
        limit: Optional limit per keyword (prompts if not provided).
        clear_pdfs: Clear PDFs before download (default: False).
        clear_library: Perform total clear before operations (default: False).
        interactive: Whether in interactive mode.
        
    Returns:
        Exit code (0=success, 1=failure).
    """
    log_header("LITERATURE SEARCH AND META-ANALYSIS PIPELINE")
    
    # Handle clear operations
    from infrastructure.literature.library.clear import clear_pdfs as clear_pdfs_func, clear_library as clear_library_func
    
    if clear_library:
        result = clear_library_func(confirm=True, interactive=interactive)
        if not result["success"]:
            logger.info("Library clear cancelled")
            return 1
        logger.info(f"Total clear completed: {result['message']}")
        clear_pdfs = False
    elif clear_pdfs:
        result = clear_pdfs_func(confirm=True, interactive=interactive)
        if not result["success"]:
            logger.info("PDF clear cancelled")
            return 1
        logger.info(f"Cleared PDFs: {result['message']}")
    
    # Get enabled sources
    enabled_sources = list(workflow.literature_search.sources.keys())
    searchable_sources = [s for s in enabled_sources 
                         if hasattr(workflow.literature_search.sources[s], 'search')]
    
    # Format sources display
    if not searchable_sources:
        sources_display = "no sources"
    elif len(searchable_sources) <= 8:
        sources_display = ', '.join(searchable_sources)
    else:
        sources_display = f"{', '.join(searchable_sources[:5])}, and {len(searchable_sources) - 5} more"

    logger.info("\nThis will:")
    logger.info(f"  1. Search {sources_display} for papers")
    logger.info("  2. Download PDFs and add to BibTeX library")
    logger.info("  3. Extract text from PDFs")
    logger.info("  4. Perform meta-analysis (PCA, keywords, authors, visualizations)")
    logger.info("")
    
    # Get limit if not provided
    if limit is None:
        limit = get_limit_input()
    
    # Get keywords if not provided
    if keywords is None:
        keywords = get_keywords_input()
        if not keywords:
            logger.info("No keywords provided. Exiting.")
            return 1
    
    # Get clear options if in interactive mode
    if interactive and not (clear_pdfs or clear_library):
        clear_pdfs, _, clear_library = get_clear_options_input()
        if clear_library:
            result = clear_library_func(confirm=True, interactive=interactive)
            if not result["success"]:
                logger.info("Library clear cancelled")
                return 1
            logger.info(f"Total clear completed: {result['message']}")
            clear_pdfs = False
        elif clear_pdfs:
            result = clear_pdfs_func(confirm=True, interactive=interactive)
            if not result["success"]:
                logger.info("PDF clear cancelled")
                return 1
            logger.info(f"Cleared PDFs: {result['message']}")
    
    # Step 1: Search
    log_header("STEP 1: SEARCHING FOR PAPERS")
    logger.info(f"Search keywords: {', '.join(keywords)}")
    logger.info(f"Results per keyword: {limit}")
    
    try:
        search_results = workflow._search_papers(keywords, limit)
        papers_found = len(search_results)
        
        if not search_results:
            logger.warning("No papers found for the given keywords")
            return 1
        
        # Add all results to library
        added_count = 0
        already_existed_count = 0
        
        for result in search_results:
            try:
                citation_key = workflow.literature_search.add_to_library(result)
                added_count += 1
                logger.info(f"Added: {citation_key}")
            except Exception:
                already_existed_count += 1
                logger.debug(f"Already exists: {result.title[:50]}...")
        
        logger.info(f"Papers found: {papers_found}")
        logger.info(f"Papers added to bibliography: {added_count}")
        if already_existed_count > 0:
            logger.info(f"Papers already in bibliography: {already_existed_count}")
        
        # Step 2: Download PDFs
        log_header("STEP 2: DOWNLOADING PDFs")
        library_entries = workflow.literature_search.library_index.list_entries()
        papers_needing_pdf = find_papers_needing_pdf(library_entries)
        
        if papers_needing_pdf:
            logger.info(f"Downloading {len(papers_needing_pdf)} PDFs...")
            downloaded_count = 0
            failed_count = 0
            
            for i, entry in enumerate(papers_needing_pdf, 1):
                logger.info(f"[{i}/{len(papers_needing_pdf)}] Processing: {entry.title[:60]}...")
                search_result = library_entry_to_search_result(entry)
                download_result = workflow.literature_search.download_paper_with_result(search_result)
                
                if download_result.success and download_result.pdf_path:
                    downloaded_count += 1
                    logger.info(f"✓ Downloaded: {download_result.pdf_path.name}")
                else:
                    failed_count += 1
                    logger.warning(f"✗ Failed: {entry.citation_key}")
            
            logger.info(f"PDFs downloaded: {downloaded_count}")
            if failed_count > 0:
                logger.warning(f"Download failures: {failed_count}")
        else:
            logger.info("All papers already have PDFs")
        
        # Step 3: Extract text
        log_header("STEP 3: EXTRACTING TEXT FROM PDFs")
        from infrastructure.literature.summarization.orchestrator import run_extract_text
        extract_exit_code = run_extract_text(workflow)
        if extract_exit_code != 0:
            logger.warning("Some text extractions failed, continuing with meta-analysis...")
        
        # Step 4: Meta-analysis
        log_header("STEP 4: PERFORMING META-ANALYSIS")
        
        # Ensure output directory exists
        output_dir = Path("literature/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Initialize aggregator
        from infrastructure.literature.meta_analysis.aggregator import DataAggregator
        aggregator = DataAggregator(workflow.literature_search.config)
        
        # Get library entries for analysis
        library_entries = workflow.literature_search.library_index.list_entries()
        
        if not library_entries:
            logger.warning("Library is empty. Cannot perform meta-analysis.")
            return 1
        
        logger.info(f"Analyzing {len(library_entries)} papers...")
        
        # Perform meta-analysis operations
        outputs_generated = []
        
        try:
            # PCA Analysis
            logger.info("Generating PCA visualizations...")
            from infrastructure.literature.meta_analysis.pca import (
                create_pca_2d_plot,
                create_pca_3d_plot,
            )
            
            pca_2d_path = create_pca_2d_plot(aggregator=aggregator, n_clusters=5, format="png")
            outputs_generated.append(("PCA 2D", pca_2d_path))
            logger.info(f"✓ Generated: {pca_2d_path.name}")
            
            pca_3d_path = create_pca_3d_plot(aggregator=aggregator, n_clusters=5, format="png")
            outputs_generated.append(("PCA 3D", pca_3d_path))
            logger.info(f"✓ Generated: {pca_3d_path.name}")
            
        except ImportError as e:
            logger.warning(f"PCA analysis skipped (scikit-learn not available): {e}")
        except Exception as e:
            logger.warning(f"PCA analysis failed: {e}")
        
        try:
            # Keyword Analysis
            logger.info("Generating keyword analysis...")
            from infrastructure.literature.meta_analysis.keywords import (
                create_keyword_frequency_plot,
                create_keyword_evolution_plot,
            )
            
            keyword_data = aggregator.prepare_keyword_data()
            keyword_freq_path = create_keyword_frequency_plot(
                keyword_data, top_n=20, format="png"
            )
            outputs_generated.append(("Keyword Frequency", keyword_freq_path))
            logger.info(f"✓ Generated: {keyword_freq_path.name}")
            
            # Get top keywords for evolution plot
            sorted_keywords = sorted(
                keyword_data.keyword_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            top_keywords = [k for k, _ in sorted_keywords]
            
            if top_keywords:
                keyword_evol_path = create_keyword_evolution_plot(
                    keyword_data, keywords=top_keywords, format="png"
                )
                outputs_generated.append(("Keyword Evolution", keyword_evol_path))
                logger.info(f"✓ Generated: {keyword_evol_path.name}")
            
        except Exception as e:
            logger.warning(f"Keyword analysis failed: {e}")
        
        try:
            # Author Analysis
            logger.info("Generating author analysis...")
            from infrastructure.literature.meta_analysis.metadata import (
                create_author_contributions_plot,
            )
            
            author_path = create_author_contributions_plot(
                top_n=20, aggregator=aggregator, format="png"
            )
            outputs_generated.append(("Author Contributions", author_path))
            logger.info(f"✓ Generated: {author_path.name}")
            
        except Exception as e:
            logger.warning(f"Author analysis failed: {e}")
        
        try:
            # Metadata Visualizations
            logger.info("Generating metadata visualizations...")
            from infrastructure.literature.meta_analysis.metadata import (
                create_venue_distribution_plot,
                create_citation_distribution_plot,
            )
            
            venue_path = create_venue_distribution_plot(
                top_n=15, aggregator=aggregator, format="png"
            )
            outputs_generated.append(("Venue Distribution", venue_path))
            logger.info(f"✓ Generated: {venue_path.name}")
            
            citation_path = create_citation_distribution_plot(
                aggregator=aggregator, format="png"
            )
            outputs_generated.append(("Citation Distribution", citation_path))
            logger.info(f"✓ Generated: {citation_path.name}")
            
        except Exception as e:
            logger.warning(f"Metadata visualization failed: {e}")
        
        try:
            # Temporal Analysis
            logger.info("Generating temporal analysis...")
            from infrastructure.literature.meta_analysis.temporal import (
                create_publication_timeline_plot,
            )
            
            timeline_path = create_publication_timeline_plot(
                aggregator=aggregator, format="png"
            )
            outputs_generated.append(("Publication Timeline", timeline_path))
            logger.info(f"✓ Generated: {timeline_path.name}")
            
        except Exception as e:
            logger.warning(f"Temporal analysis failed: {e}")
        
        try:
            # PCA Loadings Export
            logger.info("Exporting PCA loadings...")
            from infrastructure.literature.meta_analysis.pca import export_pca_loadings
            
            loadings_outputs = export_pca_loadings(
                aggregator=aggregator,
                n_components=5,
                top_n_words=20,
                output_dir=Path("literature/output")
            )
            
            for format_name, path in loadings_outputs.items():
                outputs_generated.append((f"PCA Loadings ({format_name})", path))
                logger.info(f"✓ Generated: {path.name}")
            
        except ImportError as e:
            logger.warning(f"PCA loadings export skipped (scikit-learn not available): {e}")
        except Exception as e:
            logger.warning(f"PCA loadings export failed: {e}")
        
        try:
            # PCA Loadings Visualizations
            logger.info("Generating PCA loadings visualizations...")
            from infrastructure.literature.meta_analysis.pca_loadings import create_loadings_visualizations
            
            loadings_viz_outputs = create_loadings_visualizations(
                aggregator=aggregator,
                n_components=5,
                top_n_words=20,
                output_dir=Path("literature/output"),
                format="png"
            )
            
            for viz_name, path in loadings_viz_outputs.items():
                outputs_generated.append((f"PCA Loadings ({viz_name})", path))
                logger.info(f"✓ Generated: {path.name}")
            
        except ImportError as e:
            logger.warning(f"PCA loadings visualizations skipped (scikit-learn not available): {e}")
        except Exception as e:
            logger.warning(f"PCA loadings visualizations failed: {e}")
        
        try:
            # Metadata Completeness Visualization
            logger.info("Generating metadata completeness visualization...")
            from infrastructure.literature.meta_analysis.metadata import create_metadata_completeness_plot
            
            completeness_path = create_metadata_completeness_plot(
                aggregator=aggregator, format="png"
            )
            outputs_generated.append(("Metadata Completeness", completeness_path))
            logger.info(f"✓ Generated: {completeness_path.name}")
            
        except Exception as e:
            logger.warning(f"Metadata completeness visualization failed: {e}")
        
        try:
            # Graphical Abstracts
            logger.info("Generating graphical abstracts...")
            from infrastructure.literature.meta_analysis.graphical_abstract import (
                create_single_page_abstract,
                create_multi_page_abstract,
            )
            
            # Single-page abstract
            single_page_path = create_single_page_abstract(
                aggregator=aggregator,
                keywords=keywords,
                format="png"
            )
            outputs_generated.append(("Graphical Abstract (Single Page)", single_page_path))
            logger.info(f"✓ Generated: {single_page_path.name}")
            
            # Multi-page abstract
            multi_page_path = create_multi_page_abstract(
                aggregator=aggregator,
                keywords=keywords,
                format="pdf"
            )
            outputs_generated.append(("Graphical Abstract (Multi-Page)", multi_page_path))
            logger.info(f"✓ Generated: {multi_page_path.name}")
            
        except Exception as e:
            logger.warning(f"Graphical abstract generation failed: {e}")
        
        try:
            # Summary Reports
            logger.info("Generating summary reports...")
            from infrastructure.literature.meta_analysis.summary import generate_all_summaries
            
            summary_outputs = generate_all_summaries(
                aggregator=aggregator,
                output_dir=Path("literature/output"),
                n_pca_components=5
            )
            
            for format_name, path in summary_outputs.items():
                outputs_generated.append((f"Summary ({format_name})", path))
                logger.info(f"✓ Generated: {path.name}")
            
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
        
        # Display summary
        logger.info(f"\n{'=' * 60}")
        logger.info("META-ANALYSIS COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Keywords searched: {', '.join(keywords)}")
        logger.info(f"Papers found: {papers_found}")
        logger.info(f"Papers added: {added_count}")
        logger.info(f"Outputs generated: {len(outputs_generated)}")
        logger.info("\nGenerated visualizations:")
        for name, path in outputs_generated:
            logger.info(f"  • {name}: {path}")
        
        log_success("Meta-analysis pipeline complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Meta-analysis pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_llm_operation(workflow: LiteratureWorkflow, operation: str, paper_config_path: Optional[str] = None) -> int:
    """Execute advanced LLM operation on selected papers.

    Args:
        workflow: Configured LiteratureWorkflow instance.
        operation: Type of operation ("review", "communication", "compare", "gaps", "network").
        paper_config_path: Path to paper selection config file.

    Returns:
        Exit code (0=success, 1=failure).
    """
    import time
    from infrastructure.literature.llm.selector import PaperSelector
    from infrastructure.literature.llm.operations import LiteratureLLMOperations
    
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
        from infrastructure.literature.llm.selector import PaperSelectionConfig
        selector = PaperSelector(PaperSelectionConfig())

    # Get library entries and apply selection
    library_entries = workflow.literature_search.library_index.list_entries()

    if not library_entries:
        logger.warning("Library is empty. Nothing to analyze.")
        logger.warning("Add papers first using --search-only.")
        return 1

    selected_papers = selector.select_papers(library_entries)

    if not selected_papers:
        logger.warning("No papers match the selection criteria.")
        logger.warning(f"No papers match the selection criteria in {config_path}")
        logger.warning("Check your paper_selection.yaml configuration.")
        return 1

    # Display selection summary
    selection_stats = selector.get_selection_summary(selected_papers, len(library_entries))
    logger.info(f"\nSelected {selection_stats['selected_papers']} papers from {selection_stats['total_papers']} total")
    logger.info("Papers to analyze:")
    for i, paper in enumerate(selected_papers, 1):
        year = paper.year or "n/d"
        authors = paper.authors[0] if paper.authors else "Unknown"
        if len(paper.authors or []) > 1:
            authors += " et al."
        logger.info(f"  {i}. {paper.citation_key} - {authors} ({year}): {paper.title[:60]}...")

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
        logger.info(f"\n{'=' * 70}")
        logger.info(f"{operation_display.upper()} COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Papers analyzed: {result.papers_used}")
        logger.info(f"Generation time: {result.generation_time:.1f}s")
        logger.info(f"Estimated tokens: {result.tokens_estimated}")
        logger.info(f"Output saved to: {output_path}")
        logger.info(f"Total operation time: {total_time:.1f}s")

        display_file_locations()

        log_success(f"{operation_display} complete!")
        return 0

    except Exception as e:
        logger.error(f"LLM operation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

