"""Tests for progress tracking functionality."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from infrastructure.literature.workflow import (
    ProgressEntry,
    SummarizationProgress,
    ProgressTracker,
)


class TestProgressEntry:
    """Test ProgressEntry dataclass."""

    def test_creation(self):
        """Test ProgressEntry creation with default values."""
        entry = ProgressEntry(
            citation_key="smith2024paper",
            pdf_path="data/pdfs/smith2024paper.pdf"
        )

        assert entry.citation_key == "smith2024paper"
        assert entry.pdf_path == "data/pdfs/smith2024paper.pdf"
        assert entry.status == "pending"
        assert entry.download_attempts == 0
        assert entry.summary_attempts == 0
        assert entry.last_error is None
        assert entry.summary_path is None
        assert entry.download_time is None
        assert entry.summary_time is None

    def test_is_completed(self):
        """Test completion status checking."""
        entry = ProgressEntry("key", "path")

        assert not entry.is_completed
        assert not entry.is_successful

        entry.status = "summarized"
        assert entry.is_completed
        assert entry.is_successful

        entry.status = "failed"
        assert entry.is_completed
        assert not entry.is_successful

    def test_custom_values(self):
        """Test ProgressEntry with custom values."""
        entry = ProgressEntry(
            citation_key="test",
            pdf_path="path",
            status="downloaded",
            download_attempts=2,
            summary_attempts=1,
            last_error="Network timeout",
            summary_path="summary.md",
            download_time=1234567890.0,
            summary_time=120.5
        )

        assert entry.status == "downloaded"
        assert entry.download_attempts == 2
        assert entry.summary_attempts == 1
        assert entry.last_error == "Network timeout"
        assert entry.summary_path == "summary.md"
        assert entry.download_time == 1234567890.0
        assert entry.summary_time == 120.5


class TestSummarizationProgress:
    """Test SummarizationProgress dataclass."""

    def test_creation(self):
        """Test SummarizationProgress creation."""
        progress = SummarizationProgress(
            run_id="run_123",
            keywords=["machine learning", "neural networks"],
            total_papers=10,
            start_time=1234567890.0,
            last_update=1234567900.0
        )

        assert progress.run_id == "run_123"
        assert progress.keywords == ["machine learning", "neural networks"]
        assert progress.total_papers == 10
        assert progress.start_time == 1234567890.0
        assert progress.last_update == 1234567900.0
        assert progress.entries == {}

    def test_statistics_empty(self):
        """Test statistics with no entries."""
        progress = SummarizationProgress("run_123", ["test"], 5, 1000.0, 1000.0)

        assert progress.completed_summaries == 0
        assert progress.failed_summaries == 0
        assert progress.pending_summaries == 0
        assert progress.completion_percentage == 0.0
        assert progress.success_rate == 0.0

    def test_statistics_with_entries(self):
        """Test statistics with entries."""
        progress = SummarizationProgress("run_123", ["test"], 5, 1000.0, 1000.0)

        # Add some test entries
        progress.entries["paper1"] = ProgressEntry("paper1", "path1", status="summarized")
        progress.entries["paper2"] = ProgressEntry("paper2", "path2", status="summarized")
        progress.entries["paper3"] = ProgressEntry("paper3", "path3", status="failed")
        progress.entries["paper4"] = ProgressEntry("paper4", "path4", status="downloaded")
        progress.entries["paper5"] = ProgressEntry("paper5", "path5", status="pending")

        assert progress.completed_summaries == 3  # 2 summarized + 1 failed
        assert progress.successful_summaries == 2  # Only successfully summarized
        assert progress.failed_summaries == 1
        assert progress.pending_summaries == 1
        assert progress.completion_percentage == 60.0  # 3/5 completed
        assert progress.success_rate == (2/3) * 100  # 2 successful out of 3 completed

    def test_serialization(self):
        """Test JSON serialization/deserialization."""
        original = SummarizationProgress(
            run_id="test_run",
            keywords=["test", "keywords"],
            total_papers=3,
            start_time=1234567890.0,
            last_update=1234567900.0
        )

        # Add test entries
        original.entries["paper1"] = ProgressEntry("paper1", "path1", status="summarized")
        original.entries["paper2"] = ProgressEntry("paper2", "path2", status="failed", last_error="Error")

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = SummarizationProgress.from_dict(data)

        # Check equality
        assert restored.run_id == original.run_id
        assert restored.keywords == original.keywords
        assert restored.total_papers == original.total_papers
        assert restored.start_time == original.start_time
        assert restored.last_update == original.last_update
        assert len(restored.entries) == len(original.entries)

        # Check entries
        assert restored.entries["paper1"].status == "summarized"
        assert restored.entries["paper2"].status == "failed"
        assert restored.entries["paper2"].last_error == "Error"

    def test_summary_stats(self):
        """Test summary statistics generation."""
        progress = SummarizationProgress("run_123", ["test"], 5, 1000.0, 1100.0)
        progress.entries["paper1"] = ProgressEntry("paper1", "path1", status="summarized", summary_time=60.0)

        stats = progress.get_summary_stats()

        assert stats["run_id"] == "run_123"
        assert stats["keywords"] == ["test"]
        assert stats["total_papers"] == 5
        assert stats["completed"] == 1
        assert stats["successful"] == 1
        assert stats["failed"] == 0
        assert stats["completion_percentage"] == 20.0
        assert stats["total_time_seconds"] == 100.0  # 1100 - 1000
        assert stats["avg_time_per_paper"] == 20.0   # 100 / 5


class TestProgressTracker:
    """Test ProgressTracker functionality."""

    def test_initialization(self):
        """Test ProgressTracker initialization."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            assert tracker.progress_file == temp_file
            assert tracker.current_progress is None
        finally:
            temp_file.unlink(missing_ok=True)

    def test_start_new_run(self):
        """Test starting a new run."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)

            with patch('time.time', return_value=1234567890.0):
                progress = tracker.start_new_run(["test"], 5)

            assert progress.run_id.startswith("run_")
            assert progress.keywords == ["test"]
            assert progress.total_papers == 5
            assert progress.start_time == 1234567890.0
            assert progress.last_update == 1234567890.0
            assert tracker.current_progress is progress

            # Check file was created
            assert temp_file.exists()

        finally:
            temp_file.unlink(missing_ok=True)

    def test_load_existing_run(self):
        """Test loading existing progress."""
        # Create test data
        test_data = {
            "run_id": "test_run",
            "keywords": ["test"],
            "total_papers": 3,
            "start_time": 1234567890.0,
            "last_update": 1234567900.0,
            "entries": {
                "paper1": {
                    "citation_key": "paper1",
                    "pdf_path": "path1",
                    "status": "summarized"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            progress = tracker.load_existing_run()

            assert progress is not None
            assert progress.run_id == "test_run"
            assert progress.keywords == ["test"]
            assert progress.total_papers == 3
            assert tracker.current_progress is progress

        finally:
            temp_file.unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        """Test loading when file doesn't exist."""
        temp_file = Path("/nonexistent/file.json")
        tracker = ProgressTracker(temp_file)

        progress = tracker.load_existing_run()
        assert progress is None

    def test_update_entry_status(self):
        """Test updating entry status."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            tracker.start_new_run(["test"], 2)

            # Add a paper
            tracker.add_paper("paper1", "path1.pdf")

            # Update status
            tracker.update_entry_status("paper1", "downloaded", download_time=123.0)

            entry = tracker.current_progress.entries["paper1"]
            assert entry.status == "downloaded"
            assert entry.download_time == 123.0

        finally:
            temp_file.unlink(missing_ok=True)

    def test_update_nonexistent_entry(self):
        """Test updating status for non-existent entry."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            tracker.start_new_run(["test"], 1)

            # This should not raise an error
            tracker.update_entry_status("nonexistent", "failed")

            # Entry should not be created
            assert "nonexistent" not in tracker.current_progress.entries

        finally:
            temp_file.unlink(missing_ok=True)

    def test_add_paper(self):
        """Test adding a paper to track."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            tracker.start_new_run(["test"], 2)

            # Add paper
            tracker.add_paper("paper1", "path1.pdf")

            assert "paper1" in tracker.current_progress.entries
            entry = tracker.current_progress.entries["paper1"]
            assert entry.citation_key == "paper1"
            assert entry.pdf_path == "path1.pdf"
            assert entry.status == "pending"

        finally:
            temp_file.unlink(missing_ok=True)

    def test_get_incomplete_papers(self):
        """Test getting list of incomplete papers."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            tracker.start_new_run(["test"], 3)

            tracker.add_paper("paper1", "path1.pdf")
            tracker.add_paper("paper2", "path2.pdf")
            tracker.add_paper("paper3", "path3.pdf")

            tracker.update_entry_status("paper1", "summarized")
            tracker.update_entry_status("paper2", "failed")
            # paper3 remains pending

            incomplete = tracker.get_incomplete_papers()
            assert "paper3" in incomplete
            assert "paper1" not in incomplete
            assert "paper2" not in incomplete

        finally:
            temp_file.unlink(missing_ok=True)

    def test_get_failed_papers(self):
        """Test getting list of failed papers."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            tracker.start_new_run(["test"], 3)

            tracker.add_paper("paper1", "path1.pdf")
            tracker.add_paper("paper2", "path2.pdf")
            tracker.add_paper("paper3", "path3.pdf")

            tracker.update_entry_status("paper1", "summarized")
            tracker.update_entry_status("paper2", "failed")
            tracker.update_entry_status("paper3", "downloaded")

            failed = tracker.get_failed_papers()
            assert "paper2" in failed
            assert "paper1" not in failed
            assert "paper3" not in failed

        finally:
            temp_file.unlink(missing_ok=True)

    def test_archive_progress(self):
        """Test archiving progress file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            tracker = ProgressTracker(temp_file)
            tracker.start_new_run(["test"], 1)

            # Archive
            archived = tracker.archive_progress()

            assert archived is not None
            assert archived.name.startswith(temp_file.stem)
            assert archived.name.endswith(".json")
            assert archived.exists()
            assert not temp_file.exists()

        finally:
            temp_file.unlink(missing_ok=True)
            if 'archived' in locals():
                archived.unlink(missing_ok=True)
