"""Progress reporting utilities for pipeline operations.

This module provides utilities for displaying progress bars, ETA calculations,
and sub-stage progress tracking for long-running operations.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import sys
import time
from typing import Optional, Callable

from infrastructure.core.logging_utils import (
    get_logger, format_duration, calculate_eta, calculate_eta_ema,
    calculate_eta_with_confidence
)

logger = get_logger(__name__)


class ProgressBar:
    """Simple text-based progress bar for terminal output.
    
    Provides visual progress indication with percentage and optional ETA.
    Supports both item-based and token-based progress tracking.
    
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
        update_interval: float = 0.1,
        use_ema: bool = True
    ):
        """Initialize progress bar.
        
        Args:
            total: Total number of items to process
            task: Task description
            width: Width of progress bar in characters
            show_eta: Whether to show ETA
            update_interval: Minimum time between updates (seconds)
            use_ema: Whether to use exponential moving average for ETA
        """
        self.total = total
        self.task = task
        self.width = width
        self.show_eta = show_eta
        self.update_interval = update_interval
        self.use_ema = use_ema
        
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = 0.0
        self.previous_eta: Optional[float] = None
        
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
            if self.use_ema:
                linear_eta = calculate_eta(elapsed, self.current, self.total)
                if linear_eta is not None:
                    if self.previous_eta is None:
                        self.previous_eta = linear_eta
                    else:
                        self.previous_eta = calculate_eta_ema(
                            elapsed, self.current, self.total,
                            previous_eta=self.previous_eta
                        )
                    status_parts.append(f"ETA: {format_duration(self.previous_eta)}")
            else:
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


class LLMProgressTracker:
    """Progress tracker for LLM operations with token-based progress.
    
    Tracks token generation progress, throughput, and provides real-time updates.
    
    Example:
        >>> tracker = LLMProgressTracker(total_tokens=1000, task="Generating review")
        >>> for chunk in llm_stream:
        ...     tokens = estimate_tokens(chunk)
        ...     tracker.update_tokens(tokens)
        >>> tracker.finish()
    """
    
    def __init__(
        self,
        total_tokens: Optional[int] = None,
        task: str = "LLM Generation",
        show_throughput: bool = True
    ):
        """Initialize LLM progress tracker.
        
        Args:
            total_tokens: Total expected tokens (None for unknown)
            task: Task description
            show_throughput: Whether to show tokens/sec throughput
        """
        self.total_tokens = total_tokens
        self.task = task
        self.show_throughput = show_throughput
        
        self.generated_tokens = 0
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.last_token_count = 0
        self.chunks_received = 0
        
    def update_tokens(self, tokens: int) -> None:
        """Update token count.
        
        Args:
            tokens: Number of tokens generated in this chunk
        """
        self.generated_tokens += tokens
        self.chunks_received += 1
        
        now = time.time()
        elapsed = now - self.start_time
        
        # Calculate throughput
        if elapsed > 0:
            throughput = self.generated_tokens / elapsed
        else:
            throughput = 0.0
        
        # Update display every 0.5 seconds or if we have total and are near completion
        if (now - self.last_update_time >= 0.5) or \
           (self.total_tokens and self.generated_tokens >= self.total_tokens * 0.99):
            self._display(throughput)
            self.last_update_time = now
    
    def _display(self, throughput: float) -> None:
        """Display current progress."""
        elapsed = time.time() - self.start_time
        
        if self.total_tokens:
            percent = (self.generated_tokens * 100) // self.total_tokens if self.total_tokens > 0 else 0
            status = f"  {self.task}: {self.generated_tokens}/{self.total_tokens} tokens ({percent}%)"
            
            # Calculate ETA
            if self.generated_tokens > 0 and throughput > 0:
                remaining_tokens = self.total_tokens - self.generated_tokens
                eta_seconds = remaining_tokens / throughput
                status += f" | ETA: {format_duration(eta_seconds)}"
        else:
            status = f"  {self.task}: {self.generated_tokens} tokens generated"
        
        if self.show_throughput and throughput > 0:
            status += f" | {throughput:.1f} tokens/sec"
        
        # Write to stderr
        if sys.stderr.isatty():
            sys.stderr.write(f"\r{status}")
            sys.stderr.flush()
        else:
            logger.info(status)
    
    def finish(self) -> None:
        """Finish tracking and display final stats."""
        elapsed = time.time() - self.start_time
        throughput = self.generated_tokens / elapsed if elapsed > 0 else 0.0
        
        # Clear progress line
        if sys.stderr.isatty():
            sys.stderr.write("\r" + " " * 80 + "\r")
            sys.stderr.flush()
        
        logger.info(
            f"  ✅ {self.task} complete: {self.generated_tokens} tokens in {format_duration(elapsed)} "
            f"({throughput:.1f} tokens/sec)"
        )


class SubStageProgress:
    """Track progress across multiple sub-stages within a main stage.
    
    Useful for operations with multiple steps (e.g., rendering multiple files).
    Uses EMA for improved ETA accuracy.
    
    Example:
        >>> progress = SubStageProgress(total=5, stage_name="Rendering PDFs")
        >>> for i, file in enumerate(files):
        ...     progress.start_substage(i + 1, file.name)
        ...     render_file(file)
        ...     progress.complete_substage()
    """
    
    def __init__(self, total: int, stage_name: str = "", use_ema: bool = True):
        """Initialize sub-stage progress tracker.
        
        Args:
            total: Total number of sub-stages
            stage_name: Name of the main stage
            use_ema: Whether to use exponential moving average for ETA (default: True)
        """
        self.total = total
        self.stage_name = stage_name
        self.current = 0
        self.start_time = time.time()
        self.substage_start_time = None
        self.current_substage_name = ""
        self.use_ema = use_ema
        self.previous_eta: Optional[float] = None
        self.substage_durations: list[float] = []
    
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
            self.substage_durations.append(duration)
            logger.info(f"    ✅ Completed in {format_duration(duration)}")
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time remaining.
        
        Uses EMA if enabled for smoother estimates.
        
        Returns:
            Estimated seconds remaining, or None if cannot calculate
        """
        if self.current <= 0:
            return None
        
        elapsed = time.time() - self.start_time
        
        if self.use_ema:
            linear_eta = calculate_eta(elapsed, self.current, self.total)
            if linear_eta is None:
                return None
            
            if self.previous_eta is None:
                self.previous_eta = linear_eta
                return linear_eta
            
            # Update EMA
            self.previous_eta = calculate_eta_ema(
                elapsed, self.current, self.total,
                previous_eta=self.previous_eta
            )
            return self.previous_eta
        else:
            return calculate_eta(elapsed, self.current, self.total)
    
    def get_eta_with_confidence(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Get ETA with confidence intervals.
        
        Returns:
            Tuple of (realistic_eta, optimistic_eta, pessimistic_eta)
        """
        if self.current <= 0:
            return None, None, None
        
        elapsed = time.time() - self.start_time
        return calculate_eta_with_confidence(
            elapsed, self.current, self.total,
            item_durations=self.substage_durations if self.substage_durations else None
        )
    
    def log_progress(self) -> None:
        """Log current progress with ETA."""
        percent = (self.current * 100) // self.total if self.total > 0 else 0
        elapsed = time.time() - self.start_time
        eta_seconds = self.get_eta()
        
        status = f"  Progress: {self.current}/{self.total} ({percent}%) - Elapsed: {format_duration(elapsed)}"
        if eta_seconds is not None:
            status += f" | ETA: {format_duration(eta_seconds)}"
        
        logger.info(status)


