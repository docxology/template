"""Tests for infrastructure.core.files.cleanup_helpers."""

import logging
from pathlib import Path

from infrastructure.core.files.cleanup_helpers import (
    archive_output_logs,
    clean_dir_preserving,
    clean_output_dir_contents,
)


class TestCleanDirPreserving:
    def test_removes_all_when_no_preserved(self, tmp_path):
        output_dir = tmp_path
        subdir = tmp_path / "data"
        subdir.mkdir()
        (subdir / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")

        log = logging.getLogger("test_clean")
        clean_dir_preserving(subdir, output_dir, set(), log)

        # Files should be removed
        assert not (subdir / "file1.txt").exists()
        assert not (subdir / "file2.txt").exists()

    def test_preserves_specified_files(self, tmp_path):
        output_dir = tmp_path
        subdir = tmp_path / "data"
        subdir.mkdir()
        (subdir / "keep.txt").write_text("keep me")
        (subdir / "remove.txt").write_text("remove me")

        preserved = {Path("data/keep.txt")}
        log = logging.getLogger("test_clean")
        clean_dir_preserving(subdir, output_dir, preserved, log)

        assert (subdir / "keep.txt").exists()
        assert not (subdir / "remove.txt").exists()

    def test_cleans_empty_subdirectories(self, tmp_path):
        output_dir = tmp_path
        subdir = tmp_path / "data"
        nested = subdir / "nested"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("content")

        log = logging.getLogger("test_clean")
        clean_dir_preserving(subdir, output_dir, set(), log)

        # Nested dir should be removed since it's now empty
        assert not nested.exists()


class TestArchiveOutputLogs:
    def test_no_logs_dir(self, tmp_path):
        # Should be a no-op
        archive_output_logs(tmp_path)

    def test_empty_logs_dir(self, tmp_path):
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        archive_output_logs(tmp_path)
        # Archive dir should be created but no files archived
        assert (logs_dir / "archive").is_dir()

    def test_archives_log_files(self, tmp_path):
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / "pipeline.log").write_text("log content")
        (logs_dir / "stage1.log").write_text("stage 1 log")

        archive_output_logs(tmp_path)

        archive_dir = logs_dir / "archive"
        assert archive_dir.is_dir()
        archived = list(archive_dir.glob("*.log"))
        assert len(archived) == 2

    def test_log_files_still_exist_after_archive(self, tmp_path):
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / "test.log").write_text("data")

        archive_output_logs(tmp_path)

        # Original log should still exist (copy2, not move)
        assert (logs_dir / "test.log").exists()


class TestCleanOutputDirContents:
    def test_removes_files_and_dirs(self, tmp_path):
        (tmp_path / "file.txt").write_text("content")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        clean_output_dir_contents(tmp_path, set())

        assert not (tmp_path / "file.txt").exists()
        assert not subdir.exists()

    def test_preserves_checkpoints(self, tmp_path):
        checkpoint_dir = tmp_path / ".checkpoints"
        checkpoint_dir.mkdir()
        (checkpoint_dir / "state.json").write_text("{}")
        (tmp_path / "data.txt").write_text("data")

        clean_output_dir_contents(tmp_path, set())

        assert checkpoint_dir.exists()
        assert (checkpoint_dir / "state.json").exists()
        assert not (tmp_path / "data.txt").exists()

    def test_preserves_specified_files(self, tmp_path):
        (tmp_path / "keep.txt").write_text("keep me")
        (tmp_path / "remove.txt").write_text("remove me")

        preserved = {Path("keep.txt")}
        clean_output_dir_contents(tmp_path, preserved)

        assert (tmp_path / "keep.txt").exists()
        assert not (tmp_path / "remove.txt").exists()

    def test_selectively_cleans_dir_with_preserved_files(self, tmp_path):
        subdir = tmp_path / "data"
        subdir.mkdir()
        (subdir / "keep.csv").write_text("data")
        (subdir / "remove.csv").write_text("old data")

        preserved = {Path("data/keep.csv")}
        clean_output_dir_contents(tmp_path, preserved)

        assert (subdir / "keep.csv").exists()
        assert not (subdir / "remove.csv").exists()
