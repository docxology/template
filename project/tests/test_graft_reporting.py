"""Comprehensive tests for graft_reporting module."""
import tempfile
from pathlib import Path

import numpy as np
import pytest

from graft_reporting import GraftReportGenerator


class TestReportGenerator:
    """Test report generator."""
    
    def test_markdown_report(self, tmp_path):
        """Test markdown report generation."""
        generator = GraftReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {"n_trials": 100, "success_rate": 0.75},
            "findings": ["High success rate", "Good compatibility"]
        }
        report_path = generator.generate_markdown_report("Test Report", results)
        assert report_path.exists()
        assert report_path.suffix == ".md"
    
    def test_trial_report(self, tmp_path):
        """Test trial report generation."""
        generator = GraftReportGenerator(output_dir=str(tmp_path))
        success = np.array([1, 1, 0, 1, 0])
        union_strength = np.array([0.8, 0.9, np.nan, 0.7, np.nan])
        report_path = generator.generate_trial_report(success, union_strength)
        assert report_path.exists()
    
    def test_markdown_report_with_tables(self, tmp_path):
        """Test markdown report generation with tables."""
        generator = GraftReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {"n_trials": 100, "success_rate": 0.75},
            "findings": ["High success rate"],
            "tables": {
                "technique_comparison": {
                    "headers": ["Technique", "Success Rate", "N"],
                    "rows": [
                        ["Whip", "0.85", "50"],
                        ["Cleft", "0.70", "30"],
                        ["Bark", "0.65", "20"]
                    ]
                }
            }
        }
        report_path = generator.generate_markdown_report("Test Report with Tables", results)
        assert report_path.exists()
        
        # Verify table content in report
        content = report_path.read_text()
        assert "Technique Comparison" in content
        assert "Whip" in content
        assert "0.85" in content
    
    def test_markdown_report_with_string_details(self, tmp_path):
        """Test markdown report with string details (non-dict)."""
        generator = GraftReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {"n_trials": 100},
            "details": {
                "notes": "This is a string note, not a dict"
            }
        }
        report_path = generator.generate_markdown_report("Test Report with String Details", results)
        assert report_path.exists()
        
        # Verify string content in report
        content = report_path.read_text()
        assert "This is a string note" in content
    
    def test_markdown_report_complete_structure(self, tmp_path):
        """Test markdown report with complete data structure."""
        generator = GraftReportGenerator(output_dir=str(tmp_path))
        results = {
            "summary": {
                "n_trials": 100,
                "success_rate": 0.75,
                "mean_union_strength": 0.82
            },
            "findings": [
                "High success rate",
                "Good compatibility",
                "Optimal environmental conditions"
            ],
            "details": {
                "statistics": {
                    "mean": 0.75,
                    "std": 0.15
                },
                "notes": "String note"
            },
            "tables": {
                "monthly_analysis": {
                    "headers": ["Month", "Success Rate"],
                    "rows": [
                        ["March", "0.80"],
                        ["April", "0.85"],
                        ["May", "0.70"]
                    ]
                }
            }
        }
        report_path = generator.generate_markdown_report("Complete Test Report", results)
        assert report_path.exists()
        
        # Verify all sections present
        content = report_path.read_text()
        assert "Summary" in content
        assert "Key Findings" in content
        assert "Detailed Results" in content
        assert "Tables" in content
        assert "Monthly Analysis" in content


if __name__ == "__main__":
    pytest.main([__file__])

