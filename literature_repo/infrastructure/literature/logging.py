"""Structured logging for literature search operations.

Provides enhanced logging capabilities including:
- JSON format option for programmatic analysis
- Progress indicators for long-running operations
- Performance metrics logging
- Detailed error context
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class LogFormat(Enum):
    """Log output format options."""
    TEXT = "text"
    JSON = "json"


@dataclass
class LogEntry:
    """Structured log entry for literature operations."""
    timestamp: str
    level: str
    operation: str
    message: str
    source: Optional[str] = None
    paper_id: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_text(self) -> str:
        """Convert to human-readable text format."""
        parts = [f"[{self.timestamp}] [{self.level}]"]
        if self.source:
            parts.append(f"[{self.source}]")
        if self.paper_id:
            parts.append(f"[{self.paper_id}]")
        parts.append(f"{self.operation}: {self.message}")
        
        if self.metrics:
            metrics_str = ", ".join(f"{k}={v}" for k, v in self.metrics.items())
            parts.append(f"({metrics_str})")
        
        if self.error:
            parts.append(f"ERROR: {self.error.get('message', 'Unknown error')}")
        
        return " ".join(parts)


class StructuredLogger:
    """Structured logger for literature operations.
    
    Provides structured logging with optional JSON output and progress tracking.
    """
    
    def __init__(
        self,
        format: LogFormat = LogFormat.TEXT,
        output_file: Optional[Path] = None,
        enable_progress: bool = True
    ):
        """Initialize structured logger.
        
        Args:
            format: Log output format (TEXT or JSON).
            output_file: Optional file path for log output.
            enable_progress: Enable progress indicators.
        """
        self.format = format
        self.output_file = output_file
        self.enable_progress = enable_progress
        self.entries: List[LogEntry] = []
        self._operation_start_times: Dict[str, float] = {}
        self._progress_counters: Dict[str, int] = {}
    
    def log(
        self,
        level: str,
        operation: str,
        message: str,
        source: Optional[str] = None,
        paper_id: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a structured entry.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG).
            operation: Operation name (e.g., "search", "download", "summarize").
            message: Log message.
            source: Source name (e.g., "arxiv", "semanticscholar").
            paper_id: Paper citation key or identifier.
            metrics: Performance metrics (timing, throughput, etc.).
            error: Error information if applicable.
            context: Additional context information.
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            operation=operation,
            message=message,
            source=source,
            paper_id=paper_id,
            metrics=metrics,
            error=error,
            context=context
        )
        
        self.entries.append(entry)
        
        # Output based on format
        if self.format == LogFormat.JSON:
            output = json.dumps(entry.to_dict(), indent=2)
        else:
            output = entry.to_text()
        
        # Write to file if specified
        if self.output_file:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(output + "\n")
        
        # Also log to standard logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(output)
    
    def start_operation(self, operation: str, message: str = "") -> None:
        """Start timing an operation.
        
        Args:
            operation: Operation name.
            message: Optional start message.
        """
        self._operation_start_times[operation] = time.time()
        if message:
            self.log("INFO", operation, f"Starting: {message}")
    
    def end_operation(
        self,
        operation: str,
        message: str = "",
        success: bool = True,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """End timing an operation and log results.
        
        Args:
            operation: Operation name.
            message: Optional completion message.
            success: Whether operation succeeded.
            metrics: Additional metrics to include.
        """
        start_time = self._operation_start_times.pop(operation, None)
        duration = time.time() - start_time if start_time else None
        
        op_metrics = metrics or {}
        if duration is not None:
            op_metrics["duration_seconds"] = duration
        
        level = "INFO" if success else "ERROR"
        status = "completed" if success else "failed"
        full_message = f"{status.capitalize()}: {message}" if message else f"Operation {status}"
        
        self.log(
            level=level,
            operation=operation,
            message=full_message,
            metrics=op_metrics
        )
    
    def log_progress(
        self,
        operation: str,
        current: int,
        total: int,
        item_name: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log progress for a long-running operation.
        
        Args:
            operation: Operation name.
            current: Current item number.
            total: Total items.
            item_name: Optional name of current item.
            metrics: Additional metrics.
        """
        if not self.enable_progress:
            return
        
        percentage = (current / total * 100) if total > 0 else 0
        progress_metrics = {
            "current": current,
            "total": total,
            "percentage": f"{percentage:.1f}%"
        }
        
        if metrics:
            progress_metrics.update(metrics)
        
        # Calculate ETA if we have timing data
        if operation in self._operation_start_times:
            elapsed = time.time() - self._operation_start_times[operation]
            if current > 0:
                rate = current / elapsed
                remaining = total - current
                eta_seconds = remaining / rate if rate > 0 else 0
                progress_metrics["eta_seconds"] = eta_seconds
                progress_metrics["items_per_second"] = rate
        
        message = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if item_name:
            message += f" - {item_name}"
        
        self.log(
            level="INFO",
            operation=operation,
            message=message,
            metrics=progress_metrics
        )
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        source: Optional[str] = None,
        paper_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error with full context.
        
        Args:
            operation: Operation name.
            error: Exception that occurred.
            source: Source name if applicable.
            paper_id: Paper ID if applicable.
            context: Additional context.
        """
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
        }
        
        if hasattr(error, "context"):
            error_info["context"] = error.context if isinstance(error.context, dict) else {}
        
        if hasattr(error, "__cause__") and error.__cause__:
            error_info["cause"] = {
                "type": type(error.__cause__).__name__,
                "message": str(error.__cause__)
            }
        
        self.log(
            level="ERROR",
            operation=operation,
            message=f"Error in {operation}: {error}",
            source=source,
            paper_id=paper_id,
            error=error_info,
            context=context
        )
    
    def export_logs(self, output_path: Path, format: Optional[LogFormat] = None) -> None:
        """Export all logged entries to a file.
        
        Args:
            output_path: Path to output file.
            format: Output format (uses instance format if None).
        """
        output_format = format or self.format
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            if output_format == LogFormat.JSON:
                json.dump([entry.to_dict() for entry in self.entries], f, indent=2)
            else:
                for entry in self.entries:
                    f.write(entry.to_text() + "\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about logged operations.
        
        Returns:
            Dictionary with operation statistics.
        """
        stats = {
            "total_entries": len(self.entries),
            "by_level": {},
            "by_operation": {},
            "errors": []
        }
        
        for entry in self.entries:
            # Count by level
            stats["by_level"][entry.level] = stats["by_level"].get(entry.level, 0) + 1
            
            # Count by operation
            if entry.operation not in stats["by_operation"]:
                stats["by_operation"][entry.operation] = {
                    "count": 0,
                    "errors": 0,
                    "total_duration": 0.0
                }
            stats["by_operation"][entry.operation]["count"] += 1
            
            if entry.error:
                stats["by_operation"][entry.operation]["errors"] += 1
                stats["errors"].append(entry.to_dict())
            
            if entry.metrics and "duration_seconds" in entry.metrics:
                stats["by_operation"][entry.operation]["total_duration"] += entry.metrics["duration_seconds"]
        
        return stats

