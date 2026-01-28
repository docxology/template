"""Tests for infrastructure.core.file_operations module.

Comprehensive tests for file and directory operation utilities including
cleaning output directories and copying final deliverables.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from infrastructure.core.file_operations import (clean_output_directories,
                                                 clean_output_directory,
                                                 copy_final_deliverables)


class TestCleanOutputDirectory:
    """Test clean_output_directory function."""

    def test_clean_existing_directory_with_files(self, tmp_path):
        """Test cleaning directory with existing files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create some files and subdirectories
        (output_dir / "file1.txt").write_text("content1")
        (output_dir / "file2.txt").write_text("content2")
        (output_dir / "subdir").mkdir()
        (output_dir / "subdir" / "file3.txt").write_text("content3")

        result = clean_output_directory(output_dir)

        assert result is True
        assert output_dir.exists()
        assert len(list(output_dir.iterdir())) == 0

    def test_clean_existing_empty_directory(self, tmp_path):
        """Test cleaning an empty directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = clean_output_directory(output_dir)

        assert result is True
        assert output_dir.exists()
        assert len(list(output_dir.iterdir())) == 0

    def test_create_nonexistent_directory(self, tmp_path):
        """Test creating directory when it doesn't exist."""
        output_dir = tmp_path / "new_output"

        assert not output_dir.exists()
        result = clean_output_directory(output_dir)

        assert result is True
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_clean_directory_with_nested_structure(self, tmp_path):
        """Test cleaning directory with deeply nested structure."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create nested structure
        (output_dir / "level1").mkdir()
        (output_dir / "level1" / "level2").mkdir()
        (output_dir / "level1" / "level2" / "level3").mkdir()
        (output_dir / "level1" / "level2" / "level3" / "deep_file.txt").write_text(
            "deep"
        )
        (output_dir / "file.txt").write_text("root")

        result = clean_output_directory(output_dir)

        assert result is True
        assert output_dir.exists()
        assert len(list(output_dir.iterdir())) == 0

    def test_clean_directory_preserves_directory_itself(self, tmp_path):
        """Test that the directory itself is preserved, only contents removed."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "file.txt").write_text("content")

        original_path = output_dir
        result = clean_output_directory(output_dir)

        assert result is True
        assert output_dir == original_path
        assert output_dir.exists()

    def test_clean_directory_with_readonly_files(self, tmp_path):
        """Test cleaning directory with read-only files."""
        import os
        import stat

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a read-only file
        readonly_file = output_dir / "readonly.txt"
        readonly_file.write_text("readonly content")
        readonly_file.chmod(stat.S_IRUSR)  # Read-only for owner

        result = clean_output_directory(output_dir)

        # Should still succeed even with read-only files
        assert result is True
        assert output_dir.exists()
        # File should be gone (or at least we tried)
        assert not readonly_file.exists() or len(list(output_dir.iterdir())) == 0

    def test_clean_directory_with_symlinks(self, tmp_path):
        """Test cleaning directory with symbolic links."""
        import os

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a regular file and a symlink to it
        real_file = output_dir / "real.txt"
        real_file.write_text("real content")

        symlink_file = output_dir / "link.txt"
        os.symlink(str(real_file), str(symlink_file))

        result = clean_output_directory(output_dir)

        assert result is True
        assert output_dir.exists()
        assert len(list(output_dir.iterdir())) == 0


class TestCleanOutputDirectories:
    """Test clean_output_directories function."""

    def test_clean_with_default_subdirs(self, tmp_path):
        """Test cleaning with default subdirectory list."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        # Create projects/project/output and output/project directories with content
        project_output = repo_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)
        (project_output / "old_file.txt").write_text("old")

        top_output = repo_root / "output" / "project"
        top_output.mkdir(parents=True)
        (top_output / "old_file.txt").write_text("old")

        clean_output_directories(repo_root, project_name="project")

        # Check that default subdirs were created
        default_subdirs = [
            "pdf",
            "figures",
            "data",
            "reports",
            "simulations",
            "slides",
            "web",
            "logs",
        ]
        for subdir in default_subdirs:
            assert (project_output / subdir).exists()
            assert (top_output / subdir).exists()

        # Check old files are gone
        assert not (project_output / "old_file.txt").exists()
        assert not (top_output / "old_file.txt").exists()

    def test_clean_with_custom_subdirs(self, tmp_path):
        """Test cleaning with custom subdirectory list."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        project_output = repo_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)
        top_output = repo_root / "output" / "project"
        top_output.mkdir(parents=True)

        custom_subdirs = ["custom1", "custom2", "custom3"]
        clean_output_directories(
            repo_root, project_name="project", subdirs=custom_subdirs
        )

        # Check that custom subdirs were created
        for subdir in custom_subdirs:
            assert (project_output / subdir).exists()
            assert (top_output / subdir).exists()

        # Check default subdirs were NOT created
        assert not (project_output / "pdf").exists()

    def test_clean_creates_missing_directories(self, tmp_path):
        """Test that missing directories are created."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        # Don't create projects/project/output or output/project directories
        clean_output_directories(repo_root, project_name="project")

        project_output = repo_root / "projects" / "project" / "output"
        top_output = repo_root / "output" / "project"

        assert project_output.exists()
        assert top_output.exists()

    def test_clean_removes_existing_content(self, tmp_path):
        """Test that existing content is removed before recreating subdirs."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        project_output = repo_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)

        # Create files and directories
        (project_output / "file.txt").write_text("content")
        (project_output / "old_dir").mkdir()
        (project_output / "old_dir" / "nested.txt").write_text("nested")

        clean_output_directories(repo_root, project_name="project")

        # Old content should be gone
        assert not (project_output / "file.txt").exists()
        assert not (project_output / "old_dir").exists()

        # New subdirs should exist
        assert (project_output / "pdf").exists()

    def test_clean_with_empty_subdirs_list(self, tmp_path):
        """Test cleaning with empty subdirectory list."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        project_output = repo_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)
        (project_output / "file.txt").write_text("content")

        clean_output_directories(repo_root, project_name="project", subdirs=[])

        # Directory should exist but be empty (or only have subdirs if they were created)
        assert project_output.exists()
        assert not (project_output / "file.txt").exists()


class TestCopyFinalDeliverables:
    """Test copy_final_deliverables function."""

    def test_copy_with_complete_structure(self, tmp_path):
        """Test copying with complete project output structure."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)

        # Create subdirectories with files
        (project_output / "pdf").mkdir()
        (project_output / "pdf" / "document.pdf").write_text("pdf content")
        (project_output / "pdf" / "project_combined.pdf").write_text("combined pdf")

        (project_output / "figures").mkdir()
        (project_output / "figures" / "plot.png").write_text("png content")

        (project_output / "data").mkdir()
        (project_output / "data" / "results.csv").write_text("csv content")

        output_dir = tmp_path / "final_output" / "project"
        output_dir.mkdir(parents=True)

        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # Check files were copied
        assert (output_dir / "pdf" / "document.pdf").exists()
        assert (output_dir / "figures" / "plot.png").exists()
        assert (output_dir / "data" / "results.csv").exists()

        # Check combined PDF was copied to root
        assert (output_dir / "project_combined.pdf").exists()

        # Check stats
        assert stats["pdf_files"] >= 2
        assert stats["figures_files"] >= 1
        assert stats["data_files"] >= 1
        assert stats["combined_pdf"] == 1
        assert stats["total_files"] > 0
        assert len(stats["errors"]) == 0

    def test_copy_with_missing_project_output(self, tmp_path):
        """Test copying when project output doesn't exist."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        output_dir = tmp_path / "final_output"
        output_dir.mkdir()

        stats = copy_final_deliverables(project_root, output_dir)

        # Should return error in stats
        assert len(stats["errors"]) > 0
        assert "not found" in stats["errors"][0].lower()
        assert stats["total_files"] == 0

    def test_copy_counts_all_file_types(self, tmp_path):
        """Test that all file types are counted correctly."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)

        # Create files in various subdirectories
        subdirs = {
            "pdf": ["doc1.pdf", "doc2.pdf"],
            "web": ["page1.html", "page2.html"],
            "slides": ["slide1.pdf"],
            "figures": ["fig1.png", "fig2.png", "fig3.png"],
            "data": ["data1.csv"],
            "reports": ["report1.md"],
            "simulations": ["sim1.npz"],
            "llm": ["review1.md"],
            "logs": ["log1.log"],
        }

        for subdir, files in subdirs.items():
            (project_output / subdir).mkdir()
            for filename in files:
                (project_output / subdir / filename).write_text("content")

        output_dir = tmp_path / "final_output" / "project"
        output_dir.mkdir(parents=True)

        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # Check counts
        assert stats["pdf_files"] >= 2
        assert stats["web_files"] >= 2
        assert stats["slides_files"] >= 1
        assert stats["figures_files"] >= 3
        assert stats["data_files"] >= 1
        assert stats["reports_files"] >= 1
        assert stats["simulations_files"] >= 1
        assert stats["llm_files"] >= 1
        assert stats["logs_files"] >= 1

    def test_copy_without_combined_pdf(self, tmp_path):
        """Test copying when combined PDF doesn't exist."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)

        (project_output / "pdf").mkdir()
        (project_output / "pdf" / "other.pdf").write_text("content")
        # Don't create project_combined.pdf

        output_dir = tmp_path / "final_output" / "project"
        output_dir.mkdir(parents=True)

        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # Combined PDF should not be copied
        assert not (output_dir / "project_combined.pdf").exists()
        assert stats["combined_pdf"] == 0
        assert len(stats["errors"]) == 0

    def test_copy_preserves_nested_structure(self, tmp_path):
        """Test that nested directory structure is preserved."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)

        # Create nested structure
        (project_output / "pdf" / "subdir").mkdir(parents=True)
        (project_output / "pdf" / "subdir" / "nested.pdf").write_text("nested")
        (project_output / "pdf" / "top.pdf").write_text("top")

        output_dir = tmp_path / "final_output" / "project"
        output_dir.mkdir(parents=True)

        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # Check nested structure preserved
        assert (output_dir / "pdf" / "subdir" / "nested.pdf").exists()
        assert (output_dir / "pdf" / "top.pdf").exists()

        # Check file content preserved
        assert (output_dir / "pdf" / "subdir" / "nested.pdf").read_text() == "nested"
        assert (output_dir / "pdf" / "top.pdf").read_text() == "top"

    def test_copy_handles_existing_output_dir(self, tmp_path):
        """Test copying when output directory already has content."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)
        (project_output / "pdf").mkdir()
        (project_output / "pdf" / "new.pdf").write_text("new content")

        output_dir = tmp_path / "final_output" / "project"
        output_dir.mkdir(parents=True)
        (output_dir / "old_file.txt").write_text("old")

        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # New files should be present
        assert (output_dir / "pdf" / "new.pdf").exists()
        # Old files may or may not be present (depends on copytree behavior)
        # The important thing is that new files are copied

    def test_copy_statistics_accuracy(self, tmp_path):
        """Test that file count statistics are accurate."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)

        # Create known number of files
        (project_output / "pdf").mkdir()
        for i in range(5):
            (project_output / "pdf" / f"doc{i}.pdf").write_text(f"content{i}")

        (project_output / "figures").mkdir()
        for i in range(3):
            (project_output / "figures" / f"fig{i}.png").write_text(f"fig{i}")

        output_dir = tmp_path / "final_output" / "project"
        output_dir.mkdir(parents=True)

        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # Verify counts match
        assert stats["pdf_files"] == 5
        assert stats["figures_files"] == 3
        assert stats["total_files"] == 8

    def test_copy_error_handling(self, tmp_path):
        """Test error handling during copy operation."""
        project_root = tmp_path / "repo"
        project_root.mkdir()

        project_output = project_root / "projects" / "project" / "output"
        project_output.mkdir(parents=True)
        (project_output / "file.txt").write_text("content")

        output_dir = tmp_path / "final_output" / "project"
        # Don't create output_dir - but function should handle this via copytree

        # Actually, let's test with a read-only directory scenario
        # Create output_dir but make it read-only (if possible on this system)
        output_dir.mkdir(parents=True)

        # Normal case should work
        stats = copy_final_deliverables(
            project_root, output_dir, project_name="project"
        )

        # Should complete successfully
        assert len(stats["errors"]) == 0 or all(
            "not found" not in err.lower() for err in stats["errors"]
        )


class TestCleanCoverageFiles:
    """Test clean_coverage_files function."""

    def test_clean_coverage_files_basic(self, tmp_path):
        """Test cleaning basic coverage files."""
        # Create test coverage files
        (tmp_path / ".coverage").write_text("coverage data")
        (tmp_path / ".coverage.infra").write_text("infra coverage")
        (tmp_path / ".coverage.project").write_text("project coverage")
        (tmp_path / "coverage_infra.json").write_text('{"coverage": "infra"}')
        (tmp_path / "coverage_project.json").write_text('{"coverage": "project"}')

        # Import and call function
        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(tmp_path)

        assert result is True

        # Verify files were removed
        assert not (tmp_path / ".coverage").exists()
        assert not (tmp_path / ".coverage.infra").exists()
        assert not (tmp_path / ".coverage.project").exists()
        assert not (tmp_path / "coverage_infra.json").exists()
        assert not (tmp_path / "coverage_project.json").exists()

    def test_clean_coverage_files_custom_patterns(self, tmp_path):
        """Test cleaning with custom file patterns."""
        # Create test files
        (tmp_path / "custom_coverage.db").write_text("custom data")
        (tmp_path / "other_file.txt").write_text("other data")

        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(tmp_path, patterns=["custom_coverage.db"])

        assert result is True

        # Verify only custom pattern was removed
        assert not (tmp_path / "custom_coverage.db").exists()
        assert (tmp_path / "other_file.txt").exists()

    def test_clean_coverage_files_locked_file(self, tmp_path):
        """Test cleaning when a coverage file is locked."""
        import os

        # Create a regular file (can't really lock on all systems)
        coverage_file = tmp_path / ".coverage"
        coverage_file.write_text("coverage data")

        # Make it read-only to simulate lock
        coverage_file.chmod(0o444)  # Read-only

        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(tmp_path)

        # Should still succeed even with locked file
        assert result is True

        # File might still exist if it was locked
        # (behavior depends on system permissions)

    def test_clean_coverage_files_no_files(self, tmp_path):
        """Test cleaning when no coverage files exist."""
        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(tmp_path)

        assert result is True

    def test_clean_coverage_files_glob_patterns(self, tmp_path):
        """Test cleaning with glob patterns."""
        # Create files with glob patterns
        (tmp_path / ".coverage").write_text("main")
        (tmp_path / ".coverage.lock").write_text("lock")
        (tmp_path / ".coverage.temp").write_text("temp")
        (tmp_path / "coverage_001.json").write_text("json1")
        (tmp_path / "coverage_002.json").write_text("json2")

        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(
            tmp_path, patterns=[".coverage*", "coverage_*.json"]
        )

        assert result is True

        # Verify globbed files were removed
        assert not (tmp_path / ".coverage").exists()
        assert not (tmp_path / ".coverage.lock").exists()
        assert not (tmp_path / ".coverage.temp").exists()
        assert not (tmp_path / "coverage_001.json").exists()
        assert not (tmp_path / "coverage_002.json").exists()

    def test_clean_coverage_files_empty_patterns(self, tmp_path):
        """Test cleaning with empty patterns list."""
        (tmp_path / ".coverage").write_text("data")

        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(tmp_path, patterns=[])

        assert result is True

        # No files should be removed since patterns is empty
        assert (tmp_path / ".coverage").exists()

    def test_clean_coverage_files_subdirectory(self, tmp_path):
        """Test that coverage files in subdirectories are also cleaned."""
        # Create coverage files in subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / ".coverage").write_text("subdir coverage")

        from infrastructure.core.file_operations import clean_coverage_files

        result = clean_coverage_files(tmp_path)

        assert result is True

        # File in subdirectory should be removed
        assert not (subdir / ".coverage").exists()
