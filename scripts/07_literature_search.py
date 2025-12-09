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

Standalone literature management orchestrator (not part of main pipeline stages).
Literature operations are available via menu option 9+ in run.sh interactive menu.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header
from infrastructure.literature import LiteratureSearch, LiteratureConfig
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.progress import ProgressTracker
from infrastructure.literature.summarizer import PaperSummarizer, SummaryQualityValidator
from infrastructure.literature.search_orchestrator import (
    run_search_only,
    run_download_only,
    run_search,
    run_cleanup,
    run_llm_operation,
    display_file_locations,
    DEFAULT_LIMIT_PER_KEYWORD,
)
from infrastructure.literature.summarize_orchestrator import run_summarize
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
  # ORCHESTRATED PIPELINE (search → download → summarize)
  # Interactive mode - prompts for keywords and limit
  python3 scripts/07_literature_search.py --search

  # Non-interactive mode - provide keywords and limit
  python3 scripts/07_literature_search.py --search --keywords "machine learning,optimization"
  python3 scripts/07_literature_search.py --search --limit 50 --keywords "AI"

  # INDIVIDUAL OPERATIONS
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
"""
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="ORCHESTRATED PIPELINE: Search for papers, download PDFs, and generate summaries (interactive)"
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
            exit_code = run_search(workflow, keywords=keywords, limit=args.limit, max_parallel_summaries=MAX_PARALLEL_SUMMARIES)
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
