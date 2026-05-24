"""Tests for file inventory and collection utilities."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path


from infrastructure.core.files.inventory import (
    FileInventoryEntry,
    FileInventoryManager,
    collect_output_files,
    format_file_size,
    generate_inventory_report,
)


class TestFileInventoryEntry:
    """Test FileInventoryEntry dataclass."""

    def test_entry_creation(self):
        """Test entry creation and properties."""
        path = Path("/tmp/test.pdf")
        entry = FileInventoryEntry(path=path, size=1024, category="pdf", modified=1234567890.0)

        assert entry.path == path
        assert entry.size == 1024
        assert entry.category == "pdf"
        assert entry.modified == 1234567890.0
        assert entry.size_formatted == "1KB"

    def test_size_formatting(self):
        """Test size formatting property."""
        test_cases = [
            (512, "512B"),
            (1024, "1KB"),
            (1536, "2KB"),  # Rounds up
            (1048576, "1MB"),
            (2147483648, "2GB"),
        ]

        for size, expected in test_cases:
            entry = FileInventoryEntry(
                path=Path("/tmp/test"), size=size, category="test", modified=0
            )
            assert entry.size_formatted == expected


class TestFormatFileSize:
    """Test format_file_size function."""

    def test_byte_sizes(self):
        """Test byte-level size formatting."""
        assert format_file_size(0) == "0B"
        assert format_file_size(512) == "512B"
        assert format_file_size(1023) == "1023B"

    def test_kilobyte_sizes(self):
        """Test kilobyte size formatting."""
        assert format_file_size(1024) == "1KB"
        assert format_file_size(1536) == "2KB"
        assert format_file_size(2047) == "2KB"

    def test_megabyte_sizes(self):
        """Test megabyte size formatting."""
        assert format_file_size(1048576) == "1MB"
        assert format_file_size(2097152) == "2MB"

    def test_gigabyte_sizes(self):
        """Test gigabyte size formatting."""
        assert format_file_size(1073741824) == "1GB"
        assert format_file_size(2147483648) == "2GB"


class TestFileInventoryManager:
    """Test FileInventoryManager class."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = FileInventoryManager()
        assert list(manager.OUTPUT_CATEGORIES) == [
            "pdf",
            "figures",
            "data",
            "reports",
            "simulations",
            "llm",
            "logs",
            "web",
            "slides",
            "tex",
        ]

    def test_collect_output_files_empty_directory(self):
        """Test collecting files from empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()

            manager = FileInventoryManager()
            entries = manager.collect_output_files(output_dir)

            assert entries == []

    def test_collect_output_files_with_files(self):
        """Test collecting files from directory with files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()

            # Create pdf directory and file
            pdf_dir = output_dir / "pdf"
            pdf_dir.mkdir()
            pdf_file = pdf_dir / "test.pdf"
            pdf_content = b"fake pdf content" * 256  # ~4KB
            pdf_file.write_bytes(pdf_content)

            # Create figures directory and file
            figures_dir = output_dir / "figures"
            figures_dir.mkdir()
            figures_file = figures_dir / "plot.png"
            figures_content = b"fake png content" * 512  # ~8KB
            figures_file.write_bytes(figures_content)

            manager = FileInventoryManager()
            entries = manager.collect_output_files(output_dir)

            # Check that files were found
            pdf_entries = [e for e in entries if e.category == "pdf"]
            figures_entries = [e for e in entries if e.category == "figures"]

            assert len(pdf_entries) == 1
            assert len(figures_entries) == 1
            assert pdf_entries[0].size == len(pdf_content)
            assert figures_entries[0].size == len(figures_content)
            assert pdf_entries[0].path == pdf_file
            assert figures_entries[0].path == figures_file

    def test_collect_output_files_root_level_files(self, tmp_path):
        """Test collecting root-level files like template_code_project_combined.pdf."""
        # Create a temporary output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a root-level PDF file
        pdf_file = output_dir / "template_code_project_combined.pdf"
        pdf_file.write_bytes(b"fake pdf content" * 100)  # ~1700 bytes

        manager = FileInventoryManager()
        entries = manager.collect_output_files(output_dir)

        # Should find the root-level PDF file
        pdf_entries = [e for e in entries if e.category == "pdf"]
        assert len(pdf_entries) == 1
        assert pdf_entries[0].size == len(b"fake pdf content" * 100)
        assert pdf_entries[0].path == pdf_file

    def test_generate_inventory_report_empty(self):
        """Test generating report for empty inventory."""
        manager = FileInventoryManager()
        report = manager.generate_inventory_report([])

        assert "No files found" in report

    def test_generate_inventory_report_text(self):
        """Test generating text format inventory report."""
        entries = [
            FileInventoryEntry(Path("/tmp/pdf/doc.pdf"), 1024, "pdf", 1234567890),
            FileInventoryEntry(Path("/tmp/figures/plot.png"), 2048, "figures", 1234567891),
            FileInventoryEntry(Path("/tmp/data/results.csv"), 512, "data", 1234567892),
        ]

        manager = FileInventoryManager()
        report = manager.generate_inventory_report(entries, "text")

        assert "Generated Files Inventory" in report
        assert "PDF (1 file(s), 1KB)" in report
        assert "Figures (1 file(s), 2KB)" in report
        assert "Data (1 file(s), 512B)" in report

    def test_generate_inventory_report_json(self):
        """Test generating JSON format inventory report."""
        entries = [
            FileInventoryEntry(Path("/tmp/pdf/doc.pdf"), 1024, "pdf", 1234567890),
        ]

        manager = FileInventoryManager()
        report = manager.generate_inventory_report(entries, "json")

        # Should be valid JSON
        data = json.loads(report)
        assert "pdf" in data
        assert data["pdf"]["count"] == 1
        assert data["pdf"]["total_size"] == 1024
        assert len(data["pdf"]["files"]) == 1

    def test_generate_inventory_report_html(self):
        """Test generating HTML format inventory report."""
        entries = [
            FileInventoryEntry(Path("/tmp/pdf/doc.pdf"), 1024, "pdf", 1234567890),
        ]

        manager = FileInventoryManager()
        report = manager.generate_inventory_report(entries, "html")

        assert "<div class='file-inventory'>" in report
        assert "<h3>Generated Files Inventory</h3>" in report
        assert "PDF (1 file(s), 1KB)" in report
        assert "</div>" in report

    def test_guess_category_from_filename(self):
        """Test category guessing from filename."""
        manager = FileInventoryManager()

        test_cases = [
            ("document.pdf", "pdf"),
            ("plot.png", "figures"),
            ("data.csv", "data"),
            ("app.log", "logs"),
            ("unknown.xyz", "misc"),
        ]

        for filename, expected_category in test_cases:
            category = manager._guess_category_from_filename(filename)
            assert category == expected_category

    def test_group_by_category(self):
        """Test grouping entries by category."""
        entries = [
            FileInventoryEntry(Path("/tmp/pdf/doc1.pdf"), 1024, "pdf", 1234567890),
            FileInventoryEntry(Path("/tmp/pdf/doc2.pdf"), 2048, "pdf", 1234567891),
            FileInventoryEntry(Path("/tmp/figures/plot.png"), 512, "figures", 1234567892),
        ]

        manager = FileInventoryManager()
        groups = manager._group_by_category(entries)

        assert len(groups) == 2
        assert len(groups["pdf"]) == 2
        assert len(groups["figures"]) == 1
        assert groups["pdf"][0].size == 1024
        assert groups["pdf"][1].size == 2048


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_collect_output_files_function(self):
        """Test collect_output_files convenience function."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result = collect_output_files(output_dir, ["pdf"])
            # Should return empty list for non-existent directory
            assert result == []

    def test_generate_inventory_report_function(self):
        """Test generate_inventory_report convenience function."""
        result = generate_inventory_report([], "text", Path("/tmp"))
        assert result == "No files found in output directory"


class TestFormatFileSizeFromFileInventory:
    def test_bytes(self):
        assert "B" in format_file_size(500)

    def test_kilobytes(self):
        result = format_file_size(2048)
        assert "KB" in result or "kB" in result or "K" in result

    def test_megabytes(self):
        result = format_file_size(5 * 1024 * 1024)
        assert "MB" in result or "M" in result

    def test_zero(self):
        result = format_file_size(0)
        assert "0" in result


class TestFileInventoryManagerFromFileInventory:
    def test_collect_empty_dir(self, tmp_path):
        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        assert entries == []

    def test_collect_nonexistent_dir(self, tmp_path):
        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path / "nonexistent")
        assert entries == []

    def test_collect_pdf_files(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF content")
        (pdf_dir / "section.pdf").write_bytes(b"%PDF more")

        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        pdf_entries = [e for e in entries if e.category == "pdf"]
        assert len(pdf_entries) == 2

    def test_collect_figures(self, tmp_path):
        fig_dir = tmp_path / "figures"
        fig_dir.mkdir()
        (fig_dir / "plot.png").write_bytes(b"PNG data")

        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        assert len(entries) >= 1

    def test_collect_specific_categories(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "doc.pdf").write_bytes(b"PDF")
        fig_dir = tmp_path / "figures"
        fig_dir.mkdir()
        (fig_dir / "fig.png").write_bytes(b"PNG")

        manager = FileInventoryManager()
        # Only collect pdf category
        entries = manager.collect_output_files(tmp_path, categories=["pdf"])
        assert all(e.category == "pdf" for e in entries)

    def test_collect_combined_pdfs_at_root(self, tmp_path):
        (tmp_path / "template_code_project_combined.pdf").write_bytes(b"Combined PDF")
        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        assert any("combined" in e.path.name for e in entries)

    def test_guess_category(self):
        manager = FileInventoryManager()
        assert manager._guess_category_from_filename("doc.pdf") == "pdf"
        assert manager._guess_category_from_filename("plot.png") == "figures"
        assert manager._guess_category_from_filename("data.csv") == "data"
        assert manager._guess_category_from_filename("results.json") == "data"
        assert manager._guess_category_from_filename("build.log") == "logs"
        assert manager._guess_category_from_filename("readme.txt") == "misc"

    def test_generate_text_report(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "doc.pdf").write_bytes(b"A" * 1024)

        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        report = manager.generate_inventory_report(entries, "text")
        assert "doc.pdf" in report

    def test_generate_json_report(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "doc.pdf").write_bytes(b"A" * 1024)

        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        report = manager.generate_inventory_report(entries, "json")
        assert "doc.pdf" in report

    def test_generate_html_report(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "doc.pdf").write_bytes(b"A" * 1024)

        manager = FileInventoryManager()
        entries = manager.collect_output_files(tmp_path)
        report = manager.generate_inventory_report(entries, "html")
        assert "<" in report  # HTML tags

    def test_generate_report_empty(self):
        manager = FileInventoryManager()
        report = manager.generate_inventory_report([])
        assert "No files" in report


class TestConvenienceFunctionsFromFileInventory:
    def test_collect_output_files(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "doc.pdf").write_bytes(b"PDF")
        entries = collect_output_files(tmp_path)
        assert len(entries) >= 1

    def test_generate_inventory_report(self, tmp_path):
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "doc.pdf").write_bytes(b"PDF")
        entries = collect_output_files(tmp_path)
        report = generate_inventory_report(entries, "text")
        assert isinstance(report, str)
