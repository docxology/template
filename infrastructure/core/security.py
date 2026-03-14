"""Security utilities and input validation for the research template system.

This module provides comprehensive security measures including input validation,
security headers, rate limiting, and security monitoring.

API style note:
- SecurityValidator, RateLimiter, SecurityMonitor are stateful classes (hold config/state).
- get_security_headers(), get_cors_headers(), validate_llm_input() are module-level
  convenience functions for stateless one-off checks. Both styles are intentional.
"""

from __future__ import annotations

import functools
import re
import threading
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Union

from infrastructure.core.exceptions import SecurityViolation
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class SecurityValidator:
    """Comprehensive input validation and security checks."""

    def __init__(self) -> None:
        # Maximum sizes for different input types
        self.limits = {
            "prompt_length": 100000,  # Max LLM prompt length
            "filename_length": 255,  # Max filename length
            "path_length": 4096,  # Max path length
            "content_size": 50 * 1024 * 1024,  # 50MB max content size
        }

        # Dangerous patterns to block.
        # \b anchors prevent substring false-positives (e.g. "hexec" won't match "exec").
        # \s* between identifier and ( catches evasion via whitespace (e.g. "exec (").
        self.dangerous_patterns = [
            # System prompt injection — exact injected phrases
            r"(?i)system\s*prompt\s*[:=]",
            r"(?i)\bignore\s+previous\s+instructions\b",
            r"(?i)\boverride\s+system\s+prompt\b",
            r"(?i)change\s+your\s+persona",
            # Python code execution — built-ins and subprocess (\b anchors to identifier boundary)
            r"(?i)\bexec\s*\(|\beval\s*\(|\bsubprocess\.\w|\bos\.system\s*\(",
            r"(?i)\bimport\s+os\b|\bimport\s+subprocess\b",
            r"(?i)shell\s*[:=]|bash\s*[:=]|cmd\s*[:=]",
            # File system access — open/file builtins and path libraries
            r"(?i)\bopen\s*\(|\bfile\s*\(|\bpathlib\.\w|\bos\.path\.\w",
            r"(?i)\bread\s+file\b|\bwrite\s+file\b|\bdelete\s+file\b",
            # Network access — library prefixes (\b prevents partial matches like "urllib2")
            r"(?i)\brequests\.\w|\burllib\.\w|\bsocket\.\w|\bhttps?://",
            r"(?i)connect\s+to|download\s+from|upload\s+to",
            # SQL injection — DML/DDL keywords (\b on both sides reduces false positives)
            r"(?i)\b(select|insert|update|delete|drop|create)\b\s+.*\bfrom\b",
            r"(?i)union\s+select|information_schema",
            # XSS — HTML injection tags ([\s>/] prevents matching "<scripted" etc.)
            r"(?i)<script[\s>/]|<iframe[\s>/]|<object[\s>/]|<embed[\s>/]",
            r"(?i)\bon\w+\s*=|javascript:|vbscript:",
            # LaTeX injection — commands that read/write files or include external content
            r"\\input\s*\{|\\include\s*\{|\\usepackage\s*[\[{]|\\newcommand\s*\{",
            r"\\write\s*\d|\\read\s*\d|\\openout\s*\d|\\openin\s*\d",
        ]

    def validate_llm_input(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        """Validate and sanitize LLM input.

        Args:
            prompt: Input prompt to validate
            context: Additional validation context

        Returns:
            Sanitized prompt

        Raises:
            SecurityViolation: If input contains dangerous content
        """
        if not isinstance(prompt, str):
            raise SecurityViolation("Input must be a string")

        if len(prompt) > self.limits["prompt_length"]:
            raise SecurityViolation(
                f"Prompt too long: {len(prompt)} > {self.limits['prompt_length']}"
            )

        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                logger.warning(f"Security pattern detected: {pattern}")
                raise SecurityViolation("Input contains potentially dangerous content")

        # Sanitize HTML entities
        prompt = self._sanitize_html(prompt)

        # Normalize whitespace
        prompt = self._normalize_whitespace(prompt)

        return prompt

    def validate_file_path(self, path: Union[str, Path]) -> Path:
        """Validate file path for security.

        Args:
            path: File path to validate

        Returns:
            Validated Path object

        Raises:
            SecurityViolation: If path is unsafe
        """
        path_obj = Path(path)

        # Check for directory traversal
        if ".." in str(path):
            raise SecurityViolation("Directory traversal detected")

        # Resolve path to check for symlinks
        try:
            resolved = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise SecurityViolation("Invalid path") from e

        # Check path length
        if len(str(path)) > self.limits["path_length"]:
            raise SecurityViolation("Path too long")

        return resolved

    def validate_filename(self, filename: str) -> str:
        """Validate and sanitize filename.

        Args:
            filename: Filename to validate

        Returns:
            Sanitized filename

        Raises:
            SecurityViolation: If filename is unsafe
        """
        if not filename or not isinstance(filename, str):
            raise SecurityViolation("Invalid filename")

        if len(filename) > self.limits["filename_length"]:
            raise SecurityViolation("Filename too long")

        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', "_", filename)

        # Remove path separators
        sanitized = re.sub(r"[\/\\]", "_", sanitized)

        # Ensure not empty after sanitization
        if not sanitized.strip():
            sanitized = "unnamed_file"

        return sanitized

    def validate_content_size(self, content: bytes) -> bytes:
        """Validate content size.

        Args:
            content: Content to validate

        Returns:
            Content if size is acceptable

        Raises:
            SecurityViolation: If content is too large
        """
        if len(content) > self.limits["content_size"]:
            raise SecurityViolation(
                f"Content too large: {len(content)} > {self.limits['content_size']}"
            )
        return content

    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML entities."""
        import html

        return html.escape(text, quote=True)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()


def get_security_headers() -> dict[str, str]:
    """Return comprehensive HTTP security headers."""
    return {
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",  # noqa: E501
        # Prevent MIME sniffing
        "X-Content-Type-Options": "nosniff",
        # Enable XSS protection
        "X-XSS-Protection": "1; mode=block",
        # Prevent referrer leakage
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # HSTS (if HTTPS is enabled)
        # 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        # Prevent caching of sensitive content
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }


def get_cors_headers(origin: str | None = None) -> dict[str, str]:
    """Get CORS headers for cross-origin requests.

    Args:
        origin: Allowed origin (None for deny all)

    Returns:
        Dictionary of CORS headers
    """
    headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",  # 24 hours
    }

    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    else:
        headers["Access-Control-Allow-Origin"] = "null"

    return headers


class RateLimiter:
    """Simple in-memory rate limiter.

    Thread-safe: all mutations to the requests dict are guarded by a Lock.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

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

            # Remove old requests outside the window
            self.requests[key] = [
                ts for ts in self.requests[key] if now - ts < self.window_seconds
            ]

            # Check if under limit
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

            # Clean old requests
            self.requests[key] = [
                ts for ts in self.requests[key] if now - ts < self.window_seconds
            ]

            return max(0, self.max_requests - len(self.requests[key]))


class SecurityMonitor:
    """Monitor security events and anomalies."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
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
        event = {
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
            logger.info(f"Security event: {event_type} - {details}")

    def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent security events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent security events
        """
        return self.events[-limit:]

    def get_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """Get events by type.

        Args:
            event_type: Type of events to retrieve

        Returns:
            List of events of specified type
        """
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



@functools.lru_cache(maxsize=1)
def get_security_validator() -> SecurityValidator:
    """Get the global security validator instance (lazily initialized)."""
    return SecurityValidator()


@functools.lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance (lazily initialized)."""
    return RateLimiter()


@functools.lru_cache(maxsize=1)
def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance (lazily initialized)."""
    return SecurityMonitor()


def rate_limit(max_requests: int = 100, window_seconds: int = 60) -> Callable[..., Any]:
    """Decorator for rate limiting functions.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
    """

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
