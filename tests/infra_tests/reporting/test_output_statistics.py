"""Tests for infrastructure.reporting.output_statistics module.

Tests output file statistics collection and report generation.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.reporting.output_statistics import (
    collect_output_statistics,
    generate_detailed_output_report,
    log_output_summary,
)


class TestCollectOutputStatistics:
    """Tests for collect_output_statistics."""

    def test_empty_project(self, tmp_path: Path):
        """Project with empty output dir should return zero counts."""
        project_dir = tmp_path / "projects" / "test"
        output_dir = project_dir / "output"
        output_dir.mkdir(parents=True)

        stats = collect_output_statistics(tmp_path, "test")
        assert stats["total_files"] == 0
        assert stats["total_size_mb"] == 0.0
        assert stats["pdf_files"] == 0
        assert len(stats["missing_expected_files"]) > 0  # No subdirs exist

    def test_with_pdf_files(self, tmp_path: Path):
        """Should count PDF files correctly."""
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4" + b"x" * 1000)
        (pdf_dir / "other.pdf").write_bytes(b"%PDF-1.4" + b"x" * 2000)

        stats = collect_output_statistics(tmp_path, "test")
        assert stats["pdf_files"] == 2
        assert stats["total_files"] >= 2

    def test_with_multiple_directories(self, tmp_path: Path):
        """Should collect stats from all output subdirectories."""
        project_dir = tmp_path / "projects" / "test"
        for subdir in ["pdf", "figures", "data", "reports"]:
            d = project_dir / "output" / subdir
            d.mkdir(parents=True)
            (d / f"file.{subdir[:3]}").write_bytes(b"content" * 100)

        stats = collect_output_statistics(tmp_path, "test")
        assert stats["total_files"] == 4
        assert stats["pdf_files"] == 1
        assert stats["figures"] == 1
        assert stats["data_files"] == 1

    def test_largest_files_tracking(self, tmp_path: Path):
        """Should track the largest files across directories."""
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "small.pdf").write_bytes(b"x" * 100)
        (pdf_dir / "large.pdf").write_bytes(b"x" * 10000)

        stats = collect_output_statistics(tmp_path, "test")
        assert len(stats["largest_files"]) > 0
        # First should be the largest
        assert float(stats["largest_files"][0]["size_mb"]) >= float(
            stats["largest_files"][-1]["size_mb"]
        )

    def test_missing_combined_pdf(self, tmp_path: Path):
        """Should report missing combined PDF."""
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)

        stats = collect_output_statistics(tmp_path, "test")
        assert any("test_combined.pdf" in m for m in stats["missing_expected_files"])

    def test_combined_pdf_present(self, tmp_path: Path):
        """Should not report missing combined PDF when it exists."""
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "test_combined.pdf").write_bytes(b"pdf content")

        stats = collect_output_statistics(tmp_path, "test")
        assert not any("test_combined.pdf" in m for m in stats["missing_expected_files"])

    def test_file_type_counts(self, tmp_path: Path):
        """Should count files by extension."""
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "a.pdf").write_bytes(b"x")
        (pdf_dir / "b.pdf").write_bytes(b"x")
        (pdf_dir / "c.log").write_text("log")

        stats = collect_output_statistics(tmp_path, "test")
        assert ".pdf" in stats["file_counts_by_type"]
        assert stats["file_counts_by_type"][".pdf"] == 2

    def test_project_dir_override(self, tmp_path: Path):
        """Should use project_dir when explicitly provided."""
        custom_dir = tmp_path / "custom_project"
        pdf_dir = custom_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"x" * 500)

        stats = collect_output_statistics(tmp_path, "ignored", project_dir=custom_dir)
        assert stats["pdf_files"] == 1

    def test_directory_info_structure(self, tmp_path: Path):
        """Each directory entry should have expected keys."""
        project_dir = tmp_path / "projects" / "test"
        (project_dir / "output" / "pdf").mkdir(parents=True)

        stats = collect_output_statistics(tmp_path, "test")
        pdf_info = stats["directories"]["pdf"]
        assert "exists" in pdf_info
        assert "file_count" in pdf_info
        assert "size_mb" in pdf_info

    def test_nonexistent_directory_info(self, tmp_path: Path):
        """Missing directories should be marked as not existing."""
        project_dir = tmp_path / "projects" / "test"
        (project_dir / "output").mkdir(parents=True)

        stats = collect_output_statistics(tmp_path, "test")
        for dir_name in ["web", "slides", "figures"]:
            assert stats["directories"][dir_name]["exists"] is False
            assert stats["directories"][dir_name]["file_count"] == 0


class TestGenerateDetailedOutputReport:
    """Tests for generate_detailed_output_report."""

    def test_basic_report(self, tmp_path: Path):
        """Should generate a formatted string report."""
        stats = {
            "total_files": 5,
            "total_size_mb": 10.5,
            "directories": {
                "pdf": {"exists": True, "file_count": 3, "size_mb": "8.00"},
                "web": {"exists": False, "file_count": 0, "size_mb": "0.00"},
            },
            "largest_files": [
                {"name": "big.pdf", "size_mb": "5.00", "category": "pdf"},
            ],
            "missing_expected_files": ["web/ directory"],
            "file_counts_by_type": {".pdf": 3, ".html": 2},
        }
        report = generate_detailed_output_report(tmp_path, stats)
        assert "OUTPUT STATISTICS REPORT" in report
        assert "Total Files: 5" in report
        assert "pdf: 3 files" in report
        assert "big.pdf" in report
        assert "web/ directory" in report

    def test_empty_stats(self, tmp_path: Path):
        """Should handle empty statistics gracefully."""
        stats = {
            "total_files": 0,
            "total_size_mb": 0.0,
            "directories": {},
            "largest_files": [],
            "missing_expected_files": [],
            "file_counts_by_type": {},
        }
        report = generate_detailed_output_report(tmp_path, stats)
        assert "Total Files: 0" in report

    def test_report_limits_largest_files(self, tmp_path: Path):
        """Should show at most 5 largest files."""
        stats = {
            "total_files": 10,
            "total_size_mb": 50.0,
            "directories": {},
            "largest_files": [
                {"name": f"file_{i}.pdf", "size_mb": f"{10 - i}.00", "category": "pdf"}
                for i in range(10)
            ],
            "missing_expected_files": [],
            "file_counts_by_type": {},
        }
        report = generate_detailed_output_report(tmp_path, stats)
        # Only first 5 should appear
        assert "file_0.pdf" in report
        assert "file_4.pdf" in report
        assert "file_5.pdf" not in report


class TestLogOutputSummary:
    """Tests for log_output_summary."""

    def test_basic_logging(self, tmp_path: Path, caplog):
        """Should log output summary without errors."""
        stats = {
            "pdf_files": 3,
            "web_files": 1,
            "slides_files": 0,
            "figures_files": 5,
            "data_files": 2,
            "reports_files": 1,
            "simulations_files": 0,
            "llm_files": 4,
            "logs_files": 2,
            "combined_pdf": 1,
            "total_files": 19,
            "errors": [],
        }
        with caplog.at_level("INFO"):
            log_output_summary(tmp_path, stats)
        assert "Output Copying Summary" in caplog.text

    def test_logging_with_errors(self, tmp_path: Path, caplog):
        """Should log errors/warnings."""
        stats = {
            "pdf_files": 1,
            "web_files": 0,
            "slides_files": 0,
            "figures_files": 0,
            "data_files": 0,
            "reports_files": 0,
            "simulations_files": 0,
            "llm_files": 0,
            "logs_files": 0,
            "combined_pdf": 0,
            "total_files": 1,
            "errors": ["Failed to copy figures/", "Permission denied on logs/"],
        }
        with caplog.at_level("WARNING"):
            log_output_summary(tmp_path, stats)

    def test_logging_with_structure_validation(self, tmp_path: Path, caplog):
        """Should include structure validation info."""
        stats = {
            "pdf_files": 1,
            "web_files": 0,
            "slides_files": 0,
            "figures_files": 0,
            "data_files": 0,
            "reports_files": 0,
            "simulations_files": 0,
            "llm_files": 0,
            "logs_files": 0,
            "combined_pdf": 0,
            "total_files": 1,
            "errors": [],
        }
        validation = {
            "directory_structure": {
                "pdf/": {"exists": True, "files": 3, "size_mb": "5.00"},
                "web/": {"exists": False},
                "data/": {"exists": True, "size_mb": "1.00"},
            }
        }
        with caplog.at_level("INFO"):
            log_output_summary(tmp_path, stats, structure_validation=validation)
