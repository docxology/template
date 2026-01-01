"""Reporting utilities - thin wrapper around infrastructure reporting."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Lazy imports to avoid import issues during test collection
def _get_infra_generate_pipeline_report():
    from infrastructure.reporting.pipeline_reporter import generate_pipeline_report
    return generate_pipeline_report

def _get_infra_save_pipeline_report():
    from infrastructure.reporting.pipeline_reporter import save_pipeline_report
    return save_pipeline_report

def _get_infra_ErrorAggregator():
    from infrastructure.reporting.error_aggregator import ErrorAggregator
    return ErrorAggregator

def get_error_aggregator():
    """Get error aggregator instance from infrastructure.

    Returns:
        ErrorAggregator instance for collecting and reporting errors
    """
    ErrorAggregator = _get_infra_ErrorAggregator()
    return ErrorAggregator()


# Wrapper functions for __init__.py imports
def generate_pipeline_report(*args, **kwargs):
    """Generate pipeline report using infrastructure."""
    func = _get_infra_generate_pipeline_report()
    return func(*args, **kwargs)


def save_pipeline_report(*args, **kwargs):
    """Save pipeline report using infrastructure."""
    func = _get_infra_save_pipeline_report()
    return func(*args, **kwargs)


class ReportGenerator:
    """Generate reports from simulation and analysis results."""

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

    def generate_latex_report(
        self,
        title: str,
        results: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """Generate LaTeX report.

        Args:
            title: Report title
            results: Results dictionary
            filename: Output filename (without extension)

        Returns:
            Path to generated report
        """
        if filename is None:
            filename = title.lower().replace(" ", "_")

        report_path = self.output_dir / f"{filename}.tex"

        lines = [
            "\\documentclass{article}",
            "\\usepackage{booktabs}",
            "\\usepackage{graphicx}",
            "\\begin{document}",
            "",
            f"\\title{{{title}}}",
            f"\\date{{{self._get_timestamp()}}}",
            "\\maketitle",
            "",
            "\\section{Summary}",
            ""
        ]

        # Add summary
        if "summary" in results:
            lines.extend(self._format_summary_latex(results["summary"]))

        # Add tables
        if "tables" in results:
            lines.extend([
                "\\section{Tables}",
                ""
            ])
            for table_name, table_data in results["tables"].items():
                lines.extend(self._format_table_latex(table_name, table_data))

        lines.extend([
            "",
            "\\end{document}"
        ])

        with open(report_path, 'w') as f:
            f.write("\n".join(lines))

        return report_path

    def generate_html_report(
        self,
        title: str,
        results: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """Generate HTML report.

        Args:
            title: Report title
            results: Results dictionary
            filename: Output filename (without extension)

        Returns:
            Path to generated report
        """
        if filename is None:
            filename = title.lower().replace(" ", "_")

        report_path = self.output_dir / f"{filename}.html"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Generated:</strong> {self._get_timestamp()}</p>

    <h2>Summary</h2>
    {self._format_summary_html(results.get("summary", {}))}

    <h2>Key Findings</h2>
    <ul>
"""

        if "findings" in results:
            for finding in results["findings"]:
                html += f"        <li>{finding}</li>\n"

        html += """    </ul>
</body>
</html>"""

        with open(report_path, 'w') as f:
            f.write(html)

        return report_path

    def save_structured_report(
        self,
        stage_name: str,
        results: Dict[str, Any],
        pipeline_duration: float = 0.0,
    ) -> Dict[str, Path]:
        """Persist a structured multi-format report using infrastructure.reporting.

        Args:
            stage_name: Logical name of the stage producing this report.
            results: Result payload to persist under `validation_results`.
            pipeline_duration: Optional duration for the stage.

        Returns:
            Mapping of format to saved paths.
        """
        error_agg = get_error_aggregator()
        generate_pipeline_report = _get_infra_generate_pipeline_report()
        report = generate_pipeline_report(
            stage_results=[
                {"name": stage_name, "exit_code": 0, "duration": pipeline_duration}
            ],
            total_duration=pipeline_duration,
            repo_root=Path("."),
            validation_results=results,
            error_summary=error_agg.get_summary(),
        )
        save_pipeline_report = _get_infra_save_pipeline_report()
        return save_pipeline_report(report, self.output_dir)

    def extract_key_findings(
        self,
        results: Dict[str, Any],
        threshold: float = 0.1
    ) -> List[str]:
        """Extract key findings from results.

        Args:
            results: Results dictionary
            threshold: Threshold for significance

        Returns:
            List of key findings
        """
        findings = []

        # Extract significant results
        if "metrics" in results:
            metrics = results["metrics"]
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    findings.append(f"{metric_name}: {value:.4f}")

        # Extract convergence information
        if "convergence" in results:
            conv = results["convergence"]
            if conv.get("is_converged", False):
                findings.append(f"Simulation converged in {conv.get('iterations', 'N/A')} iterations")
            else:
                findings.append("Simulation did not converge within tolerance")

        # Extract performance information
        if "performance" in results:
            perf = results["performance"]
            if "best_method" in perf:
                findings.append(f"Best performing method: {perf['best_method']}")

        return findings

    def create_comparison_report(
        self,
        runs: List[Dict[str, Any]],
        comparison_metrics: List[str]
    ) -> Dict[str, Any]:
        """Create comparison report across multiple runs.

        Args:
            runs: List of run results
            comparison_metrics: Metrics to compare

        Returns:
            Comparison report dictionary
        """
        report = {
            "n_runs": len(runs),
            "comparison_metrics": comparison_metrics,
            "comparisons": {}
        }

        for metric in comparison_metrics:
            values = []
            for run in runs:
                if metric in run.get("metrics", {}):
                    values.append(run["metrics"][metric])

            if values:
                report["comparisons"][metric] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "values": values
                }

        return report

    def _format_summary(self, summary: Dict[str, Any]) -> List[str]:
        """Format summary section."""
        lines = []
        for key, value in summary.items():
            if isinstance(value, (int, float)):
                lines.append(f"- **{key}**: {value:.4f}")
            else:
                lines.append(f"- **{key}**: {value}")
        lines.append("")
        return lines

    def _format_summary_latex(self, summary: Dict[str, Any]) -> List[str]:
        """Format summary for LaTeX."""
        lines = []
        for key, value in summary.items():
            if isinstance(value, (int, float)):
                lines.append(f"{key}: {value:.4f}\\\\")
            else:
                lines.append(f"{key}: {value}\\\\")
        lines.append("")
        return lines

    def _format_summary_html(self, summary: Dict[str, Any]) -> str:
        """Format summary for HTML."""
        html = "<ul>\n"
        for key, value in summary.items():
            if isinstance(value, (int, float)):
                html += f"    <li><strong>{key}</strong>: {value:.4f}</li>\n"
            else:
                html += f"    <li><strong>{key}</strong>: {value}</li>\n"
        html += "</ul>"
        return html

    def _format_details(self, details: Dict[str, Any]) -> List[str]:
        """Format details section."""
        lines = []
        for section, content in details.items():
            lines.append(f"### {section}")
            lines.append("")
            if isinstance(content, dict):
                for key, value in content.items():
                    lines.append(f"- {key}: {value}")
            elif isinstance(content, list):
                for item in content:
                    lines.append(f"- {item}")
            else:
                lines.append(str(content))
            lines.append("")
        return lines

    def _format_table(self, name: str, data: Dict[str, List[Any]]) -> List[str]:
        """Format table for markdown."""
        lines = [
            f"### {name}",
            ""
        ]

        # Get headers
        headers = list(data.keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Get number of rows
        n_rows = max(len(v) for v in data.values()) if data else 0

        # Format rows
        for i in range(n_rows):
            row = [str(data[h][i]) if i < len(data[h]) else "" for h in headers]
            lines.append("| " + " | ".join(row) + " |")

        lines.append("")
        return lines

    def _format_table_latex(self, name: str, data: Dict[str, List[Any]]) -> List[str]:
        """Format table for LaTeX."""
        lines = [
            f"\\subsection{{{name}}}",
            "",
            "\\begin{table}[h]",
            "\\centering",
            "\\begin{tabular}{" + "c" * len(data) + "}",
            "\\toprule"
        ]

        # Headers
        headers = list(data.keys())
        lines.append(" & ".join(headers) + " \\\\")
        lines.append("\\midrule")

        # Rows
        n_rows = max(len(v) for v in data.values()) if data else 0
        for i in range(n_rows):
            row = [str(data[h][i]) if i < len(data[h]) else "" for h in headers]
            lines.append(" & ".join(row) + " \\\\")

        lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            f"\\caption{{{name}}}",
            "\\end{table}",
            ""
        ])

        return lines

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Re-export infrastructure functions and local classes for backward compatibility
__all__ = [
    'generate_pipeline_report',
    'save_pipeline_report',
    'get_error_aggregator',
    'ReportGenerator'
]