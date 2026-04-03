"""Tests for infrastructure.core.files.inventory — comprehensive coverage."""


from infrastructure.core.files.inventory import (
    FileInventoryManager,
    collect_output_files,
    generate_inventory_report,
    format_file_size,
)


class TestFormatFileSize:
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


class TestFileInventoryManager:
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
        (tmp_path / "project_combined.pdf").write_bytes(b"Combined PDF")
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


class TestConvenienceFunctions:
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
