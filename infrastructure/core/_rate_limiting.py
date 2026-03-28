"""Rate limiting and security event monitoring.

Extracted from security.py for single-responsibility. Import via security.py
for backwards compatibility.
"""

from __future__ import annotations

import functools
import threading
import time
from functools import wraps
from typing import Any, Callable, TypedDict

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter.

    Thread-safe: all mutations to the requests dict are guarded by a Lock.

    Note: This class is available for LLM call throttling but is not currently
    wired into LLMClient. Wire via dependency injection when rate-limit enforcement
    is needed for Ollama requests.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _clean_window(self, key: str, now: float) -> None:
        """Remove timestamps outside the current window for the given key."""
        if key in self.requests:
            self.requests[key] = [
                ts for ts in self.requests[key] if now - ts < self.window_seconds
            ]

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key.

        Args:
            key: Identifier for rate limiting (e.g., IP address, user ID)

        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        with self._lock:
            if key not in self.requests:
                self.requests[key] = []

            self._clean_window(key, now)

            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True

        # Intentionally outside the lock — reached only when request count is at the limit
        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for given key.

        Args:
            key: Identifier for rate limiting

        Returns:
            Number of remaining requests in current window
        """
        now = time.time()
        with self._lock:
            if key not in self.requests:
                return self.max_requests

            self._clean_window(key, now)

            return max(0, self.max_requests - len(self.requests[key]))


class SecurityEvent(TypedDict):
    """Structured security event record stored by SecurityMonitor."""

    timestamp: float
    type: str
    severity: str
    details: dict[str, Any]


class SecurityMonitor:
    """Monitor security events and anomalies."""

    def __init__(self) -> None:
        self.events: list[SecurityEvent] = []
        self.max_events = 1000

    def log_security_event(
        self, event_type: str, details: dict[str, Any], severity: str = "info"
    ) -> None:
        """Log a security event.

        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (info, warning, error, critical)
        """
        event: SecurityEvent = {
            "timestamp": time.time(),
            "type": event_type,
            "severity": severity,
            "details": details,
        }

        self.events.append(event)

        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Log based on severity
        if severity == "warning":
            logger.warning(f"Security event: {event_type} - {details}")
        elif severity == "error":
            logger.error(f"Security event: {event_type} - {details}")
        elif severity == "critical":
            logger.critical(f"Security event: {event_type} - {details}")
        else:
            logger.debug(f"Security event: {event_type} - {details}")

    def get_recent_events(self, limit: int = 100) -> list[SecurityEvent]:
        """Get recent security events."""
        return self.events[-limit:]

    def get_events_by_type(self, event_type: str) -> list[SecurityEvent]:
        """Get events by type."""
        return [event for event in self.events if event["type"] == event_type]

    def get_security_summary(self) -> dict[str, Any]:
        """Get security summary statistics.

        Returns:
            Dictionary with security statistics
        """
        total_events = len(self.events)
        events_by_type: dict[str, int] = {}
        events_by_severity: dict[str, int] = {}

        for event in self.events:
            event_type = event["type"]
            severity = event["severity"]

            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            events_by_severity[severity] = events_by_severity.get(severity, 0) + 1

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "events_by_severity": events_by_severity,
            "most_recent_event": self.events[-1] if self.events else None,
        }


def rate_limit(max_requests: int = 100, window_seconds: int = 60) -> Callable[..., Any]:
    """Decorator for rate limiting functions.

    Note: This decorator is implemented and functional but not yet applied to any
    production callable. Apply to LLMClient or API boundary callables when rate
    limiting is needed.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
    """
    # Import here to avoid circular dependency at module level
    from infrastructure.core.exceptions import SecurityViolation

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        limiter = RateLimiter(max_requests, window_seconds)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Use function name as rate limit key (could be enhanced with user ID/IP)
            key = f"{func.__module__}.{func.__name__}"

            if not limiter.is_allowed(key):
                remaining = limiter.get_remaining_requests(key)
                get_security_monitor().log_security_event(
                    "rate_limit_exceeded",
                    {
                        "function": f"{func.__module__}.{func.__name__}",
                        "remaining": remaining,
                    },
                    "warning",
                )
                raise SecurityViolation(f"Rate limit exceeded. {remaining} requests remaining.")

            return func(*args, **kwargs)

        return wrapper

    return decorator


@functools.lru_cache(maxsize=1)
def get_security_monitor() -> SecurityMonitor:
    """Return the process-wide SecurityMonitor singleton."""
    return SecurityMonitor()


def reset_security_monitor() -> None:
    """Reset the security monitor singleton (for testing)."""
    get_security_monitor.cache_clear()
