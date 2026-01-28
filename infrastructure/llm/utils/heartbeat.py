"""Heartbeat monitoring for LLM streaming operations.

Provides real-time monitoring of streaming LLM operations to detect stalls,
provide progress updates, and warn about potential hangs.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class StreamHeartbeatMonitor:
    """Monitor heartbeat for streaming LLM operations.

    Tracks token reception and provides progress updates and stall detection.
    Thread-safe for use with streaming operations.
    """

    def __init__(
        self,
        operation_name: str,
        timeout_seconds: float,
        heartbeat_interval: float = 15.0,
        stall_threshold: float = 60.0,
        early_warning_threshold: float = 30.0,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize heartbeat monitor.

        Args:
            operation_name: Name of the operation (e.g., "translation", "review")
            timeout_seconds: Total timeout for the operation
            heartbeat_interval: Seconds between progress updates (default: 15s)
            stall_threshold: Seconds without tokens before stall warning (default: 60s)
            early_warning_threshold: Seconds before first token to trigger early warning (default: 30s)
            logger: Optional logger instance
        """
        self.operation_name = operation_name
        self.timeout_seconds = timeout_seconds
        self.heartbeat_interval = heartbeat_interval
        self.stall_threshold = stall_threshold
        self.early_warning_threshold = early_warning_threshold
        self.logger = logger or get_logger(__name__)

        # Threading state
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Progress tracking
        self.start_time = time.time()
        self.last_token_time: Optional[float] = None
        self.token_count = 0
        self.first_token_time: Optional[float] = None
        self.estimated_total_tokens: Optional[int] = None

        # Heartbeat state
        self.last_heartbeat_time = self.start_time
        self.last_progress_log_time = self.start_time

    def start_monitoring(self) -> None:
        """Start the heartbeat monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return  # Already monitoring

        self._stop_event.clear()
        self.start_time = time.time()
        self.last_heartbeat_time = self.start_time
        self.last_progress_log_time = self.start_time

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"heartbeat-{self.operation_name}",
        )
        self._monitor_thread.start()

        self.logger.debug(
            f"Started heartbeat monitoring for {self.operation_name}",
            extra={
                "operation": self.operation_name,
                "timeout": self.timeout_seconds,
                "heartbeat_interval": self.heartbeat_interval,
                "stall_threshold": self.stall_threshold,
            },
        )

    def stop_monitoring(self) -> None:
        """Stop the heartbeat monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)

        self.logger.debug(
            f"Stopped heartbeat monitoring for {self.operation_name}",
            extra={
                "operation": self.operation_name,
                "total_tokens": self.token_count,
                "elapsed": time.time() - self.start_time,
            },
        )

    def update_token_received(self, token_count: int = 1) -> None:
        """Update heartbeat when tokens are received.

        Args:
            token_count: Number of tokens received (default: 1)
        """
        now = time.time()

        with self._lock:
            self.token_count += token_count
            self.last_token_time = now

            if self.first_token_time is None:
                self.first_token_time = now
                # Log first token received
                time_to_first = now - self.start_time
                self.logger.info(
                    f"✓ First token received after {time_to_first:.1f}s - generating response...",
                    extra={
                        "operation": self.operation_name,
                        "time_to_first_token": time_to_first,
                        "token_count": self.token_count,
                    },
                )

    def set_estimated_total(self, total_tokens: int) -> None:
        """Set estimated total tokens for progress calculation.

        Args:
            total_tokens: Estimated total number of tokens
        """
        self.estimated_total_tokens = total_tokens

    def _monitor_loop(self) -> None:
        """Main monitoring loop - runs in background thread."""
        while not self._stop_event.is_set():
            now = time.time()
            elapsed = now - self.start_time

            # Check for timeout approaching
            if elapsed > self.timeout_seconds * 0.7:  # After 70% of timeout
                remaining = self.timeout_seconds - elapsed
                if remaining > 0:
                    self.logger.warning(
                        f"⚠️ {self.operation_name.capitalize()} timeout warning: {remaining:.1f}s remaining",
                        extra={
                            "operation": self.operation_name,
                            "elapsed": elapsed,
                            "timeout": self.timeout_seconds,
                            "remaining": remaining,
                            "token_count": self.token_count,
                        },
                    )

            # Check for early warning (no first token yet)
            if self.first_token_time is None:
                if elapsed > self.early_warning_threshold:
                    self.logger.warning(
                        f"⚠️ {self.operation_name.capitalize()} taking longer than expected: {elapsed:.1f}s elapsed, no tokens yet",
                        extra={
                            "operation": self.operation_name,
                            "elapsed": elapsed,
                            "early_warning_threshold": self.early_warning_threshold,
                            "timeout": self.timeout_seconds,
                        },
                    )

            # Check for stalled stream (no tokens for too long)
            if self.last_token_time is not None:
                time_since_last_token = now - self.last_token_time
                if time_since_last_token > self.stall_threshold:
                    self.logger.error(
                        f"🚨 {self.operation_name.capitalize()} stalled: no tokens received for {time_since_last_token:.1f}s",
                        extra={
                            "operation": self.operation_name,
                            "time_since_last_token": time_since_last_token,
                            "stall_threshold": self.stall_threshold,
                            "token_count": self.token_count,
                            "elapsed": elapsed,
                            "timeout_remaining": max(0, self.timeout_seconds - elapsed),
                        },
                    )

            # Log periodic progress updates
            time_since_last_progress = now - self.last_progress_log_time
            if time_since_last_progress >= self.heartbeat_interval:
                self._log_progress_update(elapsed)
                self.last_progress_log_time = now

            # Wait before next check
            self._stop_event.wait(
                self.heartbeat_interval / 4
            )  # Check more frequently than log

    def _log_progress_update(self, elapsed: float) -> None:
        """Log periodic progress update."""
        extra = {
            "operation": self.operation_name,
            "elapsed": elapsed,
            "token_count": self.token_count,
            "timeout": self.timeout_seconds,
            "remaining": max(0, self.timeout_seconds - elapsed),
        }

        if self.first_token_time is not None and elapsed > 0:
            # Calculate tokens per second
            tokens_per_sec = self.token_count / (
                elapsed - (self.first_token_time - self.start_time)
            )
            extra["tokens_per_sec"] = tokens_per_sec

            # Estimate completion if we have total estimate
            if self.estimated_total_tokens and tokens_per_sec > 0:
                remaining_tokens = self.estimated_total_tokens - self.token_count
                if remaining_tokens > 0:
                    estimated_remaining_seconds = remaining_tokens / tokens_per_sec
                    extra["estimated_remaining_seconds"] = estimated_remaining_seconds

        self.logger.info(
            f"⏳ {self.operation_name.capitalize()} still running ({elapsed:.0f}s elapsed)",
            extra=extra,
        )

    def __enter__(self) -> "StreamHeartbeatMonitor":
        """Context manager entry."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop_monitoring()
