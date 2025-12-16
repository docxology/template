"""Error aggregation system for pipeline execution.

Collects, categorizes, and provides actionable fixes for errors and warnings
encountered during pipeline execution.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ErrorEntry:
    """Single error or warning entry."""
    type: str  # 'test_failure', 'validation_error', 'stage_failure', etc.
    message: str
    stage: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    severity: str = 'error'  # 'error', 'warning', 'info'
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.type,
            'message': self.message,
            'stage': self.stage,
            'file': self.file,
            'line': self.line,
            'severity': self.severity,
            'suggestions': self.suggestions,
            'context': self.context,
        }


class ErrorAggregator:
    """Aggregate and categorize errors from pipeline execution."""
    
    def __init__(self):
        """Initialize error aggregator."""
        self.errors: List[ErrorEntry] = []
        self.warnings: List[ErrorEntry] = []
    
    def add_error(
        self,
        error_type: str,
        message: str,
        stage: Optional[str] = None,
        file: Optional[str] = None,
        line: Optional[int] = None,
        severity: str = 'error',
        suggestions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an error or warning.
        
        Args:
            error_type: Type of error (e.g., 'test_failure', 'validation_error')
            message: Error message
            stage: Stage where error occurred
            file: File where error occurred
            line: Line number (if applicable)
            severity: Error severity ('error', 'warning', 'info')
            suggestions: List of actionable suggestions
            context: Additional context dictionary
        """
        entry = ErrorEntry(
            type=error_type,
            message=message,
            stage=stage,
            file=file,
            line=line,
            severity=severity,
            suggestions=suggestions or [],
            context=context or {},
        )
        
        if severity == 'error':
            self.errors.append(entry)
        else:
            self.warnings.append(entry)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get error summary.
        
        Returns:
            Dictionary with error summary
        """
        # Categorize errors by type
        errors_by_type: Dict[str, List[ErrorEntry]] = {}
        for error in self.errors:
            if error.type not in errors_by_type:
                errors_by_type[error.type] = []
            errors_by_type[error.type].append(error)
        
        warnings_by_type: Dict[str, List[ErrorEntry]] = {}
        for warning in self.warnings:
            if warning.type not in warnings_by_type:
                warnings_by_type[warning.type] = []
            warnings_by_type[warning.type].append(warning)
        
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors_by_type': {k: len(v) for k, v in errors_by_type.items()},
            'warnings_by_type': {k: len(v) for k, v in warnings_by_type.items()},
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
        }
    
    def get_actionable_fixes(self) -> List[Dict[str, Any]]:
        """Get actionable fixes for errors.
        
        Returns:
            List of fix dictionaries with priority and actions
        """
        fixes = []
        
        # Group errors by type and provide fixes
        error_types = {}
        for error in self.errors:
            if error.type not in error_types:
                error_types[error.type] = []
            error_types[error.type].append(error)
        
        for error_type, errors in error_types.items():
            if error_type == 'test_failure':
                fixes.append({
                    'priority': 'high',
                    'issue': f'{len(errors)} test failure(s)',
                    'actions': [
                        'Review test output for failure details',
                        'Run failing tests individually: pytest path/to/test_file.py::test_name',
                        'Check test data and fixtures',
                        'Review recent code changes',
                    ],
                    'documentation': 'docs/TESTING_GUIDE.md',
                })
            elif error_type == 'validation_error':
                fixes.append({
                    'priority': 'high',
                    'issue': f'{len(errors)} validation error(s)',
                    'actions': [
                        'Review validation report: output/reports/validation_report.md',
                        'Check PDF compilation logs: output/pdf/*_compile.log',
                        'Verify markdown syntax and references',
                        'Ensure all required files are generated',
                    ],
                    'documentation': 'docs/TROUBLESHOOTING_GUIDE.md',
                })
            elif error_type == 'stage_failure':
                fixes.append({
                    'priority': 'high',
                    'issue': f'{len(errors)} stage failure(s)',
                    'actions': [
                        'Review stage execution logs',
                        'Check for missing dependencies',
                        'Verify input files exist',
                        'Review error messages above',
                    ],
                    'documentation': 'docs/TROUBLESHOOTING_GUIDE.md',
                })
            else:
                # Generic fix
                fixes.append({
                    'priority': 'medium',
                    'issue': f'{len(errors)} {error_type} error(s)',
                    'actions': errors[0].suggestions if errors[0].suggestions else [
                        'Review error messages',
                        'Check logs for details',
                    ],
                })
        
        return fixes
    
    def save_report(self, output_dir: Path) -> Path:
        """Save error summary report.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            Path to saved report
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = self.get_summary()
        summary['timestamp'] = datetime.now().isoformat()
        summary['actionable_fixes'] = self.get_actionable_fixes()
        
        json_path = output_dir / "error_summary.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate markdown report
        md_path = output_dir / "error_summary.md"
        md_content = self._generate_markdown_report(summary)
        md_path.write_text(md_content)
        
        return json_path
    
    def _generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Generate Markdown error summary report.
        
        Args:
            summary: Error summary dictionary
            
        Returns:
            Markdown formatted report
        """
        lines = [
            "# Error Summary Report",
            "",
            f"**Generated:** {summary.get('timestamp', 'unknown')}",
            "",
            f"**Total Errors:** {summary.get('total_errors', 0)}",
            f"**Total Warnings:** {summary.get('total_warnings', 0)}",
            "",
        ]
        
        # Errors by type
        if summary.get('errors_by_type'):
            lines.append("## Errors by Type")
            lines.append("")
            for error_type, count in summary['errors_by_type'].items():
                lines.append(f"- **{error_type}:** {count}")
            lines.append("")
        
        # Actionable fixes
        if summary.get('actionable_fixes'):
            lines.append("## Actionable Fixes")
            lines.append("")
            for fix in summary['actionable_fixes']:
                priority_emoji = "🔴" if fix['priority'] == 'high' else "🟡"
                lines.append(f"### {priority_emoji} {fix['issue']} ({fix['priority']} priority)")
                lines.append("")
                lines.append("**Actions:**")
                for i, action in enumerate(fix['actions'], 1):
                    lines.append(f"{i}. {action}")
                if 'documentation' in fix:
                    lines.append(f"\n**Documentation:** {fix['documentation']}")
                lines.append("")
        
        # Error details (first 10)
        if summary.get('errors'):
            lines.append("## Error Details")
            lines.append("")
            for i, error in enumerate(summary['errors'][:10], 1):
                lines.append(f"### Error {i}")
                lines.append(f"- **Type:** {error.get('type', 'unknown')}")
                lines.append(f"- **Message:** {error.get('message', 'N/A')}")
                if error.get('stage'):
                    lines.append(f"- **Stage:** {error.get('stage')}")
                if error.get('file'):
                    lines.append(f"- **File:** {error.get('file')}")
                if error.get('suggestions'):
                    lines.append("- **Suggestions:**")
                    for suggestion in error['suggestions']:
                        lines.append(f"  - {suggestion}")
                lines.append("")
            
            if len(summary['errors']) > 10:
                lines.append(f"*... and {len(summary['errors']) - 10} more errors*")
        
        return "\n".join(lines)


# Global error aggregator instance
_global_aggregator: Optional[ErrorAggregator] = None


def get_error_aggregator() -> ErrorAggregator:
    """Get global error aggregator instance.
    
    Returns:
        ErrorAggregator instance
    """
    global _global_aggregator
    if _global_aggregator is None:
        _global_aggregator = ErrorAggregator()
    return _global_aggregator


def reset_error_aggregator() -> None:
    """Reset global error aggregator (for testing)."""
    global _global_aggregator
    _global_aggregator = None
















