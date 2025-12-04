"""Progress reporting utilities for pipeline operations.

This module provides utilities for displaying progress bars, ETA calculations,
and sub-stage progress tracking for long-running operations.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import sys
import time
from typing import Optional

from infrastructure.core.logging_utils import get_logger, format_duration, calculate_eta

logger = get_logger(__name__)


class ProgressBar:
    """Simple text-based progress bar for terminal output.
    
    Provides visual progress indication with percentage and optional ETA.
    
    Example:
        >>> bar = ProgressBar(total=100, task="Processing files")
        >>> for i in range(100):
        ...     bar.update(i + 1)
        >>> bar.finish()
    """
    
    def __init__(
        self,
        total: int,
        task: str = "",
        width: int = 30,
        show_eta: bool = True,
        update_interval: float = 0.1
    ):
        """Initialize progress bar.
        
        Args:
            total: Total number of items to process
            task: Task description
            width: Width of progress bar in characters
            show_eta: Whether to show ETA
            update_interval: Minimum time between updates (seconds)
        """
        self.total = total
        self.task = task
        self.width = width
        self.show_eta = show_eta
        self.update_interval = update_interval
        
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = 0.0
        
    def update(self, value: int, force: bool = False) -> None:
        """Update progress bar.
        
        Args:
            value: Current progress value
            force: Force update even if interval hasn't passed
        """
        self.current = min(value, self.total)
        
        # Throttle updates
        now = time.time()
        if not force and (now - self.last_update_time) < self.update_interval:
            return
        
        self.last_update_time = now
        self._render()
    
    def _render(self) -> None:
        """Render the progress bar to stdout."""
        percent = (self.current * 100) // self.total if self.total > 0 else 0
        filled = (self.current * self.width) // self.total if self.total > 0 else 0
        bar = "█" * filled + "░" * (self.width - filled)
        
        # Build status line
        status_parts = [f"[{bar}] {self.current}/{self.total} ({percent}%)"]
        
        if self.task:
            status_parts.insert(0, self.task)
        
        # Add ETA if enabled
        if self.show_eta and self.current > 0:
            elapsed = time.time() - self.start_time
            eta_seconds = calculate_eta(elapsed, self.current, self.total)
            if eta_seconds is not None:
                status_parts.append(f"ETA: {format_duration(eta_seconds)}")
        
        status = " ".join(status_parts)
        
        # Write to stderr to avoid interfering with stdout
        sys.stderr.write(f"\r  {status}")
        sys.stderr.flush()
    
    def finish(self) -> None:
        """Finish progress bar and print final status."""
        elapsed = time.time() - self.start_time
        self._render()
        sys.stderr.write("\n")  # New line after progress bar
        
        if self.task:
            logger.info(f"  ✅ Completed: {self.task} ({format_duration(elapsed)})")


class SubStageProgress:
    """Track progress across multiple sub-stages within a main stage.
    
    Useful for operations with multiple steps (e.g., rendering multiple files).
    
    Example:
        >>> progress = SubStageProgress(total=5, stage_name="Rendering PDFs")
        >>> for i, file in enumerate(files):
        ...     progress.start_substage(i + 1, file.name)
        ...     render_file(file)
        ...     progress.complete_substage()
    """
    
    def __init__(self, total: int, stage_name: str = ""):
        """Initialize sub-stage progress tracker.
        
        Args:
            total: Total number of sub-stages
            stage_name: Name of the main stage
        """
        self.total = total
        self.stage_name = stage_name
        self.current = 0
        self.start_time = time.time()
        self.substage_start_time = None
        self.current_substage_name = ""
    
    def start_substage(self, substage_num: int, substage_name: str = "") -> None:
        """Start a new sub-stage.
        
        Args:
            substage_num: Sub-stage number (1-based)
            substage_name: Name of the sub-stage
        """
        self.current = substage_num
        self.current_substage_name = substage_name
        self.substage_start_time = time.time()
        
        # Log sub-stage start
        if substage_name:
            logger.info(f"  [{substage_num}/{self.total}] {substage_name}")
        else:
            logger.info(f"  [{substage_num}/{self.total}] Processing...")
    
    def complete_substage(self) -> None:
        """Mark current sub-stage as complete."""
        if self.substage_start_time:
            duration = time.time() - self.substage_start_time
            logger.info(f"    ✅ Completed in {format_duration(duration)}")
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time remaining.
        
        Returns:
            Estimated seconds remaining, or None if cannot calculate
        """
        if self.current <= 0:
            return None
        
        elapsed = time.time() - self.start_time
        return calculate_eta(elapsed, self.current, self.total)
    
    def log_progress(self) -> None:
        """Log current progress with ETA."""
        percent = (self.current * 100) // self.total if self.total > 0 else 0
        elapsed = time.time() - self.start_time
        eta_seconds = self.get_eta()
        
        status = f"  Progress: {self.current}/{self.total} ({percent}%) - Elapsed: {format_duration(elapsed)}"
        if eta_seconds is not None:
            status += f" | ETA: {format_duration(eta_seconds)}"
        
        logger.info(status)


