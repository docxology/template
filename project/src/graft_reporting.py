"""Automated report generation for tree grafting experiments.

This module provides template-based report generation from grafting results,
summary statistics tables, key findings extraction, and comparison reports.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np


class GraftReportGenerator:
    """Generate reports from grafting experiment results."""
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """Initialize report generator.
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir) if output_dir else Path("output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_markdown_report(
        self,
        title: str,
        results: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """Generate markdown report.
        
        Args:
            title: Report title
            results: Results dictionary
            filename: Output filename (without extension)
            
        Returns:
            Path to generated report
        """
        if filename is None:
            filename = title.lower().replace(" ", "_")
        
        report_path = self.output_dir / f"{filename}.md"
        
        lines = [
            f"# {title}",
            "",
            f"**Generated**: {self._get_timestamp()}",
            "",
            "## Summary",
            ""
        ]
        
        # Add summary statistics
        if "summary" in results:
            lines.extend(self._format_summary(results["summary"]))
        
        # Add key findings
        if "findings" in results:
            lines.extend([
                "## Key Findings",
                ""
            ])
            for finding in results["findings"]:
                lines.append(f"- {finding}")
            lines.append("")
        
        # Add detailed results
        if "details" in results:
            lines.extend([
                "## Detailed Results",
                ""
            ])
            lines.extend(self._format_details(results["details"]))
        
        # Add tables
        if "tables" in results:
            lines.extend([
                "## Tables",
                ""
            ])
            for table_name, table_data in results["tables"].items():
                lines.extend(self._format_table(table_name, table_data))
        
        # Write report
        with open(report_path, 'w') as f:
            f.write("\n".join(lines))
        
        return report_path
    
    def generate_trial_report(
        self,
        success: np.ndarray,
        union_strength: Optional[np.ndarray] = None,
        healing_time: Optional[np.ndarray] = None,
        filename: Optional[str] = None
    ) -> Path:
        """Generate report for grafting trial results.
        
        Args:
            success: Success outcomes
            union_strength: Union strength values (optional)
            healing_time: Healing times (optional)
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        from graft_statistics import calculate_graft_statistics
        
        stats = calculate_graft_statistics(success, union_strength, healing_time)
        
        results = {
            "summary": {
                "n_trials": int(len(success)),
                "n_successful": int(np.sum(success)),
                "success_rate": float(np.mean(success))
            },
            "findings": [
                f"Overall success rate: {np.mean(success):.1%}",
                f"Total trials: {len(success)}"
            ],
            "details": {
                "statistics": {k: v.to_dict() for k, v in stats.items()}
            }
        }
        
        if filename is None:
            filename = "graft_trial_report"
        
        return self.generate_markdown_report("Grafting Trial Report", results, filename)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_summary(self, summary: Dict[str, Any]) -> List[str]:
        """Format summary section."""
        lines = []
        for key, value in summary.items():
            if isinstance(value, float):
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value:.3f}")
            else:
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        lines.append("")
        return lines
    
    def _format_details(self, details: Dict[str, Any]) -> List[str]:
        """Format details section."""
        lines = []
        for key, value in details.items():
            lines.append(f"### {key.replace('_', ' ').title()}")
            lines.append("")
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    lines.append(f"- {subkey}: {subvalue}")
            else:
                lines.append(str(value))
            lines.append("")
        return lines
    
    def _format_table(self, table_name: str, table_data: Dict[str, Any]) -> List[str]:
        """Format table section."""
        lines = [
            f"### {table_name.replace('_', ' ').title()}",
            "",
            "| " + " | ".join(table_data.get("headers", [])) + " |",
            "| " + " | ".join(["---"] * len(table_data.get("headers", []))) + " |"
        ]
        
        for row in table_data.get("rows", []):
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        
        lines.append("")
        return lines

