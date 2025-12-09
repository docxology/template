"""Search workflow orchestration for literature processing."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.library_index import LibraryEntry
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
        pdf_url=entry.pdf_url,
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

    print("\nThis will:")
    print(f"  1. Search {sources_display} for papers")
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

        # Get source information
        source_health = workflow.literature_search.get_source_health_status()
        enabled_sources = list(workflow.literature_search.sources.keys())
        
        # Display results
        print(f"\n{'=' * 60}")
        print("SEARCH COMPLETED")
        print("=" * 60)
        print(f"Keywords searched: {', '.join(keywords)}")
        print(f"Sources used: {', '.join(enabled_sources)}")
        print(f"Papers found: {papers_found}")
        print(f"Papers added to bibliography: {added_count}")
        if already_existed_count > 0:
            print(f"Papers already in bibliography: {already_existed_count}")
        print(f"Success rate: {(added_count / papers_found) * 100:.1f}%")
        
        # Display source health status
        unhealthy_sources = [name for name, status in source_health.items() 
                          if not status.get('healthy', True)]
        if unhealthy_sources:
            print(f"\n⚠️  Note: Some sources had issues: {', '.join(unhealthy_sources)}")
        
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
    papers_needing_pdf = find_papers_needing_pdf(library_entries)

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
    from infrastructure.literature.clear_operations import clear_pdfs, clear_summaries, clear_library
    
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

    print("\nThis will:")
    print(f"  1. Search {sources_display} for papers")
    print("  2. Download PDFs and add to BibTeX library")
    print("  3. Generate AI summaries for each paper")
    print(f"  4. Process up to {max_parallel_summaries} papers in parallel")
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
        
        print(f"\n{'=' * 60}")
        print("SEARCH COMPLETED")
        print("=" * 60)
        print(f"Keywords searched: {', '.join(keywords)}")
        print(f"Sources used: {', '.join(enabled_sources)}")
        print(f"Papers found: {stats['search']['papers_found']}")
        print(f"Papers already downloaded: {result.papers_already_existed}")
        print(f"Papers newly downloaded: {result.papers_newly_downloaded}")
        print(f"Download failures: {result.papers_failed_download}")
        print(f"Papers summarized: {stats['summarization']['successful']}")
        if result.summaries_skipped > 0:
            print(f"Summaries skipped (already exist): {result.summaries_skipped}")
        print(f"Summary failures: {result.summaries_failed}")
        print(f"Success rate: {result.success_rate:.1f}%")
        
        # Display source health status
        unhealthy_sources = [name for name, status in source_health.items() 
                          if not status.get('healthy', True)]
        if unhealthy_sources:
            print(f"\n⚠️  Note: Some sources had issues: {', '.join(unhealthy_sources)}")
        
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
    import time
    from infrastructure.literature.paper_selector import PaperSelector
    from infrastructure.literature.llm_operations import LiteratureLLMOperations
    
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

