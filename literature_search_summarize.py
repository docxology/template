#!/usr/bin/env python3
from __future__ import annotations

"""Literature Search and Summarization Script.

This thin orchestrator:
1. Prompts user for comma-separated keywords
2. Searches arXiv and Semantic Scholar for papers matching any keyword (union)
3. Downloads PDFs and BibTeX references to literature/ directory
4. Uses local Ollama LLM to generate structured summaries for each PDF
5. Saves summaries to literature/summaries/ subfolder

Output Structure:
    literature/
    ├── pdfs/                    # Downloaded PDFs
    │   ├── smith2024machine.pdf
    │   └── jones2023deep.pdf
    ├── summaries/               # LLM-generated summaries
    │   ├── smith2024machine_summary.md
    │   └── jones2023deep_summary.md
    ├── library.json             # JSON index
    └── references.bib           # BibTeX entries

Environment Variables:
    LITERATURE_DEFAULT_LIMIT: Results per source per keyword (default: 25)
    LLM_TEMPERATURE: Summary generation temperature (default: 0.3)
    LLM_SUMMARIZATION_TIMEOUT: Timeout for paper summarization in seconds (default: 600)
    LOG_LEVEL: Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)

Usage:
    python3 literature_search_summarize.py
"""
#!/usr/bin/env python3
"""Literature Search and Summarization Script - Thin Orchestrator.

This thin orchestrator coordinates literature processing workflows:
1. Prompts user for comma-separated keywords
2. Searches arXiv and Semantic Scholar for papers matching any keyword (union)
3. Downloads PDFs and adds to BibTeX library
4. Generates AI summaries for each PDF using local LLM
5. Saves summaries to literature/summaries/ with progress persistence

All business logic is implemented in infrastructure/literature/ modules.

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
    MAX_PARALLEL_SUMMARIES: Parallel summarization workers (default: 2)
    LLM_SUMMARIZATION_TIMEOUT: Timeout for paper summarization (default: 600)
    LOG_LEVEL: Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)

Usage:
    python3 literature_search_summarize.py
"""

import os
import sys
from pathlib import Path
from typing import List
import argparse

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.core.logging_utils import get_logger, log_header
from infrastructure.literature import LiteratureSearch, LiteratureConfig
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.progress import ProgressTracker
from infrastructure.literature.summarizer import PaperSummarizer, SummaryQualityValidator
from infrastructure.llm import (
    LLMClient,
    LLMConfig,
    is_ollama_running,
    select_best_model,
)

# Output paths
FAILED_DOWNLOADS_FILE = Path("literature/failed_downloads.json")
PROGRESS_FILE = Path("literature/summarization_progress.json")
SUMMARIES_DIR = Path("literature/summaries")

logger = get_logger(__name__)

# Default configuration
DEFAULT_LIMIT_PER_KEYWORD = int(os.environ.get("LITERATURE_DEFAULT_LIMIT", "25"))
MAX_PARALLEL_SUMMARIES = int(os.environ.get("MAX_PARALLEL_SUMMARIES", "1"))


def get_user_keywords() -> List[str]:
    """Prompt user for comma-separated keywords.

    Returns:
        List of cleaned keyword strings.
    """
    print("\n" + "=" * 60)
    print("Literature Search and Summarization Tool")
    print("=" * 60)
    print("\nThis tool will:")
    print("  1. Search arXiv and Semantic Scholar for papers")
    print("  2. Download PDFs and add to BibTeX library")
    print("  3. Generate AI summaries for each paper (with progress persistence)")
    print(f"  4. Process up to {MAX_PARALLEL_SUMMARIES} papers in parallel")
    print("\nOutput: literature/pdfs/, literature/summaries/, literature/references.bib")
    print("Resume: literature/summarization_progress.json (created automatically)")
    print("-" * 60)

    user_input = input("\nEnter keywords (comma-separated): ").strip()

    if not user_input:
        logger.warning("No keywords provided")
        return []

    keywords = [kw.strip() for kw in user_input.split(",") if kw.strip()]
    logger.info(f"Parsed {len(keywords)} keyword(s): {keywords}")
    return keywords


def setup_infrastructure() -> LiteratureWorkflow:
    """Set up all infrastructure components for literature processing.

    Returns:
        Configured LiteratureWorkflow instance.

    Raises:
        SystemExit: If setup fails.
    """
    # Check Ollama availability
    log_header("Checking LLM Availability")
    if not is_ollama_running():
        logger.error("Ollama is not running. Please start Ollama first:")
        logger.error("  $ ollama serve")
        sys.exit(1)

    # Select best model
    try:
        model = select_best_model()
        logger.info(f"Using model: {model}")
    except Exception as e:
        logger.error(f"No suitable model found: {e}")
        sys.exit(1)

    # Initialize literature search
    lit_config = LiteratureConfig.from_env()
    logger.info(f"Search limit: {lit_config.default_limit} results per source per keyword")

    # Log Unpaywall status
    if lit_config.use_unpaywall:
        if lit_config.unpaywall_email and lit_config.unpaywall_email != "research@4dresearch.com":
            logger.info(f"Unpaywall enabled with email: {lit_config.unpaywall_email}")
        else:
            logger.info("Unpaywall enabled with default email (consider setting UNPAYWALL_EMAIL for better rate limits)")

    literature_search = LiteratureSearch(lit_config)

    # Initialize LLM client with extended timeout for paper summarization
    llm_config = LLMConfig.from_env()
    llm_config.default_model = model
    llm_config.timeout = float(os.environ.get("LLM_SUMMARIZATION_TIMEOUT", "600"))  # 10 minutes for paper summarization

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


def display_search_results(results: List, keywords: List[str]):
    """Display search results summary to user."""
    print(f"\n{'=' * 70}")
    print(f"Found {len(results)} unique papers:")
    print("-" * 70)


def main():
    """Main execution function for literature search and summarization."""
    parser = argparse.ArgumentParser(description="Literature search and summarization tool")
    parser.add_argument("--resume", choices=["yes", "no"], default="yes",
                       help="Resume previous incomplete run (default: yes)")
    parser.add_argument("--keywords", help="Comma-separated keywords (prompt if not provided)")
    args = parser.parse_args()

    try:
        # Get keywords from command line or prompt
        if args.keywords:
            keywords = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]
            logger.info(f"Using command line keywords: {keywords}")
        else:
            keywords = get_user_keywords()

        if not keywords:
            logger.info("No keywords provided. Exiting.")
            return

        # Set up infrastructure
        log_header("Setting up Literature Processing Infrastructure")
        workflow = setup_infrastructure()

        # Execute search and summarization
        log_header("Executing Literature Search and Summarization")
        logger.info(f"Search keywords: {', '.join(keywords)}")
        logger.info(f"Results per keyword: {DEFAULT_LIMIT_PER_KEYWORD}")
        logger.info(f"Max parallel summaries: {MAX_PARALLEL_SUMMARIES}")
        logger.info(f"Resume previous run: {args.resume}")

        result = workflow.execute_search_and_summarize(
            keywords=keywords,
            limit_per_keyword=DEFAULT_LIMIT_PER_KEYWORD,
            max_parallel_summaries=MAX_PARALLEL_SUMMARIES,
            resume_existing=(args.resume == "yes"),
            interactive=not args.keywords  # Interactive if keywords were prompted, not passed via CLI
        )

        # Display results and log file information
        display_search_results(result.download_results, keywords)

        # Log detailed file information
        log_header("FILE LOCATION SUMMARY")
        logger.info("PDF files downloaded to: literature/pdfs/")
        for download_result in result.download_results:
            if download_result.success and download_result.pdf_path:
                try:
                    file_size = download_result.pdf_path.stat().st_size
                    logger.info(f"  📄 {download_result.pdf_path.name} ({file_size:,} bytes)")
                except Exception as e:
                    logger.warning(f"Could not get file size for {download_result.pdf_path}: {e}")

        logger.info("Summary files saved to: literature/summaries/")
        summaries_created = 0
        for summary_result in result.summarization_results:
            if summary_result.success and summary_result.summary_path:
                try:
                    file_size = summary_result.summary_path.stat().st_size
                    logger.info(f"  📝 {summary_result.summary_path.name} ({file_size:,} bytes)")
                    summaries_created += 1
                except Exception as e:
                    logger.warning(f"Could not get file size for {summary_result.summary_path}: {e}")

        if summaries_created == 0:
            logger.warning("No summary files were created - check summarization process")
        else:
            logger.info(f"Successfully created {summaries_created} summary files")

        # Display final statistics
        stats = workflow.get_workflow_stats(result)
        print(f"\n{'=' * 70}")
        print("WORKFLOW COMPLETED")
        print("=" * 70)
        print(f"Keywords searched: {', '.join(keywords)}")
        print(f"Papers found: {stats['search']['papers_found']}")
        print(f"Papers already downloaded: {result.papers_already_existed}")
        print(f"Papers newly downloaded: {result.papers_newly_downloaded}")
        print(f"Download failures: {result.papers_failed_download}")
        print(f"Papers summarized: {stats['summarization']['successful']}")
        print(f"Success rate: {result.success_rate:.1f}%")
        print(f"Completion rate: {result.completion_rate:.1f}%")

        # Show output locations with file counts and sizes
        print("\nOutput files created:")
        print("- literature/references.bib (BibTeX references)")

        # Count library entries
        try:
            import json
            with open("literature/library.json", "r") as f:
                library_data = json.load(f)
                entry_count = library_data.get("count", 0)
            print(f"- literature/library.json (JSON index with {entry_count} papers)")
        except Exception:
            print("- literature/library.json (JSON index)")

        # Count PDFs
        try:
            pdf_count = len(list(Path("literature/pdfs").glob("*.pdf")))
            pdf_dir = Path("literature/pdfs")
            total_pdf_size = sum(f.stat().st_size for f in pdf_dir.glob("*.pdf") if f.is_file())
            print(f"- literature/pdfs/ ({pdf_count} PDFs, {total_pdf_size:,} bytes total)")
        except Exception:
            print("- literature/pdfs/ (downloaded PDFs)")

        # Count summaries
        try:
            summary_count = len(list(Path("literature/summaries").glob("*.md")))
            summary_dir = Path("literature/summaries")
            total_summary_size = sum(f.stat().st_size for f in summary_dir.glob("*.md") if f.is_file())
            print(f"- literature/summaries/ ({summary_count} summaries, {total_summary_size:,} bytes total)")
        except Exception:
            print("- literature/summaries/ (AI-generated summaries)")

        if result.summaries_failed > 0:
            print(f"- literature/failed_downloads.json ({result.summaries_failed} failed downloads)")
        print("- literature/summarization_progress.json (progress tracking)")

        logger.info("Literature search and summarization completed successfully")

    except Exception as e:
        logger.error(f"Error during literature processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
