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

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Standard exceptions that indicate transient infrastructure failures.
# Pass to retry_with_backoff(exceptions=TRANSIENT_EXCEPTIONS) or use
# retry_on_transient_failure() for a pre-configured shorthand.
TRANSIENT_EXCEPTIONS: tuple[type[Exception], ...] = (IOError, ConnectionError, TimeoutError, OSError)

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

    Example:
        >>> @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        ... def fetch_data():
        ...     # May raise ConnectionError
        ...     return requests.get("https://api.example.com")
        >>>
        >>> # Will retry up to 3 times with exponential backoff
        >>> data = fetch_data()
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

                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)

                    # Add jitter to prevent synchronized retries
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay += jitter_amount

                    # Call retry callback if provided
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
            raise RuntimeError(f"{func.__name__} retry loop exhausted without returning or raising")

        return wrapper

    return decorator

def retry_on_transient_failure(
    max_attempts: int = 3, initial_delay: float = 1.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying on common transient failures.

    Convenience wrapper around retry_with_backoff that catches common
    transient failure exceptions (IOError, ConnectionError, TimeoutError).

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)

    Returns:
        Decorator function

    Example:
        >>> @retry_on_transient_failure()
        ... def read_file(path):
        ...     return open(path).read()
        >>>
        >>> # Will retry on IOError (file locks, network issues, etc.)
        >>> content = read_file("data.txt")
    """
    return retry_with_backoff(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=10.0,
        exceptions=TRANSIENT_EXCEPTIONS,
    )

class RetryableOperation:
    """Context manager for retryable operations with manual control.

    Useful when you need more control over retry logic than a decorator provides.

    Example:
        >>> with RetryableOperation(max_attempts=3) as op:
        ...     for attempt in op:
        ...         try:
        ...             result = risky_operation()
        ...             op.succeed(result)
        ...         except TransientError as e:
        ...             op.retry(e)
    """

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
        self.result = None
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
    ) -> None:
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
            StopIteration: If max attempts reached
        """
        if self.attempt >= self.max_attempts:
            logger.error(f"Operation failed after {self.max_attempts} attempts: {exception}")
            raise exception

        # Calculate delay
        delay = min(
            self.initial_delay * (self.exponential_base ** (self.attempt - 1)),
            self.max_delay,
        )

        logger.warning(
            f"Attempt {self.attempt}/{self.max_attempts} failed: {exception}. "
            f"Retrying in {delay:.1f}s..."
        )

        time.sleep(delay)
