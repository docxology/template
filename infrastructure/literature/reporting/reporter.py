"""Comprehensive reporting system for literature operations.

Provides export capabilities for workflow statistics, paper metadata,
and summaries in multiple formats (JSON, CSV, HTML).
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.library.index import LibraryEntry
from infrastructure.literature.workflow.workflow import WorkflowResult

logger = get_logger(__name__)


class LiteratureReporter:
    """Comprehensive reporter for literature operations.
    
    Generates reports in multiple formats with statistics, metadata,
    and visualizations.
    """
    
    def __init__(self, output_dir: Path):
        """Initialize reporter.
        
        Args:
            output_dir: Directory for report outputs.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_workflow_report(
        self,
        workflow_result: WorkflowResult,
        library_entries: Optional[List[LibraryEntry]] = None,
        format: str = "json"
    ) -> Path:
        """Generate comprehensive workflow report.
        
        Args:
            workflow_result: Workflow result with statistics.
            library_entries: Optional library entries for detailed metadata.
            format: Output format ("json", "csv", "html", or "all").
            
        Returns:
            Path to generated report file(s).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"literature_report_{timestamp}"
        
        if format == "all":
            # Generate all formats
            json_path = self._generate_json_report(workflow_result, library_entries, base_name)
            csv_path = self._generate_csv_report(workflow_result, library_entries, base_name)
            html_path = self._generate_html_report(workflow_result, library_entries, base_name)
            logger.info(f"Generated reports: {json_path}, {csv_path}, {html_path}")
            return json_path  # Return primary format
        elif format == "json":
            return self._generate_json_report(workflow_result, library_entries, base_name)
        elif format == "csv":
            return self._generate_csv_report(workflow_result, library_entries, base_name)
        elif format == "html":
            return self._generate_html_report(workflow_result, library_entries, base_name)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _generate_json_report(
        self,
        workflow_result: WorkflowResult,
        library_entries: Optional[List[LibraryEntry]],
        base_name: str
    ) -> Path:
        """Generate JSON report."""
        output_path = self.output_dir / f"{base_name}.json"
        
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "literature_workflow",
                "version": "1.0"
            },
            "workflow_statistics": {
                "keywords": workflow_result.keywords,
                "papers_found": workflow_result.papers_found,
                "papers_downloaded": workflow_result.papers_downloaded,
                "papers_failed_download": workflow_result.papers_failed_download,
                "papers_already_existed": workflow_result.papers_already_existed,
                "papers_newly_downloaded": workflow_result.papers_newly_downloaded,
                "summaries_generated": workflow_result.summaries_generated,
                "summaries_failed": workflow_result.summaries_failed,
                "summaries_skipped": workflow_result.summaries_skipped,
                "total_time_seconds": workflow_result.total_time,
                "success_rate": workflow_result.success_rate,
                "completion_rate": workflow_result.completion_rate
            },
            "download_results": [
                {
                    "citation_key": r.citation_key,
                    "success": r.success,
                    "pdf_path": str(r.pdf_path) if r.pdf_path else None,
                    "failure_reason": r.failure_reason,
                    "failure_message": r.failure_message,
                    "already_existed": r.already_existed
                }
                for r in workflow_result.download_results
            ],
            "summarization_results": [
                {
                    "citation_key": r.citation_key,
                    "success": r.success,
                    "input_words": r.input_words,
                    "input_chars": r.input_chars,
                    "output_words": r.output_words,
                    "generation_time": r.generation_time,
                    "quality_score": r.quality_score,
                    "compression_ratio": r.compression_ratio,
                    "words_per_second": r.words_per_second,
                    "attempts": r.attempts,
                    "error": r.error,
                    "validation_errors": r.validation_errors,
                    "summary_path": str(r.summary_path) if r.summary_path else None,
                    "skipped": r.skipped
                }
                for r in workflow_result.summarization_results
            ]
        }
        
        # Add library metadata if available
        if library_entries:
            report_data["library_metadata"] = [
                {
                    "citation_key": entry.citation_key,
                    "title": entry.title,
                    "authors": entry.authors,
                    "year": entry.year,
                    "doi": entry.doi,
                    "source": entry.source,
                    "venue": entry.venue,
                    "citation_count": entry.citation_count,
                    "has_pdf": entry.pdf_path is not None,
                    "added_date": entry.added_date
                }
                for entry in library_entries
            ]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated JSON report: {output_path}")
        return output_path
    
    def _generate_csv_report(
        self,
        workflow_result: WorkflowResult,
        library_entries: Optional[List[LibraryEntry]],
        base_name: str
    ) -> Path:
        """Generate CSV report with paper metadata and statistics."""
        output_path = self.output_dir / f"{base_name}.csv"
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Citation Key", "Title", "Authors", "Year", "DOI", "Source",
                "Venue", "Citation Count", "Download Status", "Summary Status",
                "Quality Score", "Generation Time (s)", "Input Words", "Output Words",
                "Compression Ratio", "Words Per Second", "Error"
            ])
            
            # Create lookup dictionaries
        download_lookup = {r.citation_key: r for r in workflow_result.download_results}
        summary_lookup = {r.citation_key: r for r in workflow_result.summarization_results}
        
        # Write data rows
        papers_to_report = library_entries or []
        if not papers_to_report:
            # Use download results if no library entries
            papers_to_report = [
                LibraryEntry(
                    citation_key=r.citation_key,
                    title=r.result.title if r.result else "Unknown",
                    authors=r.result.authors if r.result else [],
                    year=r.result.year if r.result else None,
                    doi=r.result.doi if r.result else None,
                    source=r.result.source if r.result else "unknown",
                    venue=r.result.venue if r.result else None,
                    citation_count=r.result.citation_count if r.result else None,
                    pdf_path=str(r.pdf_path) if r.pdf_path else None,
                    added_date=datetime.now().isoformat(),
                    abstract=""
                )
                for r in workflow_result.download_results
            ]
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Citation Key", "Title", "Authors", "Year", "DOI", "Source",
                "Venue", "Citation Count", "Download Status", "Summary Status",
                "Quality Score", "Generation Time (s)", "Input Words", "Output Words",
                "Compression Ratio", "Words Per Second", "Error"
            ])
            
            # Write data rows
            for entry in papers_to_report:
                download_result = download_lookup.get(entry.citation_key)
                summary_result = summary_lookup.get(entry.citation_key)
                
                download_status = "success" if (download_result and download_result.success) else "failed" if download_result else "not_attempted"
                summary_status = "success" if (summary_result and summary_result.success) else "failed" if summary_result else "skipped" if (summary_result and summary_result.skipped) else "not_attempted"
                
                writer.writerow([
                    entry.citation_key,
                    entry.title,
                    "; ".join(entry.authors) if entry.authors else "",
                    entry.year or "",
                    entry.doi or "",
                    entry.source,
                    entry.venue or "",
                    entry.citation_count or "",
                    download_status,
                    summary_status,
                    summary_result.quality_score if summary_result else "",
                    summary_result.generation_time if summary_result else "",
                    summary_result.input_words if summary_result else "",
                    summary_result.output_words if summary_result else "",
                    f"{summary_result.compression_ratio:.2f}" if summary_result else "",
                    f"{summary_result.words_per_second:.2f}" if summary_result else "",
                    summary_result.error or (download_result.failure_message if download_result and not download_result.success else "")
                ])
        
        logger.info(f"Generated CSV report: {output_path}")
        return output_path
    
    def _generate_html_report(
        self,
        workflow_result: WorkflowResult,
        library_entries: Optional[List[LibraryEntry]],
        base_name: str
    ) -> Path:
        """Generate HTML report with visualizations."""
        output_path = self.output_dir / f"{base_name}.html"
        
        # Calculate statistics
        total_papers = workflow_result.papers_found
        download_success_rate = (workflow_result.papers_downloaded / max(1, total_papers)) * 100
        summary_success_rate = (workflow_result.summaries_generated / max(1, workflow_result.papers_downloaded)) * 100
        
        avg_quality = 0.0
        if workflow_result.summarization_results:
            successful_summaries = [r for r in workflow_result.summarization_results if r.success]
            if successful_summaries:
                avg_quality = sum(r.quality_score for r in successful_summaries) / len(successful_summaries)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Literature Workflow Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .success {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .failed {{
            color: #f44336;
            font-weight: bold;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background-color: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background-color: #4CAF50;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Literature Workflow Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <h2>Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_papers}</div>
                <div class="stat-label">Papers Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{workflow_result.papers_downloaded}</div>
                <div class="stat-label">Papers Downloaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{workflow_result.summaries_generated}</div>
                <div class="stat-label">Summaries Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{download_success_rate:.1f}%</div>
                <div class="stat-label">Download Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary_success_rate:.1f}%</div>
                <div class="stat-label">Summary Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_quality:.2f}</div>
                <div class="stat-label">Average Quality Score</div>
            </div>
        </div>
        
        <h2>Download Results</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {download_success_rate}%"></div>
        </div>
        <p>Success: {workflow_result.papers_downloaded} / {total_papers} ({download_success_rate:.1f}%)</p>
        
        <h2>Summarization Results</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {summary_success_rate}%"></div>
        </div>
        <p>Success: {workflow_result.summaries_generated} / {workflow_result.papers_downloaded} ({summary_success_rate:.1f}%)</p>
        
        <h2>Paper Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Citation Key</th>
                    <th>Title</th>
                    <th>Download</th>
                    <th>Summary</th>
                    <th>Quality</th>
                    <th>Time (s)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add paper rows
        download_lookup = {r.citation_key: r for r in workflow_result.download_results}
        summary_lookup = {r.citation_key: r for r in workflow_result.summarization_results}
        
        papers_to_report = library_entries or []
        if not papers_to_report:
            papers_to_report = [
                LibraryEntry(
                    citation_key=r.citation_key,
                    title=r.result.title if r.result else "Unknown",
                    authors=[],
                    year=None,
                    doi=None,
                    source="unknown",
                    venue=None,
                    citation_count=None,
                    pdf_path=str(r.pdf_path) if r.pdf_path else None,
                    added_date=datetime.now().isoformat(),
                    abstract=""
                )
                for r in workflow_result.download_results
            ]
        
        for entry in papers_to_report[:50]:  # Limit to first 50 for HTML
            download_result = download_lookup.get(entry.citation_key)
            summary_result = summary_lookup.get(entry.citation_key)
            
            download_status = "✓" if (download_result and download_result.success) else "✗" if download_result else "-"
            summary_status = "✓" if (summary_result and summary_result.success) else "✗" if summary_result else "-"
            
            download_class = "success" if (download_result and download_result.success) else "failed" if download_result else ""
            summary_class = "success" if (summary_result and summary_result.success) else "failed" if summary_result else ""
            
            quality = f"{summary_result.quality_score:.2f}" if summary_result else "-"
            time_taken = f"{summary_result.generation_time:.1f}" if summary_result else "-"
            
            html_content += f"""
                <tr>
                    <td>{entry.citation_key}</td>
                    <td>{entry.title[:60]}...</td>
                    <td class="{download_class}">{download_status}</td>
                    <td class="{summary_class}">{summary_status}</td>
                    <td>{quality}</td>
                    <td>{time_taken}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        
        <h2>Keywords</h2>
        <p>{', '.join(workflow_result.keywords)}</p>
        
        <h2>Timing</h2>
        <p><strong>Total Time:</strong> {:.1f} seconds</p>
        <p><strong>Average per Paper:</strong> {:.1f} seconds</p>
    </div>
</body>
</html>
""".format(
            workflow_result.total_time,
            workflow_result.total_time / max(1, total_papers)
        )
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {output_path}")
        return output_path

