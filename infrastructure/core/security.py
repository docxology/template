"""Security utilities and input validation for the research template system.

This module provides comprehensive security measures including input validation,
security headers, rate limiting, and security monitoring.
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional, List, Callable, Union
from functools import wraps
from pathlib import Path
import re

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class SecurityValidator:
    """Comprehensive input validation and security checks."""

    def __init__(self):
        # Maximum sizes for different input types
        self.limits = {
            'prompt_length': 100000,  # Max LLM prompt length
            'filename_length': 255,   # Max filename length
            'path_length': 4096,      # Max path length
            'content_size': 50 * 1024 * 1024,  # 50MB max content size
        }

        # Dangerous patterns to block
        self.dangerous_patterns = [
            # System prompt injection
            r'(?i)system\s*prompt\s*[:=]',
            r'(?i)ignore\s+previous\s+instructions',
            r'(?i)override\s+system\s+prompt',

            # Code execution attempts
            r'(?i)exec\(|eval\(|subprocess\.|os\.system',
            r'(?i)import\s+os|import\s+subprocess',

            # File system access
            r'(?i)open\(|file\(|pathlib\.|os\.path',
            r'(?i)read\s+file|write\s+file|delete\s+file',

            # Network access
            r'(?i)requests\.|urllib\.|socket\.|http',

            # SQL injection
            r'(?i)(select|insert|update|delete|drop|create)\s+.*from',

            # XSS attempts
            r'<script|<iframe|<object|<embed',
            r'on\w+\s*=|javascript:|vbscript:',

            # LaTeX injection
            r'\\input|\\include|\\usepackage|\\newcommand',
            r'\\write|\\read|\\openout|\\openin',
        ]

    def validate_llm_input(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
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

        if len(prompt) > self.limits['prompt_length']:
            raise SecurityViolation(f"Prompt too long: {len(prompt)} > {self.limits['prompt_length']}")

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
        if ".." in str(path) or path_obj.is_absolute():
            raise SecurityViolation("Directory traversal detected")

        # Resolve path to check for symlinks
        try:
            resolved = path_obj.resolve()
        except (OSError, RuntimeError):
            raise SecurityViolation("Invalid path")

        # Check path length
        if len(str(path)) > self.limits['path_length']:
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

        if len(filename) > self.limits['filename_length']:
            raise SecurityViolation("Filename too long")

        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', '_', filename)

        # Remove path separators
        sanitized = re.sub(r'[\/\\]', '_', sanitized)

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
        if len(content) > self.limits['content_size']:
            raise SecurityViolation(f"Content too large: {len(content)} > {self.limits['content_size']}")
        return content

    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML entities."""
        import html
        return html.escape(text, quote=True)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()


class SecurityHeaders:
    """Security headers for HTTP responses and requests."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get comprehensive security headers.

        Returns:
            Dictionary of security headers
        """
        return {
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",

            # Prevent MIME sniffing
            'X-Content-Type-Options': 'nosniff',

            # Enable XSS protection
            'X-XSS-Protection': '1; mode=block',

            # Prevent referrer leakage
            'Referrer-Policy': 'strict-origin-when-cross-origin',

            # HSTS (if HTTPS is enabled)
            # 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',

            # Prevent caching of sensitive content
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        }

    @staticmethod
    def get_cors_headers(origin: Optional[str] = None) -> Dict[str, str]:
        """Get CORS headers for cross-origin requests.

        Args:
            origin: Allowed origin (None for deny all)

        Returns:
            Dictionary of CORS headers
        """
        headers = {
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400',  # 24 hours
        }

        if origin:
            headers['Access-Control-Allow-Origin'] = origin
            headers['Access-Control-Allow-Credentials'] = 'true'
        else:
            headers['Access-Control-Allow-Origin'] = 'null'

        return headers


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key.

        Args:
            key: Identifier for rate limiting (e.g., IP address, user ID)

        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside the window
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if now - timestamp < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True

        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for given key.

        Args:
            key: Identifier for rate limiting

        Returns:
            Number of remaining requests in current window
        """
        now = time.time()
        if key not in self.requests:
            return self.max_requests

        # Clean old requests
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if now - timestamp < self.window_seconds
        ]

        return max(0, self.max_requests - len(self.requests[key]))


class SecurityMonitor:
    """Monitor security events and anomalies."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.max_events = 1000

    def log_security_event(self, event_type: str, details: Dict[str, Any],
                          severity: str = 'info') -> None:
        """Log a security event.

        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (info, warning, error, critical)
        """
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'severity': severity,
            'details': details,
        }

        self.events.append(event)

        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        # Log based on severity
        if severity == 'warning':
            logger.warning(f"Security event: {event_type} - {details}")
        elif severity == 'error':
            logger.error(f"Security event: {event_type} - {details}")
        elif severity == 'critical':
            logger.critical(f"Security event: {event_type} - {details}")
        else:
            logger.info(f"Security event: {event_type} - {details}")

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent security events
        """
        return self.events[-limit:]

    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events by type.

        Args:
            event_type: Type of events to retrieve

        Returns:
            List of events of specified type
        """
        return [event for event in self.events if event['type'] == event_type]

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary statistics.

        Returns:
            Dictionary with security statistics
        """
        total_events = len(self.events)
        events_by_type = {}
        events_by_severity = {}

        for event in self.events:
            event_type = event['type']
            severity = event['severity']

            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            events_by_severity[severity] = events_by_severity.get(severity, 0) + 1

        return {
            'total_events': total_events,
            'events_by_type': events_by_type,
            'events_by_severity': events_by_severity,
            'most_recent_event': self.events[-1] if self.events else None,
        }


class SecurityViolation(Exception):
    """Exception raised for security violations."""
    pass


# Global instances
_security_validator = SecurityValidator()
_security_headers = SecurityHeaders()
_rate_limiter = RateLimiter()
_security_monitor = SecurityMonitor()


def get_security_validator() -> SecurityValidator:
    """Get the global security validator instance."""
    return _security_validator


def get_security_headers() -> Dict[str, str]:
    """Get security headers."""
    return _security_headers.get_security_headers()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance."""
    return _security_monitor


def validate_llm_input(prompt: str) -> str:
    """Convenience function for LLM input validation."""
    return _security_validator.validate_llm_input(prompt)


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting functions.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        limiter = RateLimiter(max_requests, window_seconds)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as rate limit key (could be enhanced with user ID/IP)
            key = f"{func.__module__}.{func.__name__}"

            if not limiter.is_allowed(key):
                remaining = limiter.get_remaining_requests(key)
                _security_monitor.log_security_event(
                    'rate_limit_exceeded',
                    {'function': f"{func.__module__}.{func.__name__}", 'remaining': remaining},
                    'warning'
                )
                raise SecurityViolation(f"Rate limit exceeded. {remaining} requests remaining.")

            return func(*args, **kwargs)

        return wrapper
    return decorator