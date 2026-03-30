"""Security utilities and input validation for the research template system.

This module provides comprehensive security measures including input validation,
security headers, rate limiting, and security monitoring.

API style note:
- SecurityValidator, RateLimiter, SecurityMonitor are stateful classes (hold config/state).
- get_security_headers(), get_cors_headers() are module-level convenience functions
  for stateless one-off checks.
Implementation split:
- _validation.py   — SecurityValidator (input/path/filename/content validation)
- _rate_limiting.py — RateLimiter, SecurityMonitor, rate_limit decorator
- security.py       — HTTP headers, singletons, backwards-compat re-exports
"""

from __future__ import annotations

import functools

# Re-export from submodules for backwards compatibility
from infrastructure.core._rate_limiting import (  # noqa: F401
    RateLimiter,
    SecurityMonitor,
    get_security_monitor,
    rate_limit,
)
from infrastructure.core._validation import SecurityValidator  # noqa: F401


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
    headers: dict[str, str] = {
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


@functools.lru_cache(maxsize=1)
def get_security_validator() -> SecurityValidator:
    """Return the process-wide SecurityValidator singleton."""
    return SecurityValidator()


def reset_security_validator() -> None:
    """Reset the security validator singleton (for testing)."""
    get_security_validator.cache_clear()


@functools.lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    """Return the process-wide RateLimiter singleton."""
    return RateLimiter()


def reset_rate_limiter() -> None:
    """Reset the rate limiter singleton (for testing)."""
    get_rate_limiter.cache_clear()
