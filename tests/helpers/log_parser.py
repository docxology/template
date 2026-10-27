"""Structured log parser for integration test assertions.

Provides utilities to parse JSON-formatted log output from scripts
running with STRUCTURED_LOGGING=true, enabling typed assertions
against log level, logger name, and message content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LogEntry:
    """A single parsed structured log entry."""

    timestamp: str
    level: str
    logger: str
    message: str
    exception: Optional[str] = None


def parse_structured_logs(output: str) -> List[LogEntry]:
    """Parse structured JSON log lines from command output.

    Each line of output is expected to be a JSON object with at least
    'timestamp', 'level', 'logger', and 'message' keys. Non-JSON lines
    (e.g., plain text output) are silently skipped.

    Args:
        output: Raw stdout/stderr from a command run with STRUCTURED_LOGGING=true.

    Returns:
        List of LogEntry objects, one per valid JSON log line.

    Example:
        >>> logs = parse_structured_logs(result.stdout)
        >>> assert any(e.level == "INFO" and "passed" in e.message for e in logs)
    """
    entries: List[LogEntry] = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
            entries.append(
                LogEntry(
                    timestamp=data.get("timestamp", ""),
                    level=data.get("level", ""),
                    logger=data.get("logger", ""),
                    message=data.get("message", ""),
                    exception=data.get("exception"),
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return entries


def filter_by_level(entries: List[LogEntry], level: str) -> List[LogEntry]:
    """Filter log entries by level (e.g., 'INFO', 'ERROR', 'WARNING').

    Args:
        entries: List of LogEntry objects.
        level: Log level string to filter on (case-insensitive).

    Returns:
        Filtered list of LogEntry objects matching the specified level.
    """
    return [e for e in entries if e.level.upper() == level.upper()]


def filter_by_logger(entries: List[LogEntry], logger_prefix: str) -> List[LogEntry]:
    """Filter log entries by logger name prefix.

    Args:
        entries: List of LogEntry objects.
        logger_prefix: Prefix to match against logger names.

    Returns:
        Filtered list of LogEntry objects whose logger starts with the prefix.
    """
    return [e for e in entries if e.logger.startswith(logger_prefix)]


def contains_message(entries: List[LogEntry], substring: str) -> bool:
    """Check if any log entry contains a message substring.

    Args:
        entries: List of LogEntry objects.
        substring: Substring to search for in messages.

    Returns:
        True if any entry's message contains the substring.
    """
    return any(substring in e.message for e in entries)
