"""Progress bars, spinners, and ETA calculations for logging."""

from __future__ import annotations

import logging
import sys
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

from infrastructure.core.eta import (
    calculate_eta,
    calculate_eta_ema,
    calculate_eta_with_confidence,
)
from infrastructure.core.logging_constants import EMOJIS, get_emoji_enabled
from infrastructure.core.logging_helpers import format_duration

__all__ = [
    "calculate_eta",
    "calculate_eta_ema",
    "calculate_eta_with_confidence",
]



def log_progress_bar(
    current: int,
    total: int,
    message: str = "Progress",
    logger: logging.Logger | None = None,
    bar_width: int = 40,
) -> None:
    """Log a filled/empty block progress bar at the given percentage."""
    if logger is None:
        logger = logging.getLogger(__name__)

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

    def __init__(self, message: str = "Processing...", stream: Any = None, delay: float = 0.1):
        """Initialize animated spinner."""
        self.message = message
        self.stream = stream or sys.stderr
        self.delay = delay
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
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

    def stop(self, final_message: str | None = None) -> None:
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

    def __enter__(self) -> "Spinner":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


@contextmanager
def log_with_spinner(
    message: str,
    logger: logging.Logger | None = None,
    final_message: str | None = None,
) -> Iterator[None]:
    """Context manager that shows a spinner during the block and logs completion."""
    spinner = Spinner(message)
    spinner.start()

    try:
        yield
        if final_message:
            spinner.stop(final_message)
        elif logger:
            spinner.stop()
            success_msg = message.replace("...", " complete")
            emoji = EMOJIS["success"] if get_emoji_enabled() else "[SUCCESS]"
            logger.info(f"{emoji} {success_msg}" if get_emoji_enabled() else success_msg)
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
        update_interval: float = 0.5,
    ):
        """Initialize real-time streaming progress indicator."""
        self.total = total
        self.message = message
        self.stream = stream or sys.stderr
        self.update_interval = update_interval
        self.current = 0
        self.last_update = 0.0
        self.start_time = time.time()

    def update(self, increment: int = 1, custom_message: str | None = None) -> None:
        """Update progress by increment, display if throttle interval elapsed."""
        self.current = min(self.current + increment, self.total)
        now = time.time()

        # Throttle updates
        if now - self.last_update < self.update_interval:
            return

        self.last_update = now
        self._display(custom_message)

    def set(self, value: int, custom_message: str | None = None) -> None:
        """Set progress to a specific value and display."""
        self.current = min(value, self.total)
        self._display(custom_message)

    def _display(self, custom_message: str | None = None) -> None:
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
            eta_str = f" | ETA: {format_duration(remaining)}"

        message = custom_message or self.message
        status = f"\r{message}: {self.current}/{self.total} ({percent}%){eta_str}"

        # Pad to clear previous line
        status = status.ljust(80)
        self.stream.write(status)
        self.stream.flush()

    def finish(self, final_message: str | None = None) -> None:
        """Clear progress line and display final message or completion status."""
        if self.stream.isatty():
            self.stream.write("\r" + " " * 80 + "\r")
            self.stream.flush()

        if final_message:
            self.stream.write(f"{final_message}\n")
            self.stream.flush()
        elif self.stream.isatty():
            # Show completion
            elapsed = time.time() - self.start_time
            self.stream.write(
                f"✅ {self.message}: {self.current}/{self.total} complete ({elapsed:.1f}s)\n"
            )
            self.stream.flush()


def log_progress_streaming(
    current: int,
    total: int,
    message: str = "Progress",
    logger: logging.Logger | None = None,
) -> None:
    """Log streaming progress with real-time updates.

    Args:
        current: Current progress value
        total: Total progress value
        message: Progress message
        logger: Logger instance (optional)
    """
    if not sys.stderr.isatty():
        # Not a TTY - fall back to plain log line
        _logger = logger or logging.getLogger(__name__)
        percent = (current * 100) // total if total > 0 else 0
        _logger.info(f"[{current}/{total} - {percent}%] {message}")
        return

    percent = (current * 100) // total if total > 0 else 0
    status = f"\r{message}: {current}/{total} ({percent}%)"

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
    logger: logging.Logger | None = None,
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
        logger = logging.getLogger(__name__)

    eta = calculate_eta(elapsed_time, current, total)
    if eta is not None:
        eta_str = format_duration(eta)
        logger.info(f"{stage} [{current}/{total}] - ETA: {eta_str}")
    else:
        logger.info(f"{stage} [{current}/{total}]")


def log_resource_usage(
    cpu_percent: float | None = None,
    memory_mb: float | None = None,
    logger: logging.Logger | None = None,
) -> None:
    """Log current resource usage.

    Args:
        cpu_percent: CPU usage percentage (optional)
        memory_mb: Memory usage in MB (optional)
        logger: Logger instance (optional)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    parts = []
    if cpu_percent is not None:
        parts.append(f"CPU: {cpu_percent:.1f}%")
    if memory_mb is not None:
        parts.append(f"Memory: {memory_mb:.1f} MB")

    if parts:
        logger.debug(f"Resource usage: {', '.join(parts)}")
