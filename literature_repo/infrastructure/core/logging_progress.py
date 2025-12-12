"""Progress bars, spinners, and ETA calculations for logging."""
from __future__ import annotations

import logging
import sys
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator, Optional

# Import at function level to avoid circular imports
# from infrastructure.core.logging_utils import get_logger, log_success
# from infrastructure.core.logging_helpers import format_duration


def calculate_eta(
    elapsed_time: float,
    completed_items: int,
    total_items: int
) -> Optional[float]:
    """Calculate estimated time remaining based on current progress.
    
    Uses simple linear calculation for basic ETA estimation.
    
    Args:
        elapsed_time: Time elapsed so far in seconds
        completed_items: Number of items completed
        total_items: Total number of items
        
    Returns:
        Estimated time remaining in seconds, or None if cannot calculate
        
    Example:
        >>> calculate_eta(30.0, 3, 10)
        70.0  # 30s for 3 items = 10s/item, 7 remaining = 70s
    """
    if completed_items <= 0 or total_items <= 0:
        return None
    
    if completed_items >= total_items:
        return 0.0
    
    avg_time_per_item = elapsed_time / completed_items
    remaining_items = total_items - completed_items
    return avg_time_per_item * remaining_items


def calculate_eta_ema(
    elapsed_time: float,
    completed_items: int,
    total_items: int,
    previous_eta: Optional[float] = None,
    alpha: float = 0.3
) -> Optional[float]:
    """Calculate ETA using exponential moving average for better accuracy.
    
    EMA provides smoother estimates that adapt to changing performance,
    reducing the impact of outliers (very fast or slow items).
    
    Args:
        elapsed_time: Time elapsed so far in seconds
        completed_items: Number of items completed
        total_items: Total number of items
        previous_eta: Previous ETA estimate (for EMA calculation)
        alpha: Smoothing factor (0-1), higher = more responsive to recent data
        
    Returns:
        Estimated time remaining in seconds, or None if cannot calculate
        
    Example:
        >>> # First calculation (no previous ETA)
        >>> eta1 = calculate_eta_ema(30.0, 3, 10)
        >>> # Subsequent calculation with EMA smoothing
        >>> eta2 = calculate_eta_ema(40.0, 4, 10, previous_eta=eta1)
    """
    if completed_items <= 0 or total_items <= 0:
        return None
    
    if completed_items >= total_items:
        return 0.0
    
    # Calculate linear ETA
    linear_eta = calculate_eta(elapsed_time, completed_items, total_items)
    if linear_eta is None:
        return None
    
    # If no previous ETA, return linear estimate
    if previous_eta is None:
        return linear_eta
    
    # Apply EMA: new_eta = alpha * linear_eta + (1 - alpha) * previous_eta
    ema_eta = alpha * linear_eta + (1 - alpha) * previous_eta
    
    # Ensure ETA is non-negative
    return max(0.0, ema_eta)


def calculate_eta_with_confidence(
    elapsed_time: float,
    completed_items: int,
    total_items: int,
    item_durations: Optional[list[float]] = None
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate ETA with confidence intervals (optimistic/pessimistic).
    
    Provides three estimates:
    - Optimistic: Based on fastest items
    - Realistic: Based on average
    - Pessimistic: Based on slowest items
    
    Args:
        elapsed_time: Time elapsed so far in seconds
        completed_items: Number of items completed
        total_items: Total number of items
        item_durations: Optional list of individual item durations for better estimates
        
    Returns:
        Tuple of (optimistic_eta, realistic_eta, pessimistic_eta)
        
    Example:
        >>> calculate_eta_with_confidence(30.0, 3, 10, [8.0, 10.0, 12.0])
        (56.0, 70.0, 84.0)  # Based on min/avg/max durations
    """
    if completed_items <= 0 or total_items <= 0:
        return (None, None, None)
    
    if completed_items >= total_items:
        return (0.0, 0.0, 0.0)
    
    remaining_items = total_items - completed_items
    
    if item_durations and len(item_durations) > 0:
        # Use actual item durations for better estimates
        min_duration = min(item_durations)
        avg_duration = sum(item_durations) / len(item_durations)
        max_duration = max(item_durations)
        
        optimistic = min_duration * remaining_items
        realistic = avg_duration * remaining_items
        pessimistic = max_duration * remaining_items
    else:
        # Fall back to simple linear calculation
        avg_time_per_item = elapsed_time / completed_items
        optimistic = avg_time_per_item * 0.8 * remaining_items  # 20% faster
        realistic = avg_time_per_item * remaining_items
        pessimistic = avg_time_per_item * 1.2 * remaining_items  # 20% slower
    
    return (optimistic, realistic, pessimistic)


def log_progress_bar(
    current: int,
    total: int,
    message: str = "Progress",
    logger: Optional[logging.Logger] = None,
    bar_width: int = 40
) -> None:
    """Display a progress bar in the console.
    
    Args:
        current: Current progress value
        total: Total progress value
        message: Progress message
        logger: Logger instance (optional)
        bar_width: Width of progress bar in characters
        
    Example:
        >>> log_progress_bar(3, 10, "Processing files")
        Processing files: [████████░░░░░░░░░░░░] 30%
    """
    if logger is None:
        from infrastructure.core.logging_utils import get_logger
        logger = get_logger(__name__)
    
    if total == 0:
        logger.info(f"{message}: 0/0 (0%)")
        return
    
    percent = (current * 100) // total
    filled = int((current / total) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    logger.info(f"{message}: [{bar}] {percent}%")


class Spinner:
    """Animated spinner for long-running operations.
    
    Provides visual feedback during operations that don't have discrete progress.
    """
    
    SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    
    def __init__(
        self,
        message: str = "Processing...",
        stream: Any = None,
        delay: float = 0.1
    ):
        """Initialize spinner.
        
        Args:
            message: Message to display with spinner
            stream: Output stream (defaults to stderr)
            delay: Delay between spinner updates in seconds
        """
        self.message = message
        self.stream = stream or sys.stderr
        self.delay = delay
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.idx = 0
    
    def start(self) -> None:
        """Start the spinner animation."""
        if not self.stream.isatty():
            # Not a TTY - just print message once
            self.stream.write(f"{self.message}\n")
            self.stream.flush()
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop the spinner animation.
        
        Args:
            final_message: Optional message to display when stopping
        """
        if self.thread is None:
            # No thread was started (non-TTY case), but still write final_message if provided
            if final_message:
                self.stream.write(f"{final_message}\n")
                self.stream.flush()
            return
        
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        # Clear spinner line
        if self.stream.isatty():
            self.stream.write("\r" + " " * 80 + "\r")
            self.stream.flush()
        
        if final_message:
            self.stream.write(f"{final_message}\n")
            self.stream.flush()
    
    def _spin(self) -> None:
        """Internal spinner animation loop."""
        while not self.stop_event.is_set():
            char = self.SPINNER_CHARS[self.idx % len(self.SPINNER_CHARS)]
            self.stream.write(f"\r{char} {self.message}")
            self.stream.flush()
            self.idx += 1
            self.stop_event.wait(self.delay)
    
    def __enter__(self) -> 'Spinner':
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


@contextmanager
def log_with_spinner(
    message: str,
    logger: Optional[logging.Logger] = None,
    final_message: Optional[str] = None
) -> Iterator[None]:
    """Context manager for operations with spinner indicator.
    
    Args:
        message: Message to display with spinner
        logger: Logger instance (optional, for final message)
        final_message: Message to display when done (uses logger if provided)
        
    Yields:
        None
        
    Example:
        >>> with log_with_spinner("Loading model...", logger):
        ...     load_model()
        ⠋ Loading model...
        ✅ Model loaded
    """
    spinner = Spinner(message)
    spinner.start()
    
    try:
        yield
        if final_message:
            spinner.stop(final_message)
        elif logger:
            spinner.stop()
            from infrastructure.core.logging_utils import log_success
            log_success(message.replace("...", " complete"), logger)
        else:
            spinner.stop()
    except Exception as e:
        spinner.stop()
        if logger:
            logger.error(f"{message} failed: {e}")
        raise


class StreamingProgress:
    """Real-time progress indicator for streaming operations.
    
    Updates progress in-place using carriage returns.
    """
    
    def __init__(
        self,
        total: int,
        message: str = "Progress",
        stream: Any = None,
        update_interval: float = 0.5
    ):
        """Initialize streaming progress.
        
        Args:
            total: Total number of items
            message: Progress message
            stream: Output stream (defaults to stderr)
            update_interval: Minimum time between updates (seconds)
        """
        self.total = total
        self.message = message
        self.stream = stream or sys.stderr
        self.update_interval = update_interval
        self.current = 0
        self.last_update = 0.0
        self.start_time = time.time()
    
    def update(self, increment: int = 1, custom_message: Optional[str] = None) -> None:
        """Update progress.
        
        Args:
            increment: Number of items completed
            custom_message: Optional custom message to display
        """
        self.current = min(self.current + increment, self.total)
        now = time.time()
        
        # Throttle updates
        if now - self.last_update < self.update_interval:
            return
        
        self.last_update = now
        self._display(custom_message)
    
    def set(self, value: int, custom_message: Optional[str] = None) -> None:
        """Set progress to specific value.
        
        Args:
            value: Current progress value
            custom_message: Optional custom message to display
        """
        self.current = min(value, self.total)
        self._display(custom_message)
    
    def _display(self, custom_message: Optional[str] = None) -> None:
        """Display current progress."""
        if not self.stream.isatty():
            return
        
        percent = (self.current * 100) // self.total if self.total > 0 else 0
        elapsed = time.time() - self.start_time
        
        # Calculate ETA
        eta_str = ""
        if self.current > 0 and elapsed > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            from infrastructure.core.logging_helpers import format_duration
            eta_str = f" | ETA: {format_duration(remaining)}"
        
        message = custom_message or self.message
        status = f"\r{message}: {self.current}/{self.total} ({percent}%){eta_str}"
        
        # Pad to clear previous line
        status = status.ljust(80)
        self.stream.write(status)
        self.stream.flush()
    
    def finish(self, final_message: Optional[str] = None) -> None:
        """Finish progress display.
        
        Args:
            final_message: Optional final message to display
        """
        if self.stream.isatty():
            self.stream.write("\r" + " " * 80 + "\r")
            self.stream.flush()
        
        if final_message:
            self.stream.write(f"{final_message}\n")
            self.stream.flush()
        elif self.stream.isatty():
            # Show completion
            elapsed = time.time() - self.start_time
            self.stream.write(f"✅ {self.message}: {self.current}/{self.total} complete ({elapsed:.1f}s)\n")
            self.stream.flush()


def log_progress_streaming(
    current: int,
    total: int,
    message: str = "Progress",
    logger: Optional[logging.Logger] = None,
    show_eta: bool = True
) -> None:
    """Log streaming progress with real-time updates.
    
    Args:
        current: Current progress value
        total: Total progress value
        message: Progress message
        logger: Logger instance (optional)
        show_eta: Whether to show estimated time remaining
    """
    from infrastructure.core.logging_utils import log_progress
    
    if not sys.stderr.isatty():
        # Not a TTY - use regular progress logging
        log_progress(current, total, message, logger)
        return
    
    percent = (current * 100) // total if total > 0 else 0
    status = f"\r{message}: {current}/{total} ({percent}%)"
    
    if show_eta and current > 0:
        # Simple ETA calculation would require tracking start time
        # For now, just show percentage
        pass
    
    sys.stderr.write(status.ljust(80))
    sys.stderr.flush()
    
    if current >= total:
        sys.stderr.write("\n")
        sys.stderr.flush()


def log_stage_with_eta(
    stage: str,
    current: int,
    total: int,
    elapsed_time: float,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log stage progress with ETA calculation.
    
    Args:
        stage: Stage name
        current: Current item number
        total: Total items
        elapsed_time: Time elapsed so far
        logger: Logger instance (optional)
    """
    if logger is None:
        from infrastructure.core.logging_utils import get_logger
        logger = get_logger(__name__)
    
    from infrastructure.core.logging_helpers import format_duration
    
    eta = calculate_eta(elapsed_time, current, total)
    if eta is not None:
        eta_str = format_duration(eta)
        logger.info(f"{stage} [{current}/{total}] - ETA: {eta_str}")
    else:
        logger.info(f"{stage} [{current}/{total}]")


def log_resource_usage(
    cpu_percent: Optional[float] = None,
    memory_mb: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log current resource usage.
    
    Args:
        cpu_percent: CPU usage percentage (optional)
        memory_mb: Memory usage in MB (optional)
        logger: Logger instance (optional)
    """
    if logger is None:
        from infrastructure.core.logging_utils import get_logger
        logger = get_logger(__name__)
    
    parts = []
    if cpu_percent is not None:
        parts.append(f"CPU: {cpu_percent:.1f}%")
    if memory_mb is not None:
        parts.append(f"Memory: {memory_mb:.1f} MB")
    
    if parts:
        logger.debug(f"Resource usage: {', '.join(parts)}")

