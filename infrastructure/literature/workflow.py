"""Literature processing workflow orchestration.

This module provides high-level orchestration for literature search,
download, and summarization workflows. It coordinates between different
components while maintaining clean separation of concerns.

Classes:
    LiteratureWorkflow: Main workflow orchestrator
    WorkflowResult: Result container for workflow operations
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING

from infrastructure.core.logging_utils import get_logger, log_success, log_header
from infrastructure.core.exceptions import LiteratureSearchError
from infrastructure.literature.api import SearchResult
from infrastructure.literature.core import LiteratureSearch, DownloadResult
from infrastructure.literature.summarizer import PaperSummarizer, SummarizationResult
from infrastructure.literature.progress import ProgressTracker, SummarizationProgress

if TYPE_CHECKING:
    from infrastructure.llm import LLMClient

logger = get_logger(__name__)


@dataclass
class WorkflowResult:
    """Result of a literature processing workflow.

    Contains comprehensive statistics and results from the entire
    literature search, download, and summarization pipeline.

    Attributes:
        keywords: Search keywords used.
        papers_found: Total papers found in search.
        papers_downloaded: Number of successful downloads.
        papers_failed_download: Number of failed downloads.
        papers_already_existed: Number of papers that already existed.
        papers_newly_downloaded: Number of newly downloaded papers.
        summaries_generated: Number of successful summaries.
        summaries_failed: Number of failed summaries.
        summaries_skipped: Number of summaries skipped (already exist).
        total_time: Total workflow execution time.
        download_results: Detailed download results.
        summarization_results: Detailed summarization results.
        progress: Final progress state.
    """
    keywords: List[str]
    papers_found: int = 0
    papers_downloaded: int = 0
    papers_failed_download: int = 0
    papers_already_existed: int = 0
    papers_newly_downloaded: int = 0
    summaries_generated: int = 0
    summaries_failed: int = 0
    summaries_skipped: int = 0
    total_time: float = 0.0
    download_results: List[DownloadResult] = field(default_factory=list)
    summarization_results: List[SummarizationResult] = field(default_factory=list)
    progress: Optional[SummarizationProgress] = None

    @property
    def success_rate(self) -> float:
        """Overall success rate across download and summarization."""
        total_processed = self.papers_downloaded + self.papers_failed_download
        if total_processed == 0:
            return 0.0

        successful_operations = self.summaries_generated
        return (successful_operations / total_processed) * 100.0

    @property
    def completion_rate(self) -> float:
        """Percentage of papers that completed the full pipeline."""
        if self.papers_found == 0:
            return 0.0
        return (self.summaries_generated / self.papers_found) * 100.0


class LiteratureWorkflow:
    """High-level orchestrator for literature processing workflows.

    Coordinates the complete literature processing pipeline:
    1. Search for papers
    2. Download PDFs with fallback strategies
    3. Generate AI summaries with quality validation
    4. Track progress and handle resumability

    This class follows the thin orchestrator pattern - it coordinates
    between specialized components but doesn't contain business logic.

    Attributes:
        literature_search: Literature search and download interface.
        summarizer: Paper summarization interface.
        progress_tracker: Progress persistence interface.
    """

    def __init__(
        self,
        literature_search: LiteratureSearch,
        summarizer: Optional[PaperSummarizer] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ):
        """Initialize literature workflow.

        Args:
            literature_search: Configured literature search instance.
            summarizer: Optional paper summarizer (can be set later).
            progress_tracker: Optional progress tracker (can be set later).
        """
        self.literature_search = literature_search
        self.summarizer = summarizer
        self.progress_tracker = progress_tracker

    def set_summarizer(self, summarizer: PaperSummarizer):
        """Set the summarizer for this workflow."""
        self.summarizer = summarizer

    def set_progress_tracker(self, progress_tracker: ProgressTracker):
        """Set the progress tracker for this workflow."""
        self.progress_tracker = progress_tracker

    def _get_summary_path(self, citation_key: str) -> Path:
        """Get expected summary file path for a citation key.
        
        Args:
            citation_key: Citation key for the paper.
            
        Returns:
            Path to expected summary file.
        """
        return Path("literature/summaries") / f"{citation_key}_summary.md"

    def execute_search_and_summarize(
        self,
        keywords: List[str],
        limit_per_keyword: int = 25,
        max_parallel_summaries: int = 2,
        resume_existing: bool = True,
        interactive: bool = True
    ) -> WorkflowResult:
        """Execute complete search and summarize workflow.

        Args:
            keywords: Search keywords.
            limit_per_keyword: Maximum results per keyword.
            max_parallel_summaries: Maximum parallel summarization workers.
            resume_existing: Whether to resume existing progress.

        Returns:
            WorkflowResult with complete execution statistics.
        """
        start_time = time.time()
        result = WorkflowResult(keywords=keywords)

        try:
            # Check for existing progress
            if resume_existing and self.progress_tracker:
                existing_progress = self.progress_tracker.load_existing_run()
                if existing_progress:
                    log_header("RESUME EXISTING RUN")
                    print(f"Previous run: {existing_progress.run_id}")
                    print(f"Progress: {existing_progress.completed_summaries}/{existing_progress.total_papers} completed")
                    print(f"Keywords: {', '.join(existing_progress.keywords)}")

                    if interactive:
                        resume_choice = input("\nResume previous run? [Y/n]: ").strip().lower()
                        should_resume = resume_choice in ('', 'y', 'yes')
                    else:
                        # In non-interactive mode, always resume if resume_existing is True
                        should_resume = True
                        logger.info("Resuming previous run automatically (non-interactive mode)")

                    if should_resume:
                        self.progress_tracker.current_progress = existing_progress
                        result.progress = existing_progress
                    else:
                        print("Starting new run...")
                        # Archive old progress
                        if self.progress_tracker.progress_file.exists():
                            archive_path = self.progress_tracker.archive_progress()
                            if archive_path:
                                print(f"Archived previous progress to: {archive_path}")

            # Search for papers
            log_header("SEARCHING FOR PAPERS")
            search_results = self._search_papers(keywords, limit_per_keyword)
            result.papers_found = len(search_results)

            if not search_results:
                logger.warning("No papers found for the given keywords")
                result.total_time = time.time() - start_time
                return result

            # Download papers
            log_header("DOWNLOADING PAPERS")
            downloaded, download_results = self._download_papers(search_results)
            result.papers_downloaded = len(downloaded)
            result.papers_failed_download = len([r for r in download_results if not r.success])
            result.papers_already_existed = len([r for r in download_results if r.success and r.already_existed])
            result.papers_newly_downloaded = len([r for r in download_results if r.success and not r.already_existed])
            result.download_results = download_results

            if not downloaded:
                logger.warning("No papers were successfully downloaded")
                result.total_time = time.time() - start_time
                return result

            # Initialize progress tracking for new run
            if not self.progress_tracker.current_progress:
                self.progress_tracker.start_new_run(keywords, len(downloaded))
                result.progress = self.progress_tracker.current_progress

            # Add downloaded papers to progress tracking
            for search_result, pdf_path in downloaded:
                citation_key = pdf_path.stem
                self.progress_tracker.add_paper(citation_key, str(pdf_path))
                self.progress_tracker.update_entry_status(citation_key, "downloaded", download_time=time.time())

            # Generate summaries
            log_header("GENERATING SUMMARIES")
            logger.info(f"Using up to {max_parallel_summaries} parallel workers")

            summarization_results = self._summarize_papers_parallel(
                downloaded, max_parallel_summaries
            )

            result.summarization_results = summarization_results
            result.summaries_generated = sum(1 for r in summarization_results if r.success and not getattr(r, 'skipped', False))
            result.summaries_failed = sum(1 for r in summarization_results if not r.success)
            result.summaries_skipped = sum(1 for r in summarization_results if getattr(r, 'skipped', False))

            # Final progress save
            if self.progress_tracker:
                self.progress_tracker.save_progress()

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            result.total_time = time.time() - start_time
            raise

        result.total_time = time.time() - start_time
        return result

    def _search_papers(self, keywords: List[str], limit_per_keyword: int) -> List[SearchResult]:
        """Search for papers across all keywords."""
        all_results = []

        for keyword in keywords:
            log_header(f"Searching: '{keyword}'")
            try:
                results = self.literature_search.search(keyword, limit=limit_per_keyword)
                logger.info(f"Found {len(results)} papers for '{keyword}'")
                all_results.extend(results)
            except LiteratureSearchError as e:
                logger.error(f"Search failed for '{keyword}': {e}")
                continue

        # Deduplicate results
        unique_results = self.literature_search._deduplicate_results(all_results)
        logger.info(f"Total unique papers after deduplication: {len(unique_results)}")

        return unique_results

    def _download_papers(self, search_results: List[SearchResult]) -> Tuple[List[Tuple[SearchResult, Path]], List[DownloadResult]]:
        """Download PDFs for search results."""
        downloaded = []
        all_results = []

        for i, result in enumerate(search_results, 1):
            logger.info(f"[{i}/{len(search_results)}] {result.title[:60]}...")

            # Add to library (BibTeX + JSON index)
            try:
                citation_key = self.literature_search.add_to_library(result)
            except Exception as e:
                logger.error(f"Failed to add to library: {e}")
                continue

            # Download PDF
            download_result = self.literature_search.download_paper_with_result(result)
            all_results.append(download_result)

            if download_result.success and download_result.pdf_path:
                log_success(f"Downloaded: {download_result.pdf_path.name}")
                downloaded.append((result, download_result.pdf_path))
            elif download_result.failure_reason == "no_pdf_url":
                logger.warning(f"No PDF URL available for: {result.title[:50]}...")
            else:
                # Truncate long error messages (especially URLs)
                error_msg = download_result.failure_message or "Unknown error"
                if len(error_msg) > 200:
                    error_msg = error_msg[:197] + "..."
                logger.error(f"Failed to download PDF ({download_result.failure_reason}): {error_msg}")

        # Log download summary
        failures = [r for r in all_results if not r.success]
        if failures:
            failure_counts: Dict[str, int] = {}
            for r in failures:
                reason = r.failure_reason or "unknown"
                failure_counts[reason] = failure_counts.get(reason, 0) + 1

            logger.info("Download failures by reason:")
            for reason, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
                logger.info(f"  - {reason}: {count}")

        # Display download summary
        already_existed = len([r for r in all_results if r.success and r.already_existed])
        newly_downloaded = len([r for r in all_results if r.success and not r.already_existed])
        failed = len([r for r in all_results if not r.success])

        logger.info("")
        logger.info("=" * 50)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 50)
        logger.info(f"  Already downloaded: {already_existed}")
        logger.info(f"  Newly downloaded: {newly_downloaded}")
        logger.info(f"  Failed: {failed}")
        logger.info("=" * 50)
        logger.info(f"Successfully downloaded {len(downloaded)} of {len(search_results)} papers")
        return downloaded, all_results

    def _summarize_papers_parallel(
        self,
        downloaded: List[Tuple[SearchResult, Path]],
        max_workers: int
    ) -> List[SummarizationResult]:
        """Summarize papers using parallel processing."""
        if not self.summarizer:
            raise ValueError("Summarizer not configured")

        # Filter out already summarized papers (check both progress tracker and file existence)
        to_process = []
        skipped_results = []
        for result, pdf_path in downloaded:
            citation_key = pdf_path.stem
            summary_path = self._get_summary_path(citation_key)
            
            # Check if summary file already exists (source of truth)
            if summary_path.exists():
                logger.debug(f"Summary already exists, skipping: {summary_path.name}")
                # Create a success result for the existing summary
                skipped_result = SummarizationResult(
                    citation_key=citation_key,
                    success=True,
                    summary_path=summary_path,
                    skipped=True
                )
                skipped_results.append(skipped_result)
                # Update progress tracker if available
                if self.progress_tracker:
                    self.progress_tracker.update_entry_status(
                        citation_key, "summarized",
                        summary_path=str(summary_path),
                        summary_attempts=0,
                        summary_time=0.0
                    )
                continue
            
            # Also check progress tracker status
            progress_entry = (self.progress_tracker.current_progress.entries.get(citation_key)
                            if self.progress_tracker.current_progress else None)

            if not (progress_entry and progress_entry.status == "summarized"):
                to_process.append((result, pdf_path))

        if skipped_results:
            logger.info(f"Skipped {len(skipped_results)} existing summaries")

        if not to_process:
            if skipped_results:
                logger.info("All papers already have summaries")
            else:
                logger.info("All papers already summarized")
            return skipped_results

        logger.info(f"Processing {len(to_process)} papers with up to {max_workers} parallel workers")

        results = skipped_results.copy()

        if max_workers > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_paper = {
                    executor.submit(self._summarize_single_paper, result, pdf_path): (result, pdf_path)
                    for result, pdf_path in to_process
                }

                for future in as_completed(future_to_paper):
                    result, pdf_path = future_to_paper[future]
                    try:
                        summary_result = future.result()
                        results.append(summary_result)
                        if summary_result.success:
                            logger.info(f"Completed: {pdf_path.name}")
                        else:
                            logger.warning(f"Failed: {pdf_path.name} - {summary_result.error}")
                    except Exception as e:
                        logger.error(f"Unexpected error processing {pdf_path.name}: {e}")
                        citation_key = pdf_path.stem
                        results.append(SummarizationResult(
                            citation_key=citation_key,
                            success=False,
                            error=str(e)
                        ))
        else:
            # Sequential processing
            for result, pdf_path in to_process:
                logger.info(f"Summarizing: {pdf_path.name}")
                summary_result = self._summarize_single_paper(result, pdf_path)
                results.append(summary_result)

        return results

    def _summarize_single_paper(self, result: SearchResult, pdf_path: Path) -> SummarizationResult:
        """Summarize a single paper with progress tracking."""
        citation_key = pdf_path.stem
        summary_path = self._get_summary_path(citation_key)

        # Check if summary already exists (defensive check, should have been filtered earlier)
        if summary_path.exists():
            logger.info(f"Summary already exists, skipping: {summary_path.name}")
            # Return success result with existing path
            skipped_result = SummarizationResult(
                citation_key=citation_key,
                success=True,
                summary_path=summary_path,
                skipped=True
            )
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.update_entry_status(
                    citation_key, "summarized",
                    summary_path=str(summary_path),
                    summary_attempts=0,
                    summary_time=0.0
                )
            return skipped_result

        # Update progress
        if self.progress_tracker:
            self.progress_tracker.update_entry_status(citation_key, "processing")

        # Generate summary
        summary_result = self.summarizer.summarize_paper(result, pdf_path)

        # Save summary to disk if successful
        if summary_result.success and summary_result.summary_text:
            try:
                summary_path = self.summarizer.save_summary(
                    result, summary_result, Path("literature/summaries")
                )
                summary_result.summary_path = summary_path
            except Exception as e:
                logger.error(f"Failed to save summary for {citation_key}: {e}")
                summary_result.success = False
                summary_result.error = f"Summary generation succeeded but save failed: {e}"

        # Update progress based on result
        if self.progress_tracker:
            if summary_result.success:
                self.progress_tracker.update_entry_status(
                    citation_key, "summarized",
                    summary_path=str(summary_result.summary_path) if summary_result.summary_path else None,
                    summary_attempts=summary_result.attempts,
                    summary_time=summary_result.generation_time
                )
            else:
                self.progress_tracker.update_entry_status(
                    citation_key, "failed",
                    last_error=summary_result.error,
                    summary_attempts=summary_result.attempts
                )

        return summary_result

    def save_summaries(
        self,
        results: List[Tuple[SearchResult, SummarizationResult]],
        output_dir: Path
    ) -> List[Path]:
        """Save successful summaries to files.

        Args:
            results: List of (search_result, summarization_result) tuples.
            output_dir: Directory to save summaries.

        Returns:
            List of paths to saved summary files.
        """
        saved_paths = []

        for search_result, summary_result in results:
            if summary_result.success and summary_result.summary_text:
                try:
                    summary_path = self.summarizer.save_summary(
                        search_result, summary_result, output_dir
                    )
                    saved_paths.append(summary_path)
                    log_success(f"Saved: {summary_path.name}")
                except Exception as e:
                    logger.error(f"Failed to save summary for {summary_result.citation_key}: {e}")

        return saved_paths

    def get_workflow_stats(self, result: WorkflowResult) -> Dict[str, Any]:
        """Get comprehensive workflow statistics."""
        return {
            "search": {
                "keywords": result.keywords,
                "papers_found": result.papers_found,
            },
            "downloads": {
                "successful": result.papers_downloaded,
                "failed": result.papers_failed_download,
                "success_rate": (result.papers_downloaded / max(1, result.papers_found)) * 100.0,
            },
            "summarization": {
                "successful": result.summaries_generated,
                "skipped": result.summaries_skipped,
                "failed": result.summaries_failed,
                "success_rate": result.success_rate,
                "completion_rate": result.completion_rate,
            },
            "timing": {
                "total_time_seconds": result.total_time,
                "avg_time_per_paper": result.total_time / max(1, result.papers_found),
            },
            "progress": result.progress.get_summary_stats() if result.progress else None,
        }
