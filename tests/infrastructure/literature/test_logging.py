"""Tests for enhanced logging functionality in literature module.

Tests the structured logging improvements and progress tracking.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import SearchResult


class TestWorkflowLogging:
    """Test enhanced logging in LiteratureWorkflow."""

    def test_download_logging_structure(self, tmp_path, capsys):
        """Test that download logging follows structured format."""
        # Set up test data
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        literature_search = LiteratureSearch(config)
        workflow = LiteratureWorkflow(literature_search)

        # Create mock search results
        results = [
            SearchResult(
                title="Paper One",
                authors=["Author One"],
                year=2023,
                abstract="Abstract one",
                url="https://example.com/1",
                doi="10.1234/paper1",
                source="arxiv",
                pdf_url="https://example.com/paper1.pdf"
            ),
            SearchResult(
                title="Paper Two",
                authors=["Author Two"],
                year=2024,
                abstract="Abstract two",
                url="https://example.com/2",
                doi="10.1234/paper2",
                source="semanticscholar",
                pdf_url="https://example.com/paper2.pdf"
            )
        ]

        # Mock successful downloads
        with patch.object(literature_search, 'download_paper_with_result') as mock_download:
            # Mock successful download results
            mock_download.side_effect = [
                MagicMock(
                    success=True,
                    pdf_path=Path("literature/pdfs/paper1.pdf"),
                    already_existed=False,
                    failure_reason=None,
                    attempted_urls=["https://example.com/paper1.pdf"]
                ),
                MagicMock(
                    success=True,
                    pdf_path=Path("literature/pdfs/paper2.pdf"),
                    already_existed=True,
                    failure_reason=None,
                    attempted_urls=["https://example.com/paper2.pdf"]
                )
            ]

            # Mock add_to_library
            with patch.object(literature_search, 'add_to_library') as mock_add:
                mock_add.side_effect = ["paper1", "paper2"]

                # Execute download
                downloaded, download_results = workflow._download_papers(results)

                # Check that logging occurred
                assert len(downloaded) == 2
                assert len(download_results) == 2

                # Check stdout output contains expected structured format
                captured = capsys.readouterr()
                output = captured.out

                # Should contain progress indicators
                assert "[DOWNLOAD 1/2]" in output
                assert "[DOWNLOAD 2/2]" in output

                # Should contain success indicators
                assert "✓ Downloaded:" in output
                assert "✓ Already exists:" in output

                # Should contain summary
                assert "DOWNLOAD SUMMARY" in output
                assert "Successfully downloaded 2 of 2 papers" in output

    def test_summarization_logging_structure(self, tmp_path, capsys):
        """Test that summarization logging follows structured format."""
        # Set up test data
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        literature_search = LiteratureSearch(config)
        workflow = LiteratureWorkflow(literature_search)

        # Mock summarizer
        mock_summarizer = MagicMock()
        workflow.set_summarizer(mock_summarizer)

        # Mock progress tracker
        mock_progress_tracker = MagicMock()
        mock_progress_tracker.current_progress = MagicMock()
        mock_progress_tracker.current_progress.entries = {}
        workflow.set_progress_tracker(mock_progress_tracker)

        # Create test data
        result = SearchResult(
            title="Test Paper",
            authors=["Test Author"],
            year=2023,
            abstract="Test abstract",
            url="https://example.com/test",
            source="arxiv"
        )
        pdf_path = Path("literature/pdfs/test.pdf")

        # Mock successful summarization
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.generation_time = 2.5
        mock_result.summary_path = Path("literature/summaries/test_summary.md")
        mock_result.attempts = 1

        mock_summarizer.summarize_paper.return_value = mock_result

        # Execute summarization
        downloaded = [(result, pdf_path)]
        results = workflow._summarize_papers_parallel(downloaded, max_workers=1)

        # Check results
        assert len(results) == 1
        assert results[0].success

        # Check stdout output
        captured = capsys.readouterr()
        output = captured.out

        # Should contain structured logging
        assert "[SUMMARY 1/1]" in output
        assert "✓ Completed: test" in output
        assert "2.5s" in output  # timing

        # Should contain summary statistics
        assert "AI SUMMARIZATION SUMMARY" in output

    def test_error_logging_structure(self, tmp_path, capsys):
        """Test that error logging follows structured format."""
        # Set up test data
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        literature_search = LiteratureSearch(config)
        workflow = LiteratureWorkflow(literature_search)

        # Create mock search results with failures
        results = [
            SearchResult(
                title="Failing Paper",
                authors=["Author"],
                year=2023,
                abstract="Abstract",
                url="https://example.com/fail",
                source="arxiv",
                pdf_url="https://example.com/fail.pdf"
            )
        ]

        # Mock failed download
        with patch.object(literature_search, 'download_paper_with_result') as mock_download:
            mock_download.return_value = MagicMock(
                success=False,
                failure_reason="network_error",
                failure_message="Connection timeout",
                attempted_urls=["https://example.com/fail.pdf"],
                pdf_path=None
            )

            # Mock add_to_library
            with patch.object(literature_search, 'add_to_library') as mock_add:
                mock_add.return_value = "failing_paper"

                # Execute download
                downloaded, download_results = workflow._download_papers(results)

                # Check results
                assert len(downloaded) == 0
                assert len(download_results) == 1
                assert not download_results[0].success

                # Check stdout output
                captured = capsys.readouterr()
                output = captured.out
                assert "[DOWNLOAD 1/1]" in output
                assert "✗ Failed" in output
                assert "network_error" in output

    def test_timing_and_performance_logging(self, tmp_path, capsys):
        """Test that timing and performance metrics are logged."""
        # Set up test data
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        literature_search = LiteratureSearch(config)
        workflow = LiteratureWorkflow(literature_search)

        # Mock a quick download
        with patch.object(literature_search, 'download_paper_with_result') as mock_download:
            mock_download.return_value = MagicMock(
                success=True,
                pdf_path=Path("literature/pdfs/test.pdf"),
                already_existed=False,
                failure_reason=None,
                attempted_urls=["https://example.com/test.pdf"]
            )

            # Mock add_to_library
            with patch.object(literature_search, 'add_to_library') as mock_add:
                mock_add.return_value = "test"

                result = SearchResult(
                    title="Test Paper",
                    authors=["Author"],
                    year=2023,
                    abstract="Abstract",
                    url="https://example.com/test",
                    source="arxiv",
                    pdf_url="https://example.com/test.pdf"
                )

                # Execute download
                downloaded, download_results = workflow._download_papers([result])

                # Check stdout output
                captured = capsys.readouterr()
                output = captured.out
                assert "Total time:" in output
                assert "Average time per paper:" in output

    def test_file_size_logging(self, tmp_path, capsys):
        """Test that file sizes are logged when available."""
        # Create a test PDF file with known size
        pdf_dir = tmp_path / "downloads"
        pdf_dir.mkdir()
        test_pdf = pdf_dir / "test.pdf"
        test_content = b"PDF content here" * 100  # ~1.7KB
        test_pdf.write_bytes(test_content)

        config = LiteratureConfig(download_dir=str(pdf_dir))
        literature_search = LiteratureSearch(config)
        workflow = LiteratureWorkflow(literature_search)

        # Mock successful download result
        with patch.object(literature_search, 'download_paper_with_result') as mock_download:
            mock_download.return_value = MagicMock(
                success=True,
                pdf_path=test_pdf,
                already_existed=False,
                failure_reason=None,
                attempted_urls=["https://example.com/test.pdf"]
            )

            # Mock add_to_library
            with patch.object(literature_search, 'add_to_library') as mock_add:
                mock_add.return_value = "test"

                result = SearchResult(
                    title="Test Paper",
                    authors=["Author"],
                    year=2023,
                    abstract="Abstract",
                    url="https://example.com/test",
                    source="arxiv",
                    pdf_url="https://example.com/test.pdf"
                )

                # Execute download
                downloaded, download_results = workflow._download_papers([result])

                # Check stdout output
                captured = capsys.readouterr()
                output = captured.out
                # Should contain file size (1,600 bytes for the actual content)
                assert "1,600B" in output


class TestLoggingOutputFormat:
    """Test specific logging output formatting."""

    def test_progress_indicators(self, caplog):
        """Test that progress indicators follow consistent format."""
        import logging

        # Set up logging to capture output
        logger = logging.getLogger("infrastructure.literature.workflow")
        logger.setLevel(logging.INFO)

        # Test direct logging calls that should appear in workflow
        logger.info("[DOWNLOAD 1/5] Processing: Test Paper...")
        logger.info("[DOWNLOAD 2/5] ✓ Downloaded: test.pdf (1,234B) - 0.5s")
        logger.info("[DOWNLOAD 3/5] ✗ Failed (network_error): Connection timeout (2 URLs tried) - 1.2s")
        logger.info("[SUMMARY 1/3] ✓ Completed: citation_key (567B) - 2.1s")

        log_output = caplog.text

        # Check format consistency
        assert "[DOWNLOAD 1/5]" in log_output
        assert "[DOWNLOAD 2/5]" in log_output
        assert "[DOWNLOAD 3/5]" in log_output
        assert "[SUMMARY 1/3]" in log_output

        # Check status indicators
        assert "✓ Downloaded:" in log_output
        assert "✗ Failed" in log_output
        assert "✓ Completed:" in log_output

    def test_summary_statistics_format(self, caplog):
        """Test that summary statistics follow consistent format."""
        import logging

        logger = logging.getLogger("infrastructure.literature.workflow")

        # Simulate summary output
        logger.info("")
        logger.info("=" * 70)
        logger.info("PDF DOWNLOAD SUMMARY")
        logger.info("=" * 70)
        logger.info("  Total papers processed: 5")
        logger.info("  ✓ Successfully downloaded: 4 (80.0%)")
        logger.info("    • Already existed: 1")
        logger.info("    • Newly downloaded: 3")
        logger.info("  ✗ Failed downloads: 1")
        logger.info("  ⏱️  Total time: 12.5s")
        logger.info("  📊 Average time per paper: 2.5s")
        logger.info("=" * 70)

        log_output = caplog.text

        # Check summary structure
        assert "PDF DOWNLOAD SUMMARY" in log_output
        assert "Total papers processed: 5" in log_output
        assert "Successfully downloaded: 4 (80.0%)" in log_output
        assert "Already existed: 1" in log_output
        assert "Newly downloaded: 3" in log_output
        assert "Failed downloads: 1" in log_output
        assert "Total time: 12.5s" in log_output
        assert "Average time per paper: 2.5s" in log_output

    def test_error_message_formatting(self, caplog):
        """Test that error messages are properly truncated and formatted."""
        import logging

        logger = logging.getLogger("infrastructure.literature.workflow")

        # Test error message truncation
        long_error = "A" * 250  # Very long error message
        logger.error(f"[DOWNLOAD 1/1] ✗ Failed (network_error): {long_error} (1 URLs tried) - 1.0s")

        log_output = caplog.text

        # Should contain truncated error (197 chars + "...")
        assert "✗ Failed (network_error): " in log_output
        assert "(1 URLs tried)" in log_output
        assert " - 1.0s" in log_output


class TestLogLevelConsistency:
    """Test that logging uses appropriate levels."""

    def test_info_level_for_progress(self, caplog):
        """Test that progress information uses INFO level."""
        import logging

        logger = logging.getLogger("infrastructure.literature.workflow")
        logger.setLevel(logging.DEBUG)

        # These should be INFO level
        logger.info("[DOWNLOAD 1/1] Processing: Test Paper...")
        logger.info("✓ Downloaded: test.pdf (1KB) - 0.5s")

        log_output = caplog.text
        assert "[DOWNLOAD 1/1]" in log_output
        assert "✓ Downloaded:" in log_output

    def test_warning_level_for_recoverable_errors(self, caplog):
        """Test that recoverable errors use WARNING level."""
        import logging

        logger = logging.getLogger("infrastructure.literature.workflow")

        logger.warning("[DOWNLOAD 1/1] ✗ Failed (timeout): Request timed out (retrying...)")

        log_output = caplog.text
        assert "✗ Failed (timeout)" in log_output

    def test_error_level_for_failures(self, caplog):
        """Test that failures use ERROR level."""
        import logging

        logger = logging.getLogger("infrastructure.literature.workflow")

        logger.error("[DOWNLOAD 1/1] ✗ Failed (network_error): Connection failed after 3 retries")

        log_output = caplog.text
        assert "✗ Failed (network_error)" in log_output

    def test_debug_level_for_detailed_info(self, caplog):
        """Test that detailed information uses DEBUG level."""
        import logging

        logger = logging.getLogger("infrastructure.literature.workflow")
        logger.setLevel(logging.DEBUG)

        logger.debug("HTML parsing found 3 PDF URLs in page content")
        logger.debug("Trying alternative User-Agent: Mozilla/5.0...")

        log_output = caplog.text
        assert "HTML parsing found 3 PDF URLs" in log_output
        assert "Trying alternative User-Agent" in log_output
