"""Helper functions for logging utilities."""

from __future__ import annotations

from typing import Any

from infrastructure.core.exceptions import TemplateError


def format_error_with_suggestions(error: Any) -> str:
    """Format a TemplateError into a human-readable message.

    Includes context and recovery suggestions.
    """
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
