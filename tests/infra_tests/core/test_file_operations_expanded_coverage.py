"""Tests for infrastructure.core.files.operations — expanded coverage."""

import pytest

from infrastructure.core.files.operations import (
    copy_final_deliverables,
    calculate_file_hash,
)
from infrastructure.core.exceptions import FileOperationError


class TestCopyFinalDeliverables:
    def test_project_output_not_found(self, tmp_path):
        """No project output directory."""
        stats = copy_final_deliverables(tmp_path, tmp_path / "output", "nonexistent")
        assert len(stats["errors"]) > 0
        assert "not found" in stats["errors"][0]

    def test_basic_copy(self, tmp_path):
        """Copy a basic project output structure."""
        proj = tmp_path / "projects" / "myproj" / "output"
        (proj / "pdf").mkdir(parents=True)
        (proj / "pdf" / "paper.pdf").write_bytes(b"%PDF-1.4 test content")
        (proj / "figures").mkdir()
        (proj / "figures" / "fig1.png").write_bytes(b"PNG data")

        output_dir = tmp_path / "output" / "myproj"
        output_dir.mkdir(parents=True)
        stats = copy_final_deliverables(tmp_path, output_dir, "myproj")
        assert stats["total_files"] >= 2
        assert stats["pdf_files"] >= 1

    def test_with_logs_directory(self, tmp_path):
        """Test log file detection."""
        proj = tmp_path / "projects" / "proj" / "output"
        (proj / "logs").mkdir(parents=True)
        (proj / "logs" / "pipeline.log").write_text("Log line 1\nLog line 2")

        output_dir = tmp_path / "output" / "proj"
        output_dir.mkdir(parents=True)
        stats = copy_final_deliverables(tmp_path, output_dir, "proj")
        assert stats["logs_files"] >= 1

    def test_with_empty_log_file(self, tmp_path):
        """Test empty log file warning."""
        proj = tmp_path / "projects" / "proj" / "output"
        (proj / "logs").mkdir(parents=True)
        (proj / "logs" / "pipeline.log").write_text("")  # empty

        output_dir = tmp_path / "output" / "proj"
        output_dir.mkdir(parents=True)
        stats = copy_final_deliverables(tmp_path, output_dir, "proj")
        assert stats["logs_files"] >= 1

    def test_combined_pdf_copied(self, tmp_path):
        """Test combined PDF copying to root."""
        proj = tmp_path / "projects" / "proj" / "output"
        (proj / "pdf").mkdir(parents=True)
        (proj / "pdf" / "proj_combined.pdf").write_bytes(b"%PDF-1.4 combined")

        output_dir = tmp_path / "output" / "proj"
        output_dir.mkdir(parents=True)
        stats = copy_final_deliverables(tmp_path, output_dir, "proj")
        assert stats["combined_pdf"] == 1

    def test_no_logs_directory(self, tmp_path):
        """Test with no logs subdirectory."""
        proj = tmp_path / "projects" / "proj" / "output"
        (proj / "pdf").mkdir(parents=True)
        (proj / "pdf" / "paper.pdf").write_bytes(b"content")

        output_dir = tmp_path / "output" / "proj"
        output_dir.mkdir(parents=True)
        stats = copy_final_deliverables(tmp_path, output_dir, "proj")
        assert stats["logs_files"] == 0


class TestCalculateFileHash:
    def test_sha256(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("hello world")
        result = calculate_file_hash(file, "sha256")
        assert result is not None
        assert len(result) == 64  # SHA256 hex length

    def test_md5(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("hello world")
        result = calculate_file_hash(file, "md5")
        assert result is not None
        assert len(result) == 32  # MD5 hex length

    def test_file_not_found(self, tmp_path):
        result = calculate_file_hash(tmp_path / "nonexistent.txt")
        assert result is None

    def test_unsupported_algorithm(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("data")
        with pytest.raises(FileOperationError, match="Unsupported"):
            calculate_file_hash(file, "fake_algo")

    def test_empty_file(self, tmp_path):
        file = tmp_path / "empty.txt"
        file.write_text("")
        result = calculate_file_hash(file, "sha256")
        assert result is not None

    def test_binary_file(self, tmp_path):
        file = tmp_path / "binary.bin"
        file.write_bytes(bytes(range(256)))
        result = calculate_file_hash(file, "sha256")
        assert result is not None
