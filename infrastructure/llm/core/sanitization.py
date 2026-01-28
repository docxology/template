"""Input sanitization and security utilities for LLM operations.

This module provides comprehensive input validation, sanitization,
and security measures for LLM prompts and user inputs.
"""

import html
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class InputSanitizer:
    """Comprehensive input sanitization for LLM operations."""

    def __init__(self):
        # Dangerous patterns to filter
        self.dangerous_patterns = [
            # System prompt injection attempts
            r"(?i)system\s*prompt\s*[:=]",
            r"(?i)ignore\s+previous\s+instructions",
            r"(?i)override\s+system\s+prompt",
            r"(?i)change\s+your\s+persona",
            # Code execution attempts
            r"(?i)exec\(|eval\(|subprocess\.|os\.system",
            r"(?i)import\s+os|import\s+subprocess",
            r"(?i)shell\s*[:=]|bash\s*[:=]|cmd\s*[:=]",
            # File system access
            r"(?i)open\(|file\(|pathlib\.|os\.path",
            r"(?i)read\s+file|write\s+file|delete\s+file",
            # Network access
            r"(?i)requests\.|urllib\.|socket\.|http",
            r"(?i)connect\s+to|download\s+from|upload\s+to",
            # Dangerous LaTeX commands
            r"\\input|\\include|\\usepackage|\\newcommand",
            r"\\write|\\read|\\openout|\\openin",
            # SQL injection patterns
            r"(?i)(select|insert|update|delete|drop|create)\s+.*from",
            r"(?i)union\s+select|information_schema",
            # XSS attempts
            r"<script|<iframe|<object|<embed",
            r"on\w+\s*=|javascript:|vbscript:",
        ]

        # HTML entities to escape
        self.html_entities = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }

    def sanitize_prompt(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Sanitize LLM prompt for security.

        Args:
            prompt: Raw prompt text
            context: Additional context for validation

        Returns:
            Sanitized prompt text

        Raises:
            SecurityError: If prompt contains dangerous content
        """
        if not isinstance(prompt, str):
            raise SecurityError("Prompt must be a string")

        # Remove null bytes and other control characters
        prompt = self._remove_control_characters(prompt)

        # Check for dangerous patterns
        self._check_dangerous_patterns(prompt)

        # Sanitize HTML entities
        prompt = self._escape_html_entities(prompt)

        # Remove excessive whitespace
        prompt = self._normalize_whitespace(prompt)

        # Limit prompt length
        prompt = self._limit_length(prompt)

        logger.debug(f"Sanitized prompt: {len(prompt)} characters")
        return prompt

    def validate_file_input(
        self, file_path: Path, allowed_extensions: Optional[List[str]] = None
    ) -> bool:
        """Validate file input for security.

        Args:
            file_path: Path to file
            allowed_extensions: List of allowed file extensions

        Returns:
            True if file is safe to process

        Raises:
            SecurityError: If file input is unsafe
        """
        # Check if path is absolute (potential directory traversal)
        if file_path.is_absolute():
            raise SecurityError("Absolute paths not allowed")

        # Resolve path to prevent traversal attacks
        try:
            resolved = file_path.resolve()
        except (OSError, RuntimeError):
            raise SecurityError("Invalid file path")

        # Check for directory traversal attempts
        if ".." in str(file_path) or not resolved.exists():
            raise SecurityError("Invalid file path")

        # Check file extension
        if allowed_extensions:
            if resolved.suffix.lower() not in [
                ext.lower() for ext in allowed_extensions
            ]:
                raise SecurityError(f"File extension not allowed: {resolved.suffix}")

        # Check file size (prevent DoS)
        max_size = 50 * 1024 * 1024  # 50MB limit
        if resolved.stat().st_size > max_size:
            raise SecurityError(f"File too large: {resolved.stat().st_size} bytes")

        return True

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations.

        Args:
            filename: Raw filename

        Returns:
            Sanitized filename safe for file operations
        """
        if not filename or not isinstance(filename, str):
            raise SecurityError("Invalid filename")

        # Remove path separators
        filename = re.sub(r"[\/\\]", "_", filename)

        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', "_", filename)

        # Remove control characters
        filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

        # Limit length
        filename = filename[:255]

        # Ensure not empty after sanitization
        if not filename.strip():
            filename = "unnamed_file"

        return filename

    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters from text."""
        # Remove null bytes and other dangerous control characters
        # Keep newlines, tabs, and spaces
        return re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    def _check_dangerous_patterns(self, text: str) -> None:
        """Check for dangerous patterns in text."""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected: {pattern}")
                raise SecurityError(f"Dangerous content detected in input")

    def _escape_html_entities(self, text: str) -> str:
        """Escape HTML entities for safety."""
        return html.escape(text, quote=True)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    def _limit_length(self, text: str, max_length: int = 100000) -> str:
        """Limit text length to prevent resource exhaustion."""
        if len(text) > max_length:
            logger.warning(
                f"Text truncated from {len(text)} to {max_length} characters"
            )
            return text[:max_length] + "...[truncated]"
        return text


class SecurityError(Exception):
    """Exception raised for security violations."""

    pass


class HealthChecker:
    """System health monitoring and status checks."""

    def __init__(self):
        self.checks = {
            "filesystem": self._check_filesystem,
            "dependencies": self._check_dependencies,
            "network": self._check_network,
            "memory": self._check_memory,
        }

    def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks.

        Returns:
            Dictionary of check results
        """
        results = {}
        for name, check_func in self.checks.items():
            try:
                results[name] = {
                    "status": "healthy",
                    "details": check_func(),
                    "timestamp": __import__("time").time(),
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": __import__("time").time(),
                }
        return results

    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem health."""
        import os
        import tempfile

        # Check disk space
        stat = os.statvfs(".")
        free_space = stat.f_bavail * stat.f_frsize
        total_space = stat.f_blocks * stat.f_frsize

        # Check write permissions
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
                f.write("test")
            writeable = True
        except (OSError, IOError):
            writeable = False

        return {
            "free_space_mb": free_space // (1024 * 1024),
            "total_space_mb": total_space // (1024 * 1024),
            "writeable": writeable,
        }

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies."""
        dependencies = ["numpy", "matplotlib", "requests"]
        results = {}

        for dep in dependencies:
            try:
                __import__(dep)
                results[dep] = "available"
            except ImportError:
                results[dep] = "missing"

        return results

    def _check_network(self) -> Dict[str, Any]:
        """Check network connectivity."""
        import socket

        try:
            # Test DNS resolution
            socket.gethostbyname("google.com")
            dns_resolvable = True
        except socket.gaierror:
            dns_resolvable = False

        try:
            # Test HTTP connectivity
            import requests

            response = requests.get("https://httpbin.org/status/200", timeout=5)
            http_available = response.status_code == 200
        except:
            http_available = False

        return {
            "dns_resolvable": dns_resolvable,
            "http_available": http_available,
        }

    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        import psutil

        try:
            memory = psutil.virtual_memory()
            return {
                "total_mb": memory.total // (1024 * 1024),
                "available_mb": memory.available // (1024 * 1024),
                "percent_used": memory.percent,
            }
        except ImportError:
            return {"psutil_unavailable": True}


# Global instances
_input_sanitizer = InputSanitizer()
_health_checker = HealthChecker()


def get_input_sanitizer() -> InputSanitizer:
    """Get the global input sanitizer instance."""
    return _input_sanitizer


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


def sanitize_llm_input(prompt: str) -> str:
    """Convenience function for LLM input sanitization."""
    return _input_sanitizer.sanitize_prompt(prompt)


def run_health_check() -> Dict[str, Dict[str, Any]]:
    """Convenience function for running health checks."""
    return _health_checker.run_all_checks()
