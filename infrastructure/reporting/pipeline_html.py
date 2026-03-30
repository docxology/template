"""HTML report generation for pipeline execution results.

Generates HTML-formatted reports from PipelineReport data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from infrastructure.core.logging.helpers import format_duration

if TYPE_CHECKING:
    from .pipeline_report_model import PipelineReport


def generate_html_report(report: PipelineReport) -> str:
    """Generate HTML format pipeline report."""
    # Calculate summary statistics
    passed = sum(1 for s in report.stages if s.status == "passed")
    failed = sum(1 for s in report.stages if s.status == "failed")
    total = len(report.stages)
    success_rate = (passed / total * 100) if total > 0 else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Execution Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-passed {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Pipeline Execution Report</h1>
        <p><strong>Generated:</strong> {report.timestamp}</p>
        <p><strong>Total Duration:</strong> {format_duration(report.total_duration)}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>Stages Executed</h3>
            <div class="value">{total}</div>
        </div>
        <div class="summary-card">
            <h3>Stages Passed</h3>
            <div class="value" style="color: #28a745;">{passed}</div>
        </div>
        <div class="summary-card">
            <h3>Stages Failed</h3>
            <div class="value" style="color: #dc3545;">{failed}</div>
        </div>
        <div class="summary-card">
            <h3>Success Rate</h3>
            <div class="value">{success_rate:.1f}%</div>
        </div>
    </div>

    <div class="section">
        <h2>Stage Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Exit Code</th>
                </tr>
            </thead>
            <tbody>
"""

    for stage in report.stages:
        status_class = "status-passed" if stage.status == "passed" else "status-failed"
        status_text = "\u2705 Passed" if stage.status == "passed" else "\u274c Failed"
        html += f"""                <tr>
                    <td>{stage.name}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{format_duration(stage.duration)}</td>
                    <td>{stage.exit_code}</td>
                </tr>
"""

    html += """            </tbody>
        </table>
    </div>
"""

    # Add test results section if available
    if report.test_results:
        summary = report.test_results.get("summary", {})
        html += f"""    <div class="section">
        <h2>Test Results</h2>
        <p><strong>Total Tests:</strong> {summary.get("total_tests", 0)}</p>
        <p><strong>Passed:</strong> {summary.get("total_passed", 0)}</p>
        <p><strong>Failed:</strong> {summary.get("total_failed", 0)}</p>
        <p><strong>Skipped:</strong> {summary.get("total_skipped", 0)}</p>
"""
        if "infrastructure_coverage" in summary:
            html += f"        <p><strong>Infrastructure Coverage:</strong> {summary['infrastructure_coverage']:.2f}%</p>\n"  # noqa: E501
        if "project_coverage" in summary:
            html += f"        <p><strong>Project Coverage:</strong> {summary['project_coverage']:.2f}%</p>\n"  # noqa: E501
        html += "    </div>\n"

    html += """</body>
</html>"""

    return html
