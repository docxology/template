"""Tests for infrastructure.validation.output.validator module.

Comprehensive tests for output validation functionality including
copied outputs validation and output structure validation.
"""

import subprocess

import pytest

from infrastructure.validation.output.validator import validate_output_structure


class TestCollectDetailedValidationResults:
    """Test collect_detailed_validation_results function."""

    def test_collect_complete_results(self, tmp_path):
        """Test collecting results with complete structure."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 50000)

        # Create other directories with files
        for subdir in ["figures", "data", "reports", "web", "slides"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / f"{subdir}_file.txt").write_text("content")

        result = collect_detailed_validation_results(project_output_dir)

        assert "structure" in result
        assert "directories" in result
        assert "file_counts" in result
        assert "total_size_mb" in result
        assert "issues_by_severity" in result
        assert "recommendations" in result

        # Check directory details populated
        assert result["directories"]["pdf"]["exists"] is True
        assert result["directories"]["figures"]["exists"] is True
        assert result["file_counts"]["pdf"] >= 1

    def test_collect_missing_directories(self, tmp_path):
        """Test collecting results with missing directories."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create only PDF
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 50000)

        result = collect_detailed_validation_results(project_output_dir)

        # Missing directories should be flagged as warnings
        assert len(result["issues_by_severity"]["warning"]) > 0
        assert result["directories"]["figures"]["exists"] is False
        assert result["directories"]["data"]["exists"] is False

    def test_collect_missing_pdf_critical(self, tmp_path):
        """Test that missing PDF is flagged as critical."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create other directories but no PDF
        (project_output_dir / "pdf").mkdir()
        (project_output_dir / "figures").mkdir()

        result = collect_detailed_validation_results(project_output_dir)

        # Missing PDF should be critical issue
        assert len(result["issues_by_severity"]["critical"]) > 0

    def test_collect_generates_recommendations(self, tmp_path):
        """Test that recommendations are generated based on issues."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Minimal structure - no PDF, no figures
        (project_output_dir / "pdf").mkdir()

        result = collect_detailed_validation_results(project_output_dir)

        # Should have recommendations
        assert len(result["recommendations"]) > 0
        # Check for figures recommendation
        priorities = [r["priority"] for r in result["recommendations"]]
        assert "high" in priorities or "medium" in priorities

    def test_collect_calculates_total_size(self, tmp_path):
        """Test that total size is calculated correctly."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"X" * 1024 * 1024)  # 1 MB

        # Create figures
        figures_dir = project_output_dir / "figures"
        figures_dir.mkdir()
        (figures_dir / "figure1.png").write_bytes(b"Y" * 512 * 1024)  # 0.5 MB

        result = collect_detailed_validation_results(project_output_dir)

        # Total should be around 1.5 MB
        assert result["total_size_mb"] > 1.0

    def test_collect_finds_largest_file(self, tmp_path):
        """Test that largest file is identified per directory."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF directory with multiple files
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "small.pdf").write_bytes(b"X" * 100)
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"Y" * 50000)
        (pdf_dir / "medium.pdf").write_bytes(b"Z" * 1000)

        result = collect_detailed_validation_results(project_output_dir)

        # Largest file should be identified
        assert result["directories"]["pdf"]["largest_file"] == "test_project_combined.pdf"

    def test_collect_handles_empty_output(self, tmp_path):
        """Test handling of completely empty output directory."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        result = collect_detailed_validation_results(project_output_dir)

        # Should have issues
        assert result["structure"]["valid"] is False
        assert result["total_size_mb"] == 0.0

    def test_collect_suspicious_sizes_from_structure(self, tmp_path):
        """Test that suspicious sizes from structure validation are propagated."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF with small size (suspicious)
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 10)  # Very small

        result = collect_detailed_validation_results(project_output_dir)

        # Suspicious size should be in warnings
        assert len(result["issues_by_severity"]["warning"]) > 0

    def test_detailed_statistics_ignore_runtime_state_and_empty_directories(self, tmp_path):
        """Ignored residue must not perturb provenance-bound structure data."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        project_dir = tmp_path / "project"
        output_dir = project_dir / "output"
        stable_files = {
            "pdf/project_combined.pdf": b"P" * 120_000,
            "web/index.html": b"<html></html>\n",
            "figures/nested/trace.png": b"pixels",
            "data/result.json": b"{}\n",
            "reports/quality.json": b"{}\n",
        }
        for relative, payload in stable_files.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
        (tmp_path / ".gitignore").write_text(
            "project/output/pdf/*.bbl\nproject/output/data/*.scratch\n",
            encoding="utf-8",
        )
        baseline = collect_detailed_validation_results(output_dir)

        ignored_files = {
            "pdf/project_combined.aux": b"aux",
            "pdf/project_combined.bbl": b"bibliography",
            "data/cache.scratch": b"cache",
            "reports/.history/telemetry.json": b"{}\n",
            "reports/snapshots/stage.json": b"{}\n",
            "logs/pipeline.log": b"log\n",
            "figures/.trace.png": b"partial",
        }
        for relative, payload in ignored_files.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        for relative in ("slides", "simulations", "llm"):
            (output_dir / relative).mkdir(parents=True, exist_ok=True)

        rerun = collect_detailed_validation_results(output_dir)

        assert rerun == baseline
        assert rerun["inventory_mode"] == "stable-shippable-output-v1"
        assert rerun["directories"]["pdf"]["file_count"] == 1
        assert rerun["directories"]["figures"]["file_count"] == 1
        assert rerun["directories"]["logs"]["exists"] is False

        (output_dir / "data" / "new-public-result.json").write_text("{}\n", encoding="utf-8")
        changed = collect_detailed_validation_results(output_dir)
        assert changed != baseline
        assert changed["directories"]["data"]["file_count"] == 2

    def test_detailed_statistics_fail_closed_on_output_symlinks(self, tmp_path):
        """Statistics must never follow a link outside the publication tree."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_dir = tmp_path / "project" / "output"
        data_dir = output_dir / "data"
        data_dir.mkdir(parents=True)
        outside = tmp_path / "private-result.json"
        outside.write_text('{"private": true}\n', encoding="utf-8")
        (data_dir / "linked-result.json").symlink_to(outside)

        with pytest.raises(ValueError, match="symlink artifact forbidden"):
            collect_detailed_validation_results(output_dir, require_pdf=False)

    def test_supplied_copy_inventory_cannot_use_source_pdf_fallback(self, tmp_path):
        """Stage 5 structure evidence must describe the copied tree alone."""
        from infrastructure.core.pipeline.artifacts import StableOutputInventory

        copied = tmp_path / "output" / "demo"
        copied.mkdir(parents=True)
        source_pdf = tmp_path / "projects" / "demo" / "output" / "pdf" / "demo_combined.pdf"
        source_pdf.parent.mkdir(parents=True)
        source_pdf.write_bytes(b"P" * 120_000)

        result = validate_output_structure(
            copied,
            require_pdf=True,
            inventory=StableOutputInventory(files=()),
            enabled_formats={"pdf"},
        )

        assert result["valid"] is False
        assert result["directory_structure"]["combined_pdf"]["exists"] is False
        assert result["directory_structure"]["pdf"]["exists"] is False

    def test_implicit_inventory_rejects_git_ignored_combined_pdf(self, tmp_path):
        """Direct structure validation cannot bless a non-shippable PDF."""
        output_dir = tmp_path / "projects" / "demo" / "output"
        pdf = output_dir / "pdf" / "demo_combined.pdf"
        pdf.parent.mkdir(parents=True)
        pdf.write_bytes(b"P" * 120_000)
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
        (tmp_path / ".gitignore").write_text(
            "projects/demo/output/pdf/*.pdf\n",
            encoding="utf-8",
        )

        result = validate_output_structure(output_dir, require_pdf=True)

        assert result["valid"] is False
        assert result["directory_structure"]["combined_pdf"]["exists"] is False
        assert result["directory_structure"]["pdf"]["exists"] is False

    def test_detailed_statistics_account_for_dynamic_publication_categories(self, tmp_path):
        """DOCX, EPUB, manuscript, package, and root files remain visible."""
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_dir = tmp_path / "project" / "output"
        files = {
            "docx/project_combined.docx": b"docx",
            "epub/project_combined.epub": b"epub",
            "manuscript/chapter.md": b"# Chapter\n",
            "release/package.json": b"{}\n",
            "submission.tar.gz": b"archive",
        }
        for relative, payload in files.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        result = collect_detailed_validation_results(output_dir, require_pdf=False)

        assert sum(result["file_counts"].values()) == len(files)
        assert result["file_counts"]["docx"] == 1
        assert result["file_counts"]["epub"] == 1
        assert result["file_counts"]["manuscript"] == 1
        assert result["file_counts"]["release"] == 1
        assert result["file_counts"]["root"] == 1
        assert result["directories"]["root"]["largest_file"] == "submission.tar.gz"
        assert result["directories"]["root"]["largest_file_path"] == "submission.tar.gz"

    def test_empty_data_dir_is_info_not_warning(self, tmp_path):
        """Empty ``data/`` (no producers) → ``info``, not ``warning``.

        Pure-proof projects (e.g. ``fep_lean``) never write to ``data/``;
        emitting a warning every render is noise. Truly anomalous sizes
        ("unusually small" combined PDF) remain warnings — see preceding test.
        """
        from infrastructure.validation.output.validator import collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF content" * 20000)
        (project_output_dir / "data").mkdir()  # exists but empty

        result = collect_detailed_validation_results(project_output_dir)

        info_msgs = result["issues_by_severity"]["info"]
        warning_msgs = result["issues_by_severity"]["warning"]
        assert any("data/ directory is empty" in msg for msg in info_msgs)
        assert not any("data/ directory is empty" in msg for msg in warning_msgs)
