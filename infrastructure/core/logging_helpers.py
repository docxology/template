"""Helper functions for logging utilities."""

from __future__ import annotations

from typing import Any

# Note: get_logger is imported at function level to avoid circular import


def format_error_with_suggestions(error: Any) -> str:
    """Format error message with context, recovery suggestions, and commands.

    Args:
        error: TemplateError instance with context, suggestions, and recovery commands

    Returns:
        Formatted error message string

    Example:
        >>> from infrastructure.core.exceptions import TemplateError
        >>> error = TemplateError(
        ...     "File not found",
        ...     context={"file": "test.txt", "line": 10},
        ...     suggestions=["Check file path", "Verify permissions"],
        ...     recovery_commands=["ls -la test.txt", "cat test.txt"]
        ... )
        >>> print(format_error_with_suggestions(error))
        ❌ File not found
        <BLANKLINE>
        📋 Context:
           • file: test.txt
           • line: 10
        <BLANKLINE>
        🔧 Recovery Options:
           1. Check file path
           2. Verify permissions
        <BLANKLINE>
        💻 Quick Fix Commands:
           $ ls -la test.txt
           $ cat test.txt
    """
    # Import here to avoid circular import
    from infrastructure.core.exceptions import TemplateError

    if not isinstance(error, TemplateError):
        return str(error)

    lines = [f"❌ {error.message}"]

    if error.context:
        lines.append("\n📋 Context:")
        for key, value in error.context.items():
            lines.append(f"   • {key}: {value}")

    if error.suggestions:
        lines.append("\n🔧 Recovery Options:")
        for i, suggestion in enumerate(error.suggestions, 1):
            lines.append(f"   {i}. {suggestion}")

    if error.recovery_commands:
        lines.append("\n💻 Quick Fix Commands:")
        for cmd in error.recovery_commands:
            lines.append(f"   $ {cmd}")

    return "\n".join(lines)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string (e.g., '1m 23s', '45s')."""
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {secs}s"

    hours = minutes // 60
    mins = minutes % 60

    if hours < 24:
        return f"{hours}h {mins}m"

    days = hours // 24
    hrs = hours % 24
    return f"{days}d {hrs}h"
