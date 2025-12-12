"""Progress tracking for literature search and summarization workflows.

This module provides resumable progress tracking for long-running literature
processing tasks, ensuring that work isn't lost due to interruptions.

Classes:
    ProgressEntry: Individual paper processing status
    SummarizationProgress: Overall workflow progress
    ProgressTracker: Main progress management interface
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.progress import ProgressBar

if TYPE_CHECKING:
    from infrastructure.literature.logging import StructuredLogger

logger = get_logger(__name__)


@dataclass
class ProgressEntry:
    """Progress entry for a single paper summarization.

    Tracks the processing state and metadata for individual papers
    in a literature summarization workflow.

    Attributes:
        citation_key: Unique identifier for the paper.
        pdf_path: Path to the downloaded PDF file.
        status: Current processing status.
        download_attempts: Number of download attempts made.
        summary_attempts: Number of summarization attempts made.
        last_error: Most recent error message if any.
        summary_path: Path to generated summary file if completed.
        download_time: Timestamp when download completed.
        summary_time: Time taken for summarization in seconds.
    """
    citation_key: str
    pdf_path: str
    status: str = "pending"  # "pending", "downloaded", "summarized", "failed"
    download_attempts: int = 0
    summary_attempts: int = 0
    last_error: Optional[str] = None
    summary_path: Optional[str] = None
    download_time: Optional[float] = None
    summary_time: Optional[float] = None

    @property
    def is_completed(self) -> bool:
        """Check if this paper's processing is complete."""
        return self.status in ("summarized", "failed")

    @property
    def is_successful(self) -> bool:
        """Check if this paper was successfully processed."""
        return self.status == "summarized"


@dataclass
class SummarizationProgress:
    """Overall progress tracking for summarization workflow.

    Manages the state of an entire literature summarization run,
    including metadata and collection of individual paper progress.

    Attributes:
        run_id: Unique identifier for this run.
        keywords: Search keywords used for this run.
        total_papers: Total number of papers to process.
        start_time: Unix timestamp when run started.
        last_update: Unix timestamp of last progress update.
        entries: Dictionary of citation_key -> ProgressEntry.
    """
    run_id: str
    keywords: List[str]
    total_papers: int
    start_time: float
    last_update: float
    entries: Dict[str, ProgressEntry] = field(default_factory=dict)

    @property
    def completed_summaries(self) -> int:
        """Number of papers that have completed processing (success or failure)."""
        return sum(1 for entry in self.entries.values() if entry.is_completed)

    @property
    def successful_summaries(self) -> int:
        """Number of successfully summarized papers."""
        return sum(1 for entry in self.entries.values() if entry.is_successful)

    @property
    def failed_summaries(self) -> int:
        """Number of failed summarizations."""
        return sum(1 for entry in self.entries.values() if entry.status == "failed")

    @property
    def pending_summaries(self) -> int:
        """Number of pending summarizations."""
        return sum(1 for entry in self.entries.values()
                  if entry.status == "pending")

    @property
    def completion_percentage(self) -> float:
        """Percentage of papers that are completed (success or failure)."""
        if self.total_papers == 0:
            return 0.0
        completed = sum(1 for entry in self.entries.values() if entry.is_completed)
        return (completed / self.total_papers) * 100.0

    @property
    def success_rate(self) -> float:
        """Percentage of completed papers that were successful."""
        if self.completed_summaries == 0:
            return 0.0
        return (self.successful_summaries / self.completed_summaries) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "keywords": self.keywords,
            "total_papers": self.total_papers,
            "start_time": self.start_time,
            "last_update": self.last_update,
            "entries": {k: {
                "citation_key": v.citation_key,
                "pdf_path": v.pdf_path,
                "status": v.status,
                "download_attempts": v.download_attempts,
                "summary_attempts": v.summary_attempts,
                "last_error": v.last_error,
                "summary_path": v.summary_path,
                "download_time": v.download_time,
                "summary_time": v.summary_time
            } for k, v in self.entries.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SummarizationProgress:
        """Create from dictionary."""
        entries = {}
        for k, v in data.get("entries", {}).items():
            entries[k] = ProgressEntry(**v)
        return cls(
            run_id=data["run_id"],
            keywords=data["keywords"],
            total_papers=data["total_papers"],
            start_time=data["start_time"],
            last_update=data["last_update"],
            entries=entries
        )

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this run."""
        total_time = self.last_update - self.start_time
        return {
            "run_id": self.run_id,
            "keywords": self.keywords,
            "total_papers": self.total_papers,
            "completed": self.completed_summaries,
            "successful": self.successful_summaries,
            "failed": self.failed_summaries,
            "pending": self.pending_summaries,
            "completion_percentage": self.completion_percentage,
            "success_rate": self.success_rate,
            "total_time_seconds": total_time,
            "avg_time_per_paper": total_time / max(1, self.total_papers),
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "last_update": datetime.fromtimestamp(self.last_update).isoformat()
        }


class ProgressTracker:
    """Tracks and persists summarization progress for resumability.

    Provides a high-level interface for managing progress across
    literature processing workflows, with automatic persistence
    to disk for crash recovery.

    Attributes:
        progress_file: Path to JSON file for progress persistence.
        current_progress: Current SummarizationProgress instance.
        structured_logger: Optional structured logger for enhanced logging.
        progress_bars: Dictionary of active progress bars by operation.
    """

    def __init__(
        self,
        progress_file: Path,
        structured_logger: Optional["StructuredLogger"] = None,
        enable_progress_bars: bool = True
    ):
        """Initialize progress tracker.

        Args:
            progress_file: Path to save/load progress data.
            structured_logger: Optional structured logger for enhanced logging.
            enable_progress_bars: Enable visual progress bars.
        """
        self.progress_file = progress_file
        self.current_progress: Optional[SummarizationProgress] = None
        self.structured_logger = structured_logger
        self.enable_progress_bars = enable_progress_bars
        self.progress_bars: Dict[str, ProgressBar] = {}

    def start_new_run(self, keywords: List[str], total_papers: int) -> SummarizationProgress:
        """Start a new summarization run.

        Args:
            keywords: Search keywords used for this run.
            total_papers: Total number of papers to process.

        Returns:
            New SummarizationProgress instance.
        """
        import time
        run_id = f"run_{int(time.time())}"

        self.current_progress = SummarizationProgress(
            run_id=run_id,
            keywords=keywords,
            total_papers=total_papers,
            start_time=time.time(),
            last_update=time.time()
        )

        logger.info(f"Started new summarization run: {run_id}")
        
        if self.structured_logger:
            self.structured_logger.start_operation("summarization_run", f"Run {run_id}: {total_papers} papers")
        
        if self.enable_progress_bars:
            self.progress_bars["summarization"] = ProgressBar(
                total=total_papers,
                task="Summarizing papers"
            )
        
        self.save_progress()
        return self.current_progress

    def load_existing_run(self) -> Optional[SummarizationProgress]:
        """Load existing progress from file.

        Returns:
            Progress object if file exists and is valid, None otherwise.
        """
        if not self.progress_file.exists():
            return None

        try:
            import json
            with open(self.progress_file, 'r') as f:
                data = json.load(f)

            self.current_progress = SummarizationProgress.from_dict(data)
            stats = self.current_progress.get_summary_stats()
            logger.info(f"Loaded existing progress for run: {self.current_progress.run_id}")
            logger.info(f"Progress: {stats['completed']}/{stats['total_papers']} completed "
                       f"({stats['completion_percentage']:.1f}%)")
            return self.current_progress

        except Exception as e:
            logger.warning(f"Failed to load progress file: {e}")
            return None

    def save_progress(self):
        """Save current progress to file."""
        if not self.current_progress:
            return

        try:
            import json
            self.current_progress.last_update = time.time()

            # Ensure directory exists
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.progress_file, 'w') as f:
                json.dump(self.current_progress.to_dict(), f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def update_entry_status(self, citation_key: str, status: str, **kwargs):
        """Update status for a specific entry.

        Args:
            citation_key: Citation key of the paper.
            status: New status ("pending", "downloaded", "summarized", "failed").
            **kwargs: Additional fields to update (last_error, summary_path, etc.).
        """
        if not self.current_progress:
            return

        if citation_key not in self.current_progress.entries:
            logger.warning(f"No progress entry for {citation_key}")
            return

        entry = self.current_progress.entries[citation_key]
        old_status = entry.status
        entry.status = status

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        # Log status changes
        if old_status != status:
            logger.info(f"[{citation_key}] Status: {old_status} -> {status}")
            
            # Update structured logger
            if self.structured_logger:
                metrics = {}
                if "summary_time" in kwargs:
                    metrics["duration_seconds"] = kwargs["summary_time"]
                if "download_time" in kwargs:
                    metrics["download_duration_seconds"] = kwargs["download_time"]
                
                self.structured_logger.log(
                    level="INFO",
                    operation="paper_status_update",
                    message=f"Status changed: {old_status} -> {status}",
                    paper_id=citation_key,
                    metrics=metrics if metrics else None
                )
            
            # Update progress bars
            if self.enable_progress_bars and "summarization" in self.progress_bars:
                completed = self.current_progress.completed_summaries
                total = self.current_progress.total_papers
                self.progress_bars["summarization"].update(completed)
                
                # Log progress percentage
                if total > 0:
                    percentage = (completed / total) * 100
                    logger.debug(f"Progress: {completed}/{total} ({percentage:.1f}%)")

        self.save_progress()

    def add_paper(self, citation_key: str, pdf_path: str):
        """Add a new paper to track.

        Args:
            citation_key: Unique citation key.
            pdf_path: Path to the PDF file.
        """
        if not self.current_progress:
            return

        if citation_key not in self.current_progress.entries:
            self.current_progress.entries[citation_key] = ProgressEntry(
                citation_key=citation_key,
                pdf_path=pdf_path,
                status="pending"
            )
            logger.debug(f"Added progress tracking for paper: {citation_key}")
            self.save_progress()
    
    def finish_progress_bars(self):
        """Finish all active progress bars."""
        for operation, bar in self.progress_bars.items():
            bar.finish()
        self.progress_bars.clear()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary with statistics.
        
        Returns:
            Dictionary with progress statistics.
        """
        if not self.current_progress:
            return {}
        
        stats = self.current_progress.get_summary_stats()
        
        if self.structured_logger:
            stats["log_statistics"] = self.structured_logger.get_statistics()
        
        return stats

    def get_incomplete_papers(self) -> List[str]:
        """Get list of citation keys for papers that haven't been completed.

        Returns:
            List of citation keys for papers still needing processing.
        """
        if not self.current_progress:
            return []

        return [key for key, entry in self.current_progress.entries.items()
                if not entry.is_completed]

    def get_failed_papers(self) -> List[str]:
        """Get list of citation keys for papers that failed processing.

        Returns:
            List of citation keys for failed papers.
        """
        if not self.current_progress:
            return []

        return [key for key, entry in self.current_progress.entries.items()
                if entry.status == "failed"]

    def archive_progress(self) -> Optional[Path]:
        """Archive current progress file with timestamp.

        Returns:
            Path to archived file, or None if no progress to archive.
        """
        if not self.progress_file.exists():
            return None

        archive_name = self.progress_file.with_suffix(
            f".{int(time.time())}.json"
        )
        self.progress_file.rename(archive_name)
        logger.info(f"Archived progress file to: {archive_name}")
        return archive_name
