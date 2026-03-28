"""Retry utilities for handling transient failures.

This module provides decorators and utilities for retrying operations that may
fail transiently (network issues, file locks, etc.) with exponential backoff.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import random
import time
import types
from functools import wraps
from typing import Any, Callable, TypeVar

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Standard exceptions that indicate transient infrastructure failures.
# Pass to retry_with_backoff(exceptions=TRANSIENT_EXCEPTIONS) or use
# retry_on_transient_failure() for a pre-configured shorthand.
TRANSIENT_EXCEPTIONS: tuple[type[Exception], ...] = (ConnectionError, TimeoutError, OSError)


def _compute_backoff_delay(
    attempt: int, initial_delay: float, exponential_base: float, max_delay: float
) -> float:
    """Return capped exponential backoff delay for the given attempt (1-indexed)."""
    return min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception | None], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function with exponential backoff.

    Retries the function if it raises one of the specified exceptions,
    with exponential backoff between attempts.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        exceptions: Tuple of exception types to catch and retry (default: Exception)
        on_retry: Optional callback function(attempt_num, exception) called before retry

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= max_attempts:
                        # Final attempt failed, log and re-raise
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    delay = _compute_backoff_delay(attempt, initial_delay, exponential_base, max_delay)

                    # Add jitter to prevent synchronized retries (thundering herd)
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay += jitter_amount

                    if on_retry:
                        on_retry(attempt, e)
                    else:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                    time.sleep(delay)

            # This branch is unreachable: the loop always either returns or raises.
            # The explicit raise satisfies the type checker (return type T, not T | None).
            raise RuntimeError(f"{func.__name__} retry loop exhausted without returning or raising")  # pragma: no cover

        return wrapper

    return decorator


def retry_on_transient_failure(
    max_attempts: int = 3, initial_delay: float = 1.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying on common transient failures.

    Convenience wrapper around retry_with_backoff that catches common
    transient failure exceptions (IOError, ConnectionError, TimeoutError).
    """
    return retry_with_backoff(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=10.0,
        exceptions=TRANSIENT_EXCEPTIONS,
    )


class RetryableOperation:
    """Context manager for retryable operations with manual retry control."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retryable operation.

        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.attempt = 0
        self.result: Any = None
        self.succeeded = False
        self._done = False

    def __enter__(self) -> "RetryableOperation":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None:
        """Exit context manager."""
        return None  # Don't suppress exceptions

    def __iter__(self):
        """Iterate over attempts."""
        return self

    def __next__(self) -> int:
        """Get next attempt number."""
        if self._done:
            raise StopIteration
        self.attempt += 1
        if self.attempt > self.max_attempts:
            raise StopIteration
        return self.attempt

    def succeed(self, result: Any = None) -> None:
        """Mark operation as successful.

        Args:
            result: Result value to store
        """
        self.result = result
        self.succeeded = True
        self._done = True  # Signal __next__ to stop iteration

    def retry(self, exception: Exception) -> None:
        """Retry operation after delay.

        Args:
            exception: Exception that triggered the retry

        Raises:
            Exception: Re-raises the caller-provided ``exception`` when max attempts are reached.
                The exact type depends on what the caller passed in.
        """
        if self.attempt >= self.max_attempts:
            logger.error(f"Operation failed after {self.max_attempts} attempts: {exception}")
            raise exception

        delay = _compute_backoff_delay(
            self.attempt, self.initial_delay, self.exponential_base, self.max_delay
        )
        # Add jitter to prevent thundering herd (matches retry_with_backoff behaviour)
        delay += delay * 0.1 * random.random()

        logger.warning(
            f"Attempt {self.attempt}/{self.max_attempts} failed: {exception}. "
            f"Retrying in {delay:.1f}s..."
        )

        time.sleep(delay)
