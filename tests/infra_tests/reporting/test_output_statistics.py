"""Tests for infrastructure.reporting.output_statistics module.

Tests output file statistics collection and report generation.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.reporting.output_statistics import (
    STAGE5_DELIVERY_INVENTORY_SCOPE,
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
        assert stats["directories"]["pdf"]["file_count"] == 0
        assert len(stats["missing_expected_files"]) > 0  # No subdirs exist
        assert stats["inventory_scope"] == "project-output"
        assert stats["inventory_root"] == "projects/test/output"

    def test_delivery_scope_is_explicit_and_release_safe(self, tmp_path: Path):
        """A source-located Stage 5 receipt identifies the copied tree it counts."""
        output_dir = tmp_path / "output" / "templates" / "test"
        artifact = output_dir / "data" / "result.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("{}\n", encoding="utf-8")

        stats = collect_output_statistics(
            tmp_path,
            "templates/test",
            require_pdf=False,
            output_dir=output_dir,
            inventory_scope=STAGE5_DELIVERY_INVENTORY_SCOPE,
        )

        assert stats["inventory_scope"] == "stage5-delivery-mirror"
        assert stats["inventory_root"] == "output/templates/test"
        assert stats["total_files"] == 1

    def test_with_pdf_files(self, tmp_path: Path):
        """Should count PDF files correctly."""
        project_dir = tmp_path / "projects" / "test"
        pdf_dir = project_dir / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF-1.4" + b"x" * 1000)
        (pdf_dir / "other.pdf").write_bytes(b"%PDF-1.4" + b"x" * 2000)

        stats = collect_output_statistics(tmp_path, "test")
        assert stats["directories"]["pdf"]["file_count"] == 2
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
        assert stats["directories"]["pdf"]["file_count"] == 1
        assert stats["directories"]["figures"]["file_count"] == 1
        assert stats["directories"]["data"]["file_count"] == 1

    def test_every_stable_inventory_file_is_counted(self, tmp_path: Path):
        """Dynamic publication categories and root bundles must not disappear."""
        project_dir = tmp_path / "projects" / "test"
        output_dir = project_dir / "output"
        files = {
            "manuscript/chapter.md": b"# Chapter\n",
            "docx/test_combined.docx": b"docx",
            "epub/test_combined.epub": b"epub",
            "release/checksums.txt": b"hash\n",
            "submission.tar.gz": b"archive",
        }
        for relative, payload in files.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        stats = collect_output_statistics(tmp_path, "test", require_pdf=False)

        assert stats["total_files"] == len(files)
        assert sum(info["file_count"] for info in stats["directories"].values()) == len(files)
        assert stats["directories"]["docx"]["file_count"] == 1
        assert stats["directories"]["epub"]["file_count"] == 1
        assert stats["directories"]["manuscript"]["file_count"] == 1
        assert stats["directories"]["release"]["file_count"] == 1
        assert stats["directories"]["root"]["file_count"] == 1

    def test_largest_files_use_exact_bytes_before_display_rounding(self, tmp_path: Path):
        """Sub-5-KiB files with equal displayed MB values retain true ordering."""
        project_dir = tmp_path / "projects" / "test"
        output_dir = project_dir / "output"
        for relative, size in (("pdf/tiny.pdf", 1), ("reports/larger.json", 7)):
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x" * size)

        stats = collect_output_statistics(tmp_path, "test", require_pdf=False)

        assert [item["path"] for item in stats["largest_files"][:2]] == [
            "reports/larger.json",
            "pdf/tiny.pdf",
        ]
        assert [item["size_bytes"] for item in stats["largest_files"][:2]] == [7, 1]

    def test_global_top_ten_considers_more_than_three_files_per_category(self, tmp_path: Path):
        """Per-category display limits must not truncate global candidates."""
        output_dir = tmp_path / "projects" / "test" / "output"
        data_dir = output_dir / "data"
        data_dir.mkdir(parents=True)
        for index, size in enumerate(range(100, 90, -1)):
            (data_dir / f"result-{index:02d}.bin").write_bytes(b"x" * size)
        for relative, size in (
            ("reports/summary.json", 10),
            ("figures/trace.png", 9),
            ("pdf/appendix.pdf", 8),
        ):
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x" * size)

        stats = collect_output_statistics(tmp_path, "test", require_pdf=False)

        assert [item["size_bytes"] for item in stats["largest_files"]] == list(range(100, 90, -1))
        assert len(stats["directories"]["data"]["largest_files"]) == 3

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
        assert float(stats["largest_files"][0]["size_mb"]) >= float(stats["largest_files"][-1]["size_mb"])

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

    def test_root_combined_pdf_satisfies_canonical_layout(self, tmp_path: Path):
        """The accepted copied-root layout must not invent a missing PDF dir."""
        output_dir = tmp_path / "projects" / "test" / "output"
        output_dir.mkdir(parents=True)
        (output_dir / "test_combined.pdf").write_bytes(b"pdf content")

        stats = collect_output_statistics(tmp_path, "test")

        assert stats["directories"]["root"]["file_count"] == 1
        assert "pdf/ directory" not in stats["missing_expected_files"]
        assert "test_combined.pdf" not in stats["missing_expected_files"]

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
        assert stats["directories"]["pdf"]["file_count"] == 1

    def test_directory_info_structure(self, tmp_path: Path):
        """Each directory entry should have expected keys."""
        project_dir = tmp_path / "projects" / "test"
        (project_dir / "output" / "pdf").mkdir(parents=True)

        stats = collect_output_statistics(tmp_path, "test")
        pdf_info = stats["directories"]["pdf"]
        assert "exists" in pdf_info
        assert "file_count" in pdf_info
        assert "size_mb" in pdf_info

    def test_release_safe_label_uses_last_output_segment(self, tmp_path: Path):
        """A checkout parent named output must not leak into report bytes."""
        nested_output = tmp_path / "output" / "worktree" / "repo" / "output" / "templates" / "demo"
        stats = {
            "directories": {},
            "total_files": 0,
            "total_size_mb": 0.0,
            "largest_files": [],
            "missing_expected_files": [],
            "file_counts_by_type": {},
        }

        report = generate_detailed_output_report(nested_output, stats)

        assert "Output Directory: output/templates/demo" in report
        assert "output/worktree" not in report

    def test_nonexistent_directory_info(self, tmp_path: Path):
        """Missing directories should be marked as not existing."""
        project_dir = tmp_path / "projects" / "test"
        (project_dir / "output").mkdir(parents=True)

        stats = collect_output_statistics(tmp_path, "test")
        for dir_name in ["web", "slides", "figures"]:
            assert stats["directories"][dir_name]["exists"] is False
            assert stats["directories"][dir_name]["file_count"] == 0

    def test_statistics_are_invariant_to_ignored_runtime_state(self, tmp_path: Path):
        """Publication statistics must be a fixed point over local build residue."""
        project_dir = tmp_path / "projects" / "test"
        output_dir = project_dir / "output"
        stable_files = {
            "pdf/test_combined.pdf": b"%PDF-1.7\n",
            "figures/trace.png": b"stable pixels",
            "data/results.json": b'{"result": 1}\n',
            "reports/quality.json": b'{"status": "pass"}\n',
        }
        for relative, payload in stable_files.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
        (tmp_path / ".gitignore").write_text(
            "projects/test/output/pdf/*.bbl\nprojects/test/output/data/*.scratch\n",
            encoding="utf-8",
        )
        baseline = collect_output_statistics(tmp_path, "test")

        ignored_files = {
            "pdf/test_combined.aux": b"latex auxiliary",
            "pdf/test_combined.bbl": b"gitignored bibliography",
            "data/local-cache.scratch": b"gitignored cache",
            "reports/.history/telemetry-123.json": b"{}\n",
            "reports/snapshots/stage.json": b"{}\n",
            "logs/pipeline.log": b"runtime log\n",
            "figures/.trace.png": b"atomic leftover",
        }
        for relative, payload in ignored_files.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        for relative in ("slides", "simulations", "llm"):
            (output_dir / relative).mkdir(parents=True, exist_ok=True)

        rerun = collect_output_statistics(tmp_path, "test")

        assert rerun == baseline
        assert rerun["inventory_mode"] == "stable-shippable-output-v1"
        assert rerun["directories"]["pdf"]["file_count"] == 1
        assert rerun["directories"]["logs"]["exists"] is False

        (output_dir / "data" / "new-public-result.json").write_text("{}\n", encoding="utf-8")
        changed = collect_output_statistics(tmp_path, "test")
        assert changed != baseline
        assert changed["directories"]["data"]["file_count"] == 2


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
        assert str(tmp_path) not in report
        assert "Total Files: 5" in report
        assert "pdf: 3 files" in report
        assert "big.pdf" in report
        assert "web/ directory" in report

    def test_project_output_dir_does_not_expose_lifecycle_checkout(self, tmp_path: Path):
        """Release-facing stats should not embed projects/working path prefixes."""
        output_dir = tmp_path / "projects" / "working" / "AGEINT" / "output"
        stats = {
            "total_files": 0,
            "total_size_mb": 0.0,
            "directories": {},
            "largest_files": [],
            "missing_expected_files": [],
            "file_counts_by_type": {},
        }

        report = generate_detailed_output_report(output_dir, stats)

        assert "Output Directory: output" in report
        assert "projects/working" not in report

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
                {"name": f"file_{i}.pdf", "size_mb": f"{10 - i}.00", "category": "pdf"} for i in range(10)
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
