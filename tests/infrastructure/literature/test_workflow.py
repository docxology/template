"""Tests for literature workflow orchestration."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from infrastructure.literature.api import SearchResult
from infrastructure.literature.workflow import LiteratureWorkflow, WorkflowResult
from infrastructure.literature.summarizer import SummarizationResult


class TestWorkflowResult:
    """Test WorkflowResult dataclass."""

    def test_creation(self):
        """Test WorkflowResult creation."""
        result = WorkflowResult(keywords=["test", "keywords"])

        assert result.keywords == ["test", "keywords"]
        assert result.papers_found == 0
        assert result.papers_downloaded == 0
        assert result.papers_failed_download == 0
        assert result.summaries_generated == 0
        assert result.summaries_failed == 0
        assert result.total_time == 0.0
        assert result.download_results == []
        assert result.summarization_results == []
        assert result.progress is None

    def test_success_rate_no_data(self):
        """Test success rate with no data."""
        result = WorkflowResult(["test"])
        assert result.success_rate == 0.0

    def test_success_rate_with_data(self):
        """Test success rate calculation."""
        result = WorkflowResult(["test"])
        result.papers_downloaded = 5
        result.papers_failed_download = 2
        result.summaries_generated = 3
        result.summaries_failed = 2

        # Success rate should be summaries_generated / (downloaded + failed_download)
        expected = 3 / 7 * 100  # 3 successful summaries out of 7 total operations
        assert result.success_rate == expected

    def test_completion_rate_no_papers(self):
        """Test completion rate with no papers."""
        result = WorkflowResult(["test"])
        assert result.completion_rate == 0.0

    def test_completion_rate_with_data(self):
        """Test completion rate calculation."""
        result = WorkflowResult(["test"])
        result.papers_found = 10
        result.summaries_generated = 7  # 7 out of 10 completed successfully

        expected = 7 / 10 * 100
        assert result.completion_rate == expected


class TestLiteratureWorkflow:
    """Test LiteratureWorkflow orchestration."""

    def test_creation(self):
        """Test workflow creation."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)

        assert workflow.literature_search is literature_search
        assert workflow.summarizer is None
        assert workflow.progress_tracker is None

    def test_set_summarizer(self):
        """Test setting summarizer."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)
        summarizer = Mock()

        workflow.set_summarizer(summarizer)
        assert workflow.summarizer is summarizer

    def test_set_progress_tracker(self):
        """Test setting progress tracker."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)
        tracker = Mock()

        workflow.set_progress_tracker(tracker)
        assert workflow.progress_tracker is tracker

    @patch('infrastructure.literature.workflow.time')
    @patch.object(LiteratureWorkflow, '_summarize_papers_parallel')
    def test_execute_search_and_summarize(self, mock_summarize_parallel, mock_time):
        """Test complete workflow execution."""
        mock_time.time.side_effect = [1000.0, 1001.0, 1002.0, 1100.0]  # Start time, download times, end time

        # Setup mocks
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()

        # Mock existing progress to avoid resume prompt
        progress_tracker.load_existing_run.return_value = None

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Mock search results
        search_results = [
            SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv", pdf_url="pdf1"),
            SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url2", source="arxiv", pdf_url="pdf2")
        ]
        literature_search.search.return_value = search_results
        literature_search._deduplicate_results.return_value = search_results

        # Mock download results
        download_results = [
            Mock(success=True, pdf_path=Path("paper1.pdf"), citation_key="paper1"),
            Mock(success=True, pdf_path=Path("paper2.pdf"), citation_key="paper2")
        ]
        literature_search.download_paper_with_result.side_effect = download_results

        # Mock summarization results
        summary_results = [
            SummarizationResult("paper1", True, "Summary 1", attempts=1),
            SummarizationResult("paper2", True, "Summary 2", attempts=1)
        ]
        mock_summarize_parallel.return_value = summary_results

        # Execute
        result = workflow.execute_search_and_summarize(
            keywords=["test"],
            limit_per_keyword=10,
            max_parallel_summaries=2
        )

        # Verify
        assert result.keywords == ["test"]
        assert result.papers_found == 2
        assert result.papers_downloaded == 2
        assert result.papers_failed_download == 0
        assert result.summaries_generated == 2
        assert result.summaries_failed == 0
        assert result.total_time == 100.0  # 1100 - 1000

        # Verify method calls
        literature_search.search.assert_called_once_with("test", limit=10)
        assert workflow._summarize_papers_parallel.called

    def test_search_papers(self):
        """Test paper search functionality."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)

        # Setup mock responses
        arxiv_results = [SearchResult("ArXiv Paper", ["Author"], 2024, "Abstract", "url", source="arxiv")]
        semanticscholar_results = [SearchResult("SS Paper", ["Author"], 2024, "Abstract", "url", source="semanticscholar")]

        literature_search.search.side_effect = [arxiv_results, semanticscholar_results]
        literature_search._deduplicate_results.return_value = arxiv_results + semanticscholar_results

        results = workflow._search_papers(["keyword1", "keyword2"], 10)

        assert len(results) == 2
        assert literature_search.search.call_count == 2

    def test_download_papers(self):
        """Test paper download functionality."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)

        # Setup test data
        results = [
            SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv", pdf_url="pdf1"),
            SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url2", source="arxiv", pdf_url="pdf2")
        ]

        # Mock download results
        download_results = [
            Mock(success=True, pdf_path=Path("paper1.pdf"), citation_key="paper1"),
            Mock(success=True, pdf_path=Path("paper2.pdf"), citation_key="paper2")
        ]
        literature_search.download_paper_with_result.side_effect = download_results
        literature_search.add_to_library.side_effect = ["key1", "key2"]

        downloaded, download_result_list = workflow._download_papers(results)

        assert len(downloaded) == 2
        assert len(download_result_list) == 2
        assert downloaded[0][0] == results[0]
        assert downloaded[0][1] == Path("paper1.pdf")

    @patch.object(LiteratureWorkflow, '_summarize_single_paper')
    def test_summarize_papers_parallel_single_worker(self, mock_summarize_single):
        """Test parallel summarization with single worker."""
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Setup test data
        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url", source="arxiv"), Path("paper1.pdf")),
            (SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url", source="arxiv"), Path("paper2.pdf"))
        ]

        # Mock progress - both papers need processing
        progress_tracker.current_progress.entries = {
            "paper1": Mock(status="downloaded"),
            "paper2": Mock(status="downloaded")
        }

        # Mock summarization
        summary_results = [
            SummarizationResult("paper1", True, "Summary 1"),
            SummarizationResult("paper2", True, "Summary 2")
        ]
        mock_summarize_single.side_effect = summary_results

        results = workflow._summarize_papers_parallel(downloaded, max_workers=1)

        assert len(results) == 2
        assert mock_summarize_single.call_count == 2

    @patch.object(LiteratureWorkflow, '_summarize_single_paper')
    def test_summarize_papers_parallel_multiple_workers(self, mock_summarize_single):
        """Test parallel summarization with multiple workers."""
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Setup test data
        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url", source="arxiv"), Path("paper1.pdf")),
        ]

        # Mock progress
        progress_tracker.current_progress.entries = {
            "paper1": Mock(status="downloaded")
        }

        # Mock summarization
        summary_result = SummarizationResult("paper1", True, "Summary 1")
        mock_summarize_single.return_value = summary_result

        results = workflow._summarize_papers_parallel(downloaded, max_workers=2)

        assert len(results) == 1
        assert results[0] == summary_result

    def test_summarize_single_paper(self):
        """Test single paper summarization."""
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        result = SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url", source="arxiv")
        pdf_path = Path("paper1.pdf")

        # Mock progress entry
        progress_entry = Mock(status="downloaded", summary_attempts=0)
        progress_tracker.current_progress.entries = {"paper1": progress_entry}

        # Mock summarization
        summary_result = SummarizationResult("paper1", True, "Summary")
        summarizer.summarize_paper.return_value = summary_result

        result = workflow._summarize_single_paper(result, pdf_path)

        assert result == summary_result
        progress_tracker.update_entry_status.assert_called()

    def test_save_summaries(self):
        """Test summary saving functionality."""
        literature_search = Mock()
        summarizer = Mock()

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)

        # Setup test data
        search_results = [
            SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url", source="arxiv"),
            SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url", source="arxiv")
        ]

        summary_results = [
            SummarizationResult("paper1", True, "Summary 1"),
            SummarizationResult("paper2", True, "Summary 2")
        ]

        results = list(zip(search_results, summary_results))

        # Mock save method
        summarizer.save_summary.side_effect = [Path("summary1.md"), Path("summary2.md")]

        output_dir = Path("summaries")
        saved_paths = workflow.save_summaries(results, output_dir)

        assert len(saved_paths) == 2
        assert summarizer.save_summary.call_count == 2

    def test_get_workflow_stats(self):
        """Test workflow statistics generation."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)

        result = WorkflowResult(["test", "keywords"])
        result.papers_found = 10
        result.papers_downloaded = 8
        result.papers_failed_download = 2
        result.summaries_generated = 6
        result.summaries_failed = 2
        result.total_time = 300.0

        stats = workflow.get_workflow_stats(result)

        assert stats["search"]["keywords"] == ["test", "keywords"]
        assert stats["search"]["papers_found"] == 10
        assert stats["downloads"]["successful"] == 8
        assert stats["downloads"]["failed"] == 2
        assert stats["summarization"]["successful"] == 6
        assert stats["summarization"]["failed"] == 2
        assert stats["timing"]["total_time_seconds"] == 300.0

    def test_workflow_without_summarizer(self):
        """Test workflow execution without summarizer set."""
        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)

        with pytest.raises(ValueError, match="Summarizer not configured"):
            workflow._summarize_papers_parallel([], 1)

    @patch('infrastructure.literature.workflow.time')
    def test_summarize_single_paper_saves_summary(self, mock_time, tmp_path):
        """Test that _summarize_single_paper saves successful summaries."""
        mock_time.time.return_value = 1000.0

        # Setup mocks
        literature_search = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()

        # Mock progress entry
        mock_entry = Mock()
        mock_entry.status = "downloaded"
        progress_tracker.current_progress.entries = {"test2024": mock_entry}

        # Create workflow with mock summarizer
        workflow = LiteratureWorkflow(literature_search)
        workflow.set_progress_tracker(progress_tracker)

        # Mock summarizer
        mock_summarizer = Mock()
        workflow.set_summarizer(mock_summarizer)

        # Mock summarization success
        summary_result = SummarizationResult(
            citation_key="test2024",
            success=True,
            summary_text="Test summary content",
            attempts=1,
            generation_time=1000.0
        )
        mock_summarizer.summarize_paper.return_value = summary_result

        # Mock save_summary to return a path
        mock_saved_path = tmp_path / "literature" / "summaries" / "test2024_summary.md"
        mock_summarizer.save_summary.return_value = mock_saved_path

        # Mock search result
        search_result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="url",
            source="arxiv"
        )

        pdf_path = Path("test2024.pdf")

        # Execute
        result = workflow._summarize_single_paper(search_result, pdf_path)

        # Verify save_summary was called
        mock_summarizer.save_summary.assert_called_once_with(
            search_result, summary_result, Path("literature/summaries")
        )

        # Verify summary_path was set
        assert result.summary_path == mock_saved_path

        # Verify progress tracking was updated with summary_path
        progress_tracker.update_entry_status.assert_called_with(
            "test2024", "summarized",
            summary_path=str(mock_saved_path),
            summary_attempts=1,
            summary_time=1000.0
        )

    @patch('infrastructure.literature.workflow.time')
    def test_summarize_single_paper_save_failure_handling(self, mock_time, tmp_path):
        """Test that _summarize_single_paper handles save failures gracefully."""
        mock_time.time.return_value = 1000.0

        # Setup mocks
        literature_search = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()

        # Mock progress entry
        mock_entry = Mock()
        mock_entry.status = "downloaded"
        progress_tracker.current_progress.entries = {"test2024": mock_entry}

        # Create workflow with mock summarizer
        workflow = LiteratureWorkflow(literature_search)
        workflow.set_progress_tracker(progress_tracker)

        # Mock summarizer
        mock_summarizer = Mock()
        workflow.set_summarizer(mock_summarizer)

        # Mock summarization success
        summary_result = SummarizationResult(
            citation_key="test2024",
            success=True,
            summary_text="Test summary content",
            attempts=1
        )
        mock_summarizer.summarize_paper.return_value = summary_result

        # Mock save_summary to raise exception
        mock_summarizer.save_summary.side_effect = Exception("Disk full")

        # Mock search result
        search_result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="url",
            source="arxiv"
        )

        pdf_path = Path("test2024.pdf")

        # Execute
        result = workflow._summarize_single_paper(search_result, pdf_path)

        # Verify summary was marked as failed due to save error
        assert result.success is False
        assert "Summary generation succeeded but save failed" in result.error

        # Verify progress tracking was updated with failure
        progress_tracker.update_entry_status.assert_called_with(
            "test2024", "failed",
            last_error="Summary generation succeeded but save failed: Disk full",
            summary_attempts=1
        )

    @patch('infrastructure.literature.workflow.time')
    def test_summarize_single_paper_no_save_for_failed_summary(self, mock_time):
        """Test that save_summary is not called for failed summarizations."""
        mock_time.time.return_value = 1000.0

        # Setup mocks
        literature_search = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()

        # Mock progress entry
        mock_entry = Mock()
        mock_entry.status = "downloaded"
        progress_tracker.current_progress.entries = {"test2024": mock_entry}

        # Create workflow with mock summarizer
        workflow = LiteratureWorkflow(literature_search)
        workflow.set_progress_tracker(progress_tracker)

        # Mock summarizer
        mock_summarizer = Mock()
        workflow.set_summarizer(mock_summarizer)

        # Mock summarization failure (no summary text)
        summary_result = SummarizationResult(
            citation_key="test2024",
            success=False,
            error="PDF extraction failed",
            attempts=1
        )
        mock_summarizer.summarize_paper.return_value = summary_result

        # Mock search result
        search_result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="url",
            source="arxiv"
        )

        pdf_path = Path("test2024.pdf")

        # Execute
        result = workflow._summarize_single_paper(search_result, pdf_path)

        # Verify save_summary was NOT called
        mock_summarizer.save_summary.assert_not_called()

        # Verify result unchanged
        assert result.success is False
        assert result.error == "PDF extraction failed"

        # Verify progress tracking updated with failure
        progress_tracker.update_entry_status.assert_called_with(
            "test2024", "failed",
            last_error="PDF extraction failed",
            summary_attempts=1
        )
