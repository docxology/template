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
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.core.core import LiteratureSearch, DownloadResult, SearchStatistics
from infrastructure.literature.summarization import SummarizationEngine, SummarizationResult
from infrastructure.literature.summarization.models import SummarizationProgressEvent
from infrastructure.literature.workflow.progress import ProgressTracker, SummarizationProgress

if TYPE_CHECKING:
    from infrastructure.llm.core.client import LLMClient

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
        summarizer: Optional[SummarizationEngine] = None,
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

    def set_summarizer(self, summarizer: SummarizationEngine):
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
        return Path("data/summaries") / f"{citation_key}_summary.md"

    def execute_search_and_summarize(
        self,
        keywords: List[str],
        limit_per_keyword: int = 25,
        max_parallel_summaries: int = 2,
        resume_existing: bool = True,
        interactive: bool = True,
        sources: Optional[List[str]] = None
    ) -> WorkflowResult:
        """Execute complete search and summarize workflow.

        Args:
            keywords: Search keywords.
            limit_per_keyword: Maximum results per keyword.
            max_parallel_summaries: Maximum parallel summarization workers.
            resume_existing: Whether to resume existing progress.
            interactive: Whether in interactive mode.
            sources: Optional list of sources to use. If None, uses all enabled sources.

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
                    logger.info(f"Previous run: {existing_progress.run_id}")
                    logger.info(f"Progress: {existing_progress.completed_summaries}/{existing_progress.total_papers} completed")
                    logger.info(f"Keywords: {', '.join(existing_progress.keywords)}")

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
                        logger.info("Starting new run...")
                        # Archive old progress
                        if self.progress_tracker.progress_file.exists():
                            archive_path = self.progress_tracker.archive_progress()
                            if archive_path:
                                logger.info(f"Archived previous progress to: {archive_path}")

            # Search for papers
            log_header("SEARCHING FOR PAPERS")
            search_results = self._search_papers(keywords, limit_per_keyword, sources=sources)
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
            logger.info(f"Processing {len(downloaded)} papers with up to {max_parallel_summaries} parallel workers")
            
            if self.progress_tracker and self.progress_tracker.current_progress:
                logger.info(
                    f"Progress: {self.progress_tracker.current_progress.completed_summaries}/"
                    f"{self.progress_tracker.current_progress.total_papers} completed "
                    f"({self.progress_tracker.current_progress.completion_percentage:.1f}%)"
                )

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

    def _search_papers(
        self, 
        keywords: List[str], 
        limit_per_keyword: int,
        sources: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search for papers across all keywords.
        
        Args:
            keywords: List of search keywords.
            limit_per_keyword: Maximum results per keyword per source.
            sources: Optional list of sources to use. If None, uses all enabled sources.
        
        Returns:
            Search results and logs comprehensive per-source statistics.
        """
        all_results = []
        all_search_stats: List[SearchStatistics] = []

        for keyword in keywords:
            log_header(f"Searching: '{keyword}'")
            try:
                results, search_stats = self.literature_search.search(
                    keyword, 
                    limit=limit_per_keyword,
                    sources=sources,
                    return_stats=True
                )
                logger.info(f"Found {len(results)} papers for '{keyword}'")
                all_results.extend(results)
                all_search_stats.append(search_stats)
                
                # Display per-source breakdown for this keyword
                self._display_source_breakdown(search_stats, keyword)
                
            except LiteratureSearchError as e:
                logger.error(f"Search failed for '{keyword}': {e}")
                continue

        # Deduplicate results
        unique_results = self.literature_search._deduplicate_results(all_results)
        logger.info(f"Total unique papers after deduplication: {len(unique_results)}")
        
        # Display overall source statistics across all keywords
        if all_search_stats:
            self._display_overall_source_statistics(all_search_stats)

        return unique_results
    
    def _display_source_breakdown(self, search_stats: SearchStatistics, keyword: str):
        """Display per-source breakdown for a single search query."""
        if not search_stats.source_stats:
            return
        
        logger.info("")
        logger.info(f"Source breakdown for '{keyword}':")
        logger.info("-" * 60)
        
        for source_name, stats in sorted(search_stats.source_stats.items()):
            # Health status indicator
            if stats.skipped:
                if not stats.healthy:
                    status = "⏭️  SKIPPED (unhealthy)"
                else:
                    status = "⏭️  SKIPPED (no search support)"
            elif stats.errors > 0:
                status = f"❌ ERROR ({stats.errors} error(s))"
            elif stats.healthy:
                status = "✓ HEALTHY"
            else:
                status = "⚠️  UNHEALTHY"
            
            logger.info(f"  {source_name.upper()}: {status}")
            if not stats.skipped and stats.errors == 0:
                logger.info(f"    • Results: {stats.results_found}")
                if stats.citations_found > 0:
                    logger.info(f"    • Citations: {stats.citations_found}")
                logger.info(f"    • PDFs available: {stats.pdfs_available}")
                logger.info(f"    • DOIs available: {stats.dois_available}")
                logger.info(f"    • Time: {stats.time_taken:.1f}s")
            elif stats.errors > 0:
                logger.info(f"    • Time: {stats.time_taken:.1f}s")
            logger.info("")
    
    def _display_overall_source_statistics(self, all_search_stats: List[SearchStatistics]):
        """Display aggregated statistics across all search queries."""
        # Aggregate statistics across all searches
        aggregated: Dict[str, Dict[str, Any]] = {}
        
        for search_stats in all_search_stats:
            for source_name, stats in search_stats.source_stats.items():
                if source_name not in aggregated:
                    aggregated[source_name] = {
                        "results": 0,
                        "citations": 0,
                        "pdfs": 0,
                        "dois": 0,
                        "time": 0.0,
                        "errors": 0,
                        "skipped": 0,
                        "searches": 0
                    }
                
                agg = aggregated[source_name]
                agg["results"] += stats.results_found
                agg["citations"] += stats.citations_found
                agg["pdfs"] += stats.pdfs_available
                agg["dois"] += stats.dois_available
                agg["time"] += stats.time_taken
                agg["errors"] += stats.errors
                if stats.skipped:
                    agg["skipped"] += 1
                agg["searches"] += 1
        
        if not aggregated:
            return
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("OVERALL SOURCE STATISTICS")
        logger.info("=" * 70)
        
        for source_name in sorted(aggregated.keys()):
            agg = aggregated[source_name]
            # Health indicator
            if agg['errors'] > 0:
                health_indicator = "❌"
            elif agg['skipped'] > 0:
                health_indicator = "⚠️"
            else:
                health_indicator = "✓"
            
            logger.info(f"\n{health_indicator} {source_name.upper()}:")
            logger.info(f"  • Total results: {agg['results']}")
            if agg['citations'] > 0:
                logger.info(f"  • Total citations: {agg['citations']}")
            logger.info(f"  • PDFs available: {agg['pdfs']}")
            logger.info(f"  • DOIs available: {agg['dois']}")
            logger.info(f"  • Total time: {agg['time']:.1f}s")
            if agg['searches'] > 0:
                avg_time = agg['time'] / agg['searches']
                logger.info(f"  • Avg time per search: {avg_time:.1f}s")
            if agg['errors'] > 0:
                logger.info(f"  • Errors: {agg['errors']}")
            if agg['skipped'] > 0:
                logger.info(f"  • Skipped in {agg['skipped']} search(es)")
        
        logger.info("=" * 70)
        logger.info("")

    def _download_papers(self, search_results: List[SearchResult]) -> Tuple[List[Tuple[SearchResult, Path]], List[DownloadResult]]:
        """Download PDFs for search results."""
        downloaded = []
        all_results = []
        start_time = time.time()

        logger.info(f"Starting PDF download for {len(search_results)} papers...")

        for i, result in enumerate(search_results, 1):
            paper_start_time = time.time()
            logger.info(f"[DOWNLOAD {i}/{len(search_results)}] Processing: {result.title[:60]}...")

            # Add to library (BibTeX + JSON index)
            try:
                citation_key = self.literature_search.add_to_library(result)
                logger.debug(f"Added to library: {citation_key}")
            except Exception as e:
                logger.error(f"[DOWNLOAD {i}/{len(search_results)}] Failed to add to library: {e}")
                continue

            # Download PDF with detailed result tracking
            download_result = self.literature_search.download_paper_with_result(result)
            all_results.append(download_result)

            paper_duration = time.time() - paper_start_time

            if download_result.success and download_result.pdf_path:
                # Enhanced success logging with absolute path, file size, and source
                abs_path = download_result.pdf_path.resolve()
                file_size = abs_path.stat().st_size if abs_path.exists() else 0
                source = result.source or "unknown"
                
                if download_result.already_existed:
                    logger.info(f"[DOWNLOAD {i}/{len(search_results)}] ✓ Already exists: {abs_path} ({file_size:,} bytes) [Source: {source}] - {paper_duration:.1f}s")
                else:
                    log_success(f"[DOWNLOAD {i}/{len(search_results)}] ✓ Downloaded: {abs_path} ({file_size:,} bytes) [Source: {source}] - {paper_duration:.1f}s")
                downloaded.append((result, download_result.pdf_path))
            elif download_result.failure_reason == "no_pdf_url":
                source = result.source or "unknown"
                logger.warning(f"[DOWNLOAD {i}/{len(search_results)}] ✗ No PDF URL available: {result.title[:50]}... [Source: {source}] - {paper_duration:.1f}s")
            else:
                # Enhanced failure logging with full context
                source = result.source or "unknown"
                error_msg = download_result.failure_message or "Unknown error"
                urls_attempted = download_result.attempted_urls or []
                expected_path = Path("data/pdfs") / f"{citation_key}.pdf"
                
                logger.error(f"[DOWNLOAD {i}/{len(search_results)}] ✗ Failed: {citation_key}")
                logger.error(f"  Title: {result.title[:80]}...")
                logger.error(f"  Source: {source}")
                logger.error(f"  Failure reason: {download_result.failure_reason or 'unknown'}")
                logger.error(f"  Error: {error_msg}")
                logger.error(f"  Expected path: {expected_path.resolve()}")
                if urls_attempted:
                    logger.error(f"  URLs attempted: {len(urls_attempted)}")
                    for j, url in enumerate(urls_attempted[:3], 1):  # Show first 3
                        logger.error(f"    {j}. {url[:100]}...")
                    if len(urls_attempted) > 3:
                        logger.error(f"    ... and {len(urls_attempted) - 3} more")
                logger.error(f"  Duration: {paper_duration:.1f}s")

        # Calculate comprehensive download statistics
        total_duration = time.time() - start_time
        successful = len([r for r in all_results if r.success])
        already_existed = len([r for r in all_results if r.success and r.already_existed])
        newly_downloaded = len([r for r in all_results if r.success and not r.already_existed])
        failed = len([r for r in all_results if not r.success])

        # Log detailed failure breakdown
        failures = [r for r in all_results if not r.success]
        if failures:
            failure_counts: Dict[str, int] = {}
            for r in failures:
                reason = r.failure_reason or "unknown"
                failure_counts[reason] = failure_counts.get(reason, 0) + 1

            logger.info("Download failure breakdown:")
            for reason, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
                logger.info(f"  • {reason}: {count}")

        # Calculate performance metrics
        avg_time_per_paper = total_duration / len(search_results) if search_results else 0
        success_rate = (successful / len(search_results)) * 100 if search_results else 0

        # Display comprehensive download summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("PDF DOWNLOAD SUMMARY")
        logger.info("=" * 70)
        logger.info(f"  Total papers processed: {len(search_results)}")
        logger.info(f"  ✓ Successfully downloaded: {successful} ({success_rate:.1f}%)")
        logger.info(f"    • Already existed: {already_existed}")
        logger.info(f"    • Newly downloaded: {newly_downloaded}")
        logger.info(f"  ✗ Failed downloads: {failed}")
        logger.info(f"  ⏱️  Total time: {total_duration:.1f}s")
        logger.info(f"  📊 Average time per paper: {avg_time_per_paper:.1f}s")

        if downloaded:
            # Calculate total downloaded size
            total_size = 0
            for _, pdf_path in downloaded:
                try:
                    if pdf_path.exists():
                        total_size += pdf_path.stat().st_size
                except Exception:
                    pass
            if total_size > 0:
                logger.info(f"  💾 Total data downloaded: {total_size:,} bytes")

        logger.info("=" * 70)

        return downloaded, all_results

    def _summarize_papers_parallel(
        self,
        downloaded: List[Tuple[SearchResult, Path]],
        max_workers: int
    ) -> List[SummarizationResult]:
        """Summarize papers using parallel processing."""
        if not self.summarizer:
            raise ValueError("Summarizer not configured")

        start_time = time.time()
        logger.info(f"Summarizing {len(downloaded)} papers")

        # Filter out already summarized papers
        to_process = []
        skipped_results = []

        for result, pdf_path in downloaded:
            citation_key = pdf_path.stem
            summary_path = self._get_summary_path(citation_key)

            # Check if summary file already exists
            if summary_path.exists():
                skipped_result = SummarizationResult(
                    citation_key=citation_key,
                    success=True,
                    summary_path=summary_path,
                    skipped=True
                )
                skipped_results.append(skipped_result)
                if self.progress_tracker:
                    self.progress_tracker.update_entry_status(
                        citation_key, "summarized",
                        summary_path=str(summary_path),
                        summary_attempts=0,
                        summary_time=0.0
                    )
                continue

            # Check progress tracker status
            progress_entry = (self.progress_tracker.current_progress.entries.get(citation_key)
                            if self.progress_tracker.current_progress else None)

            if not (progress_entry and progress_entry.status == "summarized"):
                to_process.append((result, pdf_path))

        # Log processing plan
        total_papers = len(downloaded)
        skipped_count = len(skipped_results)
        to_process_count = len(to_process)

        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} already summarized paper(s)")

        if not to_process:
            logger.info("All papers already summarized, no processing needed")
            return skipped_results

        processing_mode = "parallel" if max_workers > 1 else "sequential"
        logger.info(
            f"Processing {to_process_count} paper(s) ({processing_mode} mode, "
            f"{max_workers} worker(s))"
        )
        
        # Log progress if tracker available
        if self.progress_tracker and self.progress_tracker.current_progress:
            pending = self.progress_tracker.current_progress.pending_summaries
            completed = self.progress_tracker.current_progress.completed_summaries
            total = self.progress_tracker.current_progress.total_papers
            logger.info(f"Overall progress: {completed}/{total} completed, {pending} pending")

        results = skipped_results.copy()

        if max_workers > 1:
            # Parallel processing
            completed_count = len(skipped_results)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_paper = {
                    executor.submit(self._summarize_single_paper, result, pdf_path): (result, pdf_path)
                    for result, pdf_path in to_process
                }

                for future in as_completed(future_to_paper):
                    result, pdf_path = future_to_paper[future]
                    citation_key = pdf_path.stem
                    completed_count += 1

                    try:
                        summary_result = future.result()
                        results.append(summary_result)

                        if summary_result.success:
                            file_size = "?"
                            if summary_result.summary_path and summary_result.summary_path.exists():
                                try:
                                    size_bytes = summary_result.summary_path.stat().st_size
                                    file_size = f"{size_bytes:,}B"
                                except Exception:
                                    pass
                            
                            # Log with progress indicator
                            progress_indicator = f"[{completed_count}/{total_papers}]"
                            logger.info(
                                f"{progress_indicator} ✓ {citation_key} ({file_size}) - "
                                f"{summary_result.generation_time:.1f}s, "
                                f"{summary_result.output_words} words, "
                                f"quality: {summary_result.quality_score:.2f}"
                            )
                            
                            # Update progress tracker if available
                            if self.progress_tracker:
                                self.progress_tracker.update_entry_status(
                                    citation_key, "summarized",
                                    summary_path=str(summary_result.summary_path) if summary_result.summary_path else None,
                                    summary_attempts=summary_result.attempts,
                                    summary_time=summary_result.generation_time
                                )
                        else:
                            progress_indicator = f"[{completed_count}/{total_papers}]"
                            logger.warning(
                                f"{progress_indicator} ✗ {citation_key}: {summary_result.error}"
                            )
                            
                            # Update progress tracker for failures
                            if self.progress_tracker:
                                self.progress_tracker.update_entry_status(
                                    citation_key, "failed",
                                    last_error=summary_result.error,
                                    summary_attempts=summary_result.attempts
                                )

                    except Exception as e:
                        completed_count += 1
                        progress_indicator = f"[{completed_count}/{total_papers}]"
                        logger.error(f"{progress_indicator} Error processing {citation_key}: {e}")
                        results.append(SummarizationResult(
                            citation_key=citation_key,
                            success=False,
                            error=str(e)
                        ))
        else:
            # Sequential processing
            completed_count = len(skipped_results)
            for i, (result, pdf_path) in enumerate(to_process, 1):
                citation_key = pdf_path.stem
                completed_count += 1
                progress_indicator = f"[{completed_count}/{total_papers}]"
                
                logger.info(f"{progress_indicator} Processing {citation_key}...")
                summary_result = self._summarize_single_paper(result, pdf_path)
                results.append(summary_result)

                if summary_result.success:
                    file_size = "?"
                    if summary_result.summary_path and summary_result.summary_path.exists():
                        try:
                            size_bytes = summary_result.summary_path.stat().st_size
                            file_size = f"{size_bytes:,}B"
                        except Exception:
                            pass
                    logger.info(
                        f"{progress_indicator} ✓ {citation_key} ({file_size}) - "
                        f"{summary_result.generation_time:.1f}s, "
                        f"{summary_result.output_words} words, "
                        f"quality: {summary_result.quality_score:.2f}"
                    )
                else:
                    logger.warning(
                        f"{progress_indicator} ✗ {citation_key}: {summary_result.error}"
                    )

        # Calculate statistics
        total_duration = time.time() - start_time
        successful = sum(1 for r in results if r.success and not getattr(r, 'skipped', False))
        failed = sum(1 for r in results if not r.success)
        skipped = sum(1 for r in results if getattr(r, 'skipped', False))

        # Calculate metrics
        avg_time_per_paper = total_duration / to_process_count if to_process_count > 0 else 0
        success_rate = (successful / to_process_count) * 100 if to_process_count > 0 else 0

        # Calculate total summary sizes
        total_summary_size = 0
        summary_count = 0
        for result in results:
            if result.success and result.summary_path and result.summary_path.exists():
                try:
                    total_summary_size += result.summary_path.stat().st_size
                    summary_count += 1
                except Exception:
                    pass

        # Display summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARIZATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Papers processed: {to_process_count}")
        logger.info(f"  ✓ Successful: {successful} ({success_rate:.1f}%)")
        logger.info(f"  Skipped: {skipped}")
        logger.info(f"  ✗ Failed: {failed}")
        logger.info(f"  Time: {total_duration:.1f}s")
        logger.info(f"  Average per paper: {avg_time_per_paper:.1f}s")

        if summary_count > 0:
            avg_summary_size = total_summary_size / summary_count
            logger.info(f"  Total summaries: {summary_count}")
            logger.info(f"  Data generated: {total_summary_size:,} bytes")
            logger.info(f"  Average size: {avg_summary_size:,.0f} bytes")

        logger.info("=" * 60)

        return results

    def _summarize_single_paper(self, result: SearchResult, pdf_path: Path) -> SummarizationResult:
        """Summarize a single paper with progress tracking."""
        citation_key = pdf_path.stem
        summary_path = self._get_summary_path(citation_key)

        # Check if summary already exists (defensive check, should have been filtered earlier)
        if summary_path.exists():
            logger.debug(f"[{citation_key}] Summary already exists, skipping: {summary_path.name}")
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

        # Get paper number for display (if available from progress tracker)
        paper_number = None
        if self.progress_tracker and self.progress_tracker.current_progress:
            # Find paper index in entries
            entries_list = list(self.progress_tracker.current_progress.entries.keys())
            try:
                paper_index = entries_list.index(citation_key)
                paper_number = paper_index + 1
                total_papers = self.progress_tracker.current_progress.total_papers
                paper_number_str = f"[{paper_number}/{total_papers}] "
            except (ValueError, IndexError):
                paper_number_str = ""
        else:
            paper_number_str = ""
        
        # Update progress
        logger.info(f"{paper_number_str}[{citation_key}] Starting summarization for: {result.title[:60]}...")
        if self.progress_tracker:
            self.progress_tracker.update_entry_status(citation_key, "processing")

        # Create progress callback for real-time updates
        def progress_callback(event: SummarizationProgressEvent):
            """Handle progress events and update tracker/logging."""
            # Format stage name for display
            stage_display = {
                "pdf_extraction": "PDF extraction",
                "context_extraction": "Context extraction",
                "draft_generation": "Draft generation",
                "validation": "Validation",
                "refinement": "Refinement"
            }.get(event.stage, event.stage)
            
            # Log progress with formatted output
            if event.status == "started":
                logger.info(f"{paper_number_str}  → {stage_display}: {event.message or 'Starting...'}")
            elif event.status == "in_progress":
                # Handle streaming progress updates
                if event.metadata.get("streaming"):
                    chars = event.metadata.get("chars_received", 0)
                    words = event.metadata.get("words_received", 0)
                    elapsed = event.metadata.get("elapsed_time", 0)
                    logger.info(
                        f"{paper_number_str}  ↻ {stage_display}: "
                        f"Streaming: {chars:,} chars, {words:,} words ({elapsed:.1f}s elapsed)"
                    )
                else:
                    logger.info(f"{paper_number_str}  ↻ {stage_display}: {event.message or 'In progress...'}")
            elif event.status == "completed":
                # Format completion message with metadata
                msg_parts = [event.message or "Completed"]
                if event.metadata:
                    if "time" in event.metadata:
                        msg_parts.append(f"({event.metadata['time']:.2f}s)")
                    elif "elapsed_time" in event.metadata:
                        msg_parts.append(f"({event.metadata['elapsed_time']:.2f}s)")
                    if "words" in event.metadata or "words_received" in event.metadata:
                        words = event.metadata.get("words") or event.metadata.get("words_received", 0)
                        msg_parts.append(f"{words} words")
                    if "chars" in event.metadata or "chars_received" in event.metadata:
                        chars = event.metadata.get("chars") or event.metadata.get("chars_received", 0)
                        msg_parts.append(f"{chars:,} chars")
                    if "score" in event.metadata:
                        msg_parts.append(f"score: {event.metadata['score']:.2f}")
                logger.info(f"{paper_number_str}  ✓ {stage_display}: {' '.join(msg_parts)}")
            elif event.status == "failed":
                logger.error(f"{paper_number_str}  ✗ {stage_display} failed: {event.message or 'Unknown error'}")
        
        # Generate summary with progress callback
        summary_result = self.summarizer.summarize_paper(
            result, 
            pdf_path,
            progress_callback=progress_callback
        )

        # Save summary to disk if summary text exists (always save, even if validation failed)
        if summary_result.summary_text:
            try:
                summary_path = self.summarizer.save_summary(
                    result, summary_result, Path("data/summaries"), pdf_path=pdf_path
                )
                summary_result.summary_path = summary_path
                if not summary_result.success:
                    logger.info(f"[{citation_key}] Summary saved despite validation failure (quality score: {summary_result.quality_score:.2f})")
            except Exception as e:
                logger.error(f"Failed to save summary for {citation_key}: {e}")
                if summary_result.success:
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
        results: List[Tuple[SearchResult, SummarizationResult, Optional[Path]]],
        output_dir: Path
    ) -> List[Path]:
        """Save successful summaries to files.

        Args:
            results: List of (search_result, summarization_result, pdf_path) tuples.
            output_dir: Directory to save summaries.

        Returns:
            List of paths to saved summary files.
        """
        saved_paths = []

        for item in results:
            if len(item) == 3:
                search_result, summary_result, pdf_path = item
            else:
                # Backward compatibility: assume 2-tuple
                search_result, summary_result = item
                pdf_path = None
            
            # Always save if summary_text exists (even if validation failed)
            if summary_result.summary_text:
                try:
                    summary_path = self.summarizer.save_summary(
                        search_result, summary_result, output_dir, pdf_path=pdf_path
                    )
                    saved_paths.append(summary_path)
                    status = "Saved" if summary_result.success else "Saved (validation failed)"
                    log_success(f"{status}: {summary_path.name}")
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
