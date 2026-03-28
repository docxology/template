"""Unified Diagnostic Logging for the infrastructure pipeline.

Provides structured telemetry logging (DiagnosticEvent) and a centralized
collector (DiagnosticReporter) that generates compiler-style summary tables
(e.g. Red Flags, Yellow Flags, Line Numbers, Fix Suggestions).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from infrastructure.core.logging.constants import EMOJIS, get_emoji_enabled
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class DiagnosticSeverity(Enum):
    """Severity level of a diagnostic event."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class DiagnosticEvent:
    """A single diagnostic event (e.g., a broken link or a LaTeX compiler error)."""

    severity: DiagnosticSeverity
    category: str
    message: str
    file_path: str | Path | None = None
    line_number: int | None = None
    fix_suggestion: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        data = asdict(self)
        data["severity"] = self.severity.value
        if self.file_path:
            data["file_path"] = str(self.file_path)
        return data


class DiagnosticReporter:
    """Centralized collector and formatter for diagnostic events."""

    def __init__(self, project_name: str, output_dir: Path | None = None):
        """Initialize the diagnostic reporter."""
        self.project_name: str = project_name
        self.output_dir: Path | None = output_dir
        self.events: list[DiagnosticEvent] = []
        self._load_existing_events()

    def _load_existing_events(self) -> None:
        """Load existing events from the diagnostics.json file if it exists."""
        if not self.output_dir:
            return
        report_file = self.output_dir / "reports" / "diagnostics.json"
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for ev_dict in data.get("events", []):
                        try:
                            sev = DiagnosticSeverity(ev_dict.get("severity", "ERROR"))
                        except ValueError:
                            sev = DiagnosticSeverity.ERROR
                        
                        event = DiagnosticEvent(
                            severity=sev,
                            category=ev_dict.get("category", "Unknown"),
                            message=ev_dict.get("message", ""),
                            file_path=ev_dict.get("file_path"),
                            line_number=ev_dict.get("line_number"),
                            fix_suggestion=ev_dict.get("fix_suggestion"),
                            context=ev_dict.get("context", {})
                        )
                        # Avoid duplicates
                        if event not in self.events:
                            self.events.append(event)
            except (OSError, ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load existing diagnostics from {report_file}: {e}")

    def record(self, event: DiagnosticEvent) -> None:
        """Record a single diagnostic event."""
        self.events.append(event)

    def record_error(self, category: str, message: str, **kwargs: Any) -> DiagnosticEvent:
        """Helper to record an ERROR event."""
        event = DiagnosticEvent(severity=DiagnosticSeverity.ERROR, category=category, message=message, **kwargs)
        self.record(event)
        return event

    def record_warning(self, category: str, message: str, **kwargs: Any) -> DiagnosticEvent:
        """Helper to record a WARNING event."""
        event = DiagnosticEvent(severity=DiagnosticSeverity.WARNING, category=category, message=message, **kwargs)
        self.record(event)
        return event

    def record_info(self, category: str, message: str, **kwargs: Any) -> DiagnosticEvent:
        """Helper to record an INFO event."""
        event = DiagnosticEvent(severity=DiagnosticSeverity.INFO, category=category, message=message, **kwargs)
        self.record(event)
        return event

    def has_errors(self) -> bool:
        """Check if any ERROR events were recorded."""
        return any(e.severity == DiagnosticSeverity.ERROR for e in self.events)

    def print_report(self) -> None:
        """Print a compiler-style diagnostic report to the console."""
        if not self.events:
            logger.info("No diagnostic events recorded.")
            return

        use_emojis = get_emoji_enabled()
        red_flag = EMOJIS["error"] if use_emojis else "[FAIL]"
        yellow_flag = EMOJIS["warning"] if use_emojis else "[WARN]"
        info_flag = EMOJIS["info"] if use_emojis else "[INFO]"

        print(f"\n{'='*80}")
        print(f" DIAGNOSTIC REPORT: {self.project_name}")
        print(f"{'='*80}\n")

        errors = [e for e in self.events if e.severity == DiagnosticSeverity.ERROR]
        warnings = [e for e in self.events if e.severity == DiagnosticSeverity.WARNING]
        infos = [e for e in self.events if e.severity == DiagnosticSeverity.INFO]

        def _print_group(title: str, items: list[DiagnosticEvent], icon: str) -> None:
            if not items:
                return
            print(f"{icon} {title} ({len(items)})")
            print(f"{'-'*80}")
            for item in items:
                loc = ""
                if item.file_path:
                    loc = str(item.file_path)
                    if item.line_number:
                        loc += f":{item.line_number}"
                    loc = f"[{loc}] "

                print(f"  [{item.category}] {loc}{item.message}")
                if item.fix_suggestion:
                    print(f"      ↳ Fix: {item.fix_suggestion}")
            print()

        _print_group("RED FLAGS (Errors)", errors, red_flag)
        _print_group("YELLOW FLAGS (Warnings)", warnings, yellow_flag)
        _print_group("DIAGNOSTICS (Info)", infos, info_flag)

        print(f"{'='*80}\n")

    def save_report(self) -> None:
        """Save the diagnostic report to JSON if output_dir is configured."""
        if not self.output_dir:
            return

        if not self.events:
            return

        report_dir = self.output_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "diagnostics.json"

        # De-duplicate events by dictionary representation
        unique_events = []
        seen = set()
        for e in self.events:
            e_dict = e.to_dict()
            try:
                key = json.dumps(e_dict, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    unique_events.append(e)
            except (TypeError, ValueError):
                unique_events.append(e)

        data = {
            "project_name": self.project_name,
            "total_events": len(unique_events),
            "errors": sum(1 for e in unique_events if e.severity == DiagnosticSeverity.ERROR),
            "warnings": sum(1 for e in unique_events if e.severity == DiagnosticSeverity.WARNING),
            "events": [e.to_dict() for e in unique_events]
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved diagnostic report to {report_file}")
