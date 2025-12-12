"""Tests for skip-existing-summaries functionality in literature workflow.

This test suite verifies that the workflow correctly detects and skips
summaries that already exist on disk, even when progress tracker doesn't
know about them.

Some tests use mocks for parallel processing behavior testing.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock

from infrastructure.literature.sources import SearchResult
from infrastructure.literature.workflow import LiteratureWorkflow
from infrastructure.literature.summarization import SummarizationResult, SummarizationEngine
from infrastructure.literature.workflow import ProgressTracker, SummarizationProgress
from infrastructure.literature.core import LiteratureSearch
from infrastructure.literature.core import LiteratureConfig


class TestSkipExistingSummaries:
    """Test skip-existing-summaries functionality."""

    def test_get_summary_path(self, tmp_path):
        """Test _get_summary_path helper method."""
        config = LiteratureConfig()
        config.download_dir = str(tmp_path / "pdfs")
        literature_search = LiteratureSearch(config)
        workflow = LiteratureWorkflow(literature_search)
        
        path = workflow._get_summary_path("test2024")
        expected = Path("data/summaries") / "test2024_summary.md"
        
        assert path == expected

    def test_summarize_single_paper_skips_existing_file(self, tmp_path):
        """Test that _summarize_single_paper skips when summary file exists."""
        # Setup real objects
        config = LiteratureConfig()
        config.download_dir = str(tmp_path / "pdfs")
        literature_search = LiteratureSearch(config)
        
        # Create a real summarizer with LLMClient (won't be called if file exists)
        # Skip test if Ollama unavailable
        try:
            from infrastructure.llm import LLMClient
            llm_client = LLMClient()
            summarizer = SummarizationEngine(llm_client=llm_client)
        except Exception:
            pytest.skip("LLMClient unavailable - cannot create SummarizationEngine")
        
        # Create real progress tracker
        progress_file = tmp_path / "progress.json"
        progress_tracker = ProgressTracker(progress_file=progress_file)

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Create existing summary file
        summaries_dir = tmp_path / "literature" / "summaries"
        summaries_dir.mkdir(parents=True)
        existing_summary = summaries_dir / "test2024_summary.md"
        existing_summary.write_text("# Test Paper\n\nExisting summary content")

        # Override path method to use tmp_path
        workflow._get_summary_path = lambda key: summaries_dir / f"{key}_summary.md"

        search_result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2024,
            abstract="Abstract",
            url="url",
            source="arxiv"
        )
        pdf_path = tmp_path / "test2024.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        # Execute
        result = workflow._summarize_single_paper(search_result, pdf_path)

        # Verify summary was skipped
        assert result.success is True
        assert result.skipped is True
        assert result.summary_path == existing_summary
        assert result.citation_key == "test2024"

    def test_summarize_papers_parallel_filters_existing_files(self, tmp_path):
        """Test that _summarize_papers_parallel filters out existing summaries."""
        # Setup
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()
        progress_tracker.current_progress.entries = {}

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Create existing summary for one paper
        summaries_dir = tmp_path / "literature" / "summaries"
        summaries_dir.mkdir(parents=True)
        existing_summary = summaries_dir / "paper1_summary.md"
        existing_summary.write_text("# Paper 1\n\nExisting summary")

        # Setup test data
        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv"), Path("paper1.pdf")),
            (SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url2", source="arxiv"), Path("paper2.pdf"))
        ]

        # Mock path construction
        def get_summary_path(key):
            return summaries_dir / f"{key}_summary.md"
        workflow._get_summary_path = get_summary_path

        # Mock summarization for paper2 (paper1 should be skipped)
        summary_result = SummarizationResult("paper2", True, "Summary 2")
        summarizer.summarize_paper.return_value = summary_result

        # Mock _summarize_single_paper to handle both cases
        def summarize_single(result, pdf_path):
            citation_key = pdf_path.stem
            summary_path = get_summary_path(citation_key)
            if summary_path.exists():
                return SummarizationResult(
                    citation_key=citation_key,
                    success=True,
                    summary_path=summary_path,
                    skipped=True
                )
            return summary_result

        workflow._summarize_single_paper = summarize_single

        # Execute
        results = workflow._summarize_papers_parallel(downloaded, max_workers=1)

        # Verify
        assert len(results) == 2  # One skipped, one generated
        
        # Check that paper1 was skipped
        skipped_result = next(r for r in results if r.citation_key == "paper1")
        assert skipped_result.success is True
        assert skipped_result.skipped is True
        assert skipped_result.summary_path == existing_summary

        # Check that paper2 was processed
        generated_result = next(r for r in results if r.citation_key == "paper2")
        assert generated_result.success is True
        assert generated_result.skipped is False

    def test_summarize_papers_parallel_checks_file_before_progress_tracker(self, tmp_path):
        """Test that file existence is checked even if progress tracker doesn't know about it."""
        # Setup
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()
        # Progress tracker has no entry for this paper
        progress_tracker.current_progress.entries = {}

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Create existing summary file (but progress tracker doesn't know)
        summaries_dir = tmp_path / "literature" / "summaries"
        summaries_dir.mkdir(parents=True)
        existing_summary = summaries_dir / "paper1_summary.md"
        existing_summary.write_text("# Paper 1\n\nExisting summary")

        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv"), Path("paper1.pdf"))
        ]

        # Mock path construction
        def get_summary_path(key):
            return summaries_dir / f"{key}_summary.md"
        workflow._get_summary_path = get_summary_path

        # Execute
        results = workflow._summarize_papers_parallel(downloaded, max_workers=1)

        # Verify summary was skipped even though progress tracker didn't know
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].skipped is True
        assert results[0].summary_path == existing_summary

        # Verify summarizer was NOT called
        summarizer.summarize_paper.assert_not_called()

    def test_summarize_papers_parallel_all_existing_returns_skipped_results(self, tmp_path):
        """Test that all existing summaries return skipped results."""
        # Setup
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()
        progress_tracker.current_progress.entries = {}

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Create existing summaries for all papers
        summaries_dir = tmp_path / "literature" / "summaries"
        summaries_dir.mkdir(parents=True)
        (summaries_dir / "paper1_summary.md").write_text("# Paper 1")
        (summaries_dir / "paper2_summary.md").write_text("# Paper 2")

        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv"), Path("paper1.pdf")),
            (SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url2", source="arxiv"), Path("paper2.pdf"))
        ]

        # Mock path construction
        def get_summary_path(key):
            return summaries_dir / f"{key}_summary.md"
        workflow._get_summary_path = get_summary_path

        # Execute
        results = workflow._summarize_papers_parallel(downloaded, max_workers=1)

        # Verify all were skipped
        assert len(results) == 2
        assert all(r.skipped for r in results)
        assert all(r.success for r in results)

        # Verify summarizer was never called
        summarizer.summarize_paper.assert_not_called()

    def test_workflow_result_tracks_skipped_summaries(self):
        """Test that WorkflowResult correctly tracks skipped summaries."""
        from infrastructure.literature.workflow import WorkflowResult

        result = WorkflowResult(keywords=["test"])
        result.summaries_generated = 5
        result.summaries_skipped = 3
        result.summaries_failed = 1

        assert result.summaries_generated == 5
        assert result.summaries_skipped == 3
        assert result.summaries_failed == 1

    def test_workflow_stats_includes_skipped_summaries(self):
        """Test that get_workflow_stats includes skipped summaries."""
        from infrastructure.literature.workflow import LiteratureWorkflow, WorkflowResult

        literature_search = Mock()
        workflow = LiteratureWorkflow(literature_search)

        result = WorkflowResult(keywords=["test"])
        result.summaries_generated = 5
        result.summaries_skipped = 3
        result.summaries_failed = 1

        stats = workflow.get_workflow_stats(result)

        assert stats["summarization"]["successful"] == 5
        assert stats["summarization"]["skipped"] == 3
        assert stats["summarization"]["failed"] == 1

    def test_skip_existing_without_progress_tracker(self, tmp_path):
        """Test that file existence check works even without progress tracker."""
        # Setup
        literature_search = Mock()
        summarizer = Mock()

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        # No progress tracker set

        # Create existing summary file
        summaries_dir = tmp_path / "literature" / "summaries"
        summaries_dir.mkdir(parents=True)
        existing_summary = summaries_dir / "paper1_summary.md"
        existing_summary.write_text("# Paper 1\n\nExisting summary")

        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv"), Path("paper1.pdf"))
        ]

        # Mock path construction
        def get_summary_path(key):
            return summaries_dir / f"{key}_summary.md"
        workflow._get_summary_path = get_summary_path

        # Execute
        results = workflow._summarize_papers_parallel(downloaded, max_workers=1)

        # Verify summary was skipped
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].skipped is True
        assert results[0].summary_path == existing_summary

        # Verify summarizer was NOT called
        summarizer.summarize_paper.assert_not_called()

    def test_mixed_existing_and_new_summaries(self, tmp_path):
        """Test workflow with mix of existing and new summaries."""
        # Setup
        literature_search = Mock()
        summarizer = Mock()
        progress_tracker = Mock()
        progress_tracker.current_progress = Mock()
        progress_tracker.current_progress.entries = {}

        workflow = LiteratureWorkflow(literature_search)
        workflow.set_summarizer(summarizer)
        workflow.set_progress_tracker(progress_tracker)

        # Create existing summary for one paper
        summaries_dir = tmp_path / "literature" / "summaries"
        summaries_dir.mkdir(parents=True)
        (summaries_dir / "paper1_summary.md").write_text("# Paper 1\n\nExisting")

        downloaded = [
            (SearchResult("Paper 1", ["Author"], 2024, "Abstract", "url1", source="arxiv"), Path("paper1.pdf")),
            (SearchResult("Paper 2", ["Author"], 2024, "Abstract", "url2", source="arxiv"), Path("paper2.pdf"))
        ]

        # Mock path construction
        def get_summary_path(key):
            return summaries_dir / f"{key}_summary.md"
        workflow._get_summary_path = get_summary_path

        # Mock summarization for paper2
        summary_result = SummarizationResult("paper2", True, "Summary 2")
        summarizer.summarize_paper.return_value = summary_result

        # Mock _summarize_single_paper
        def summarize_single(result, pdf_path):
            citation_key = pdf_path.stem
            summary_path = get_summary_path(citation_key)
            if summary_path.exists():
                return SummarizationResult(
                    citation_key=citation_key,
                    success=True,
                    summary_path=summary_path,
                    skipped=True
                )
            # Actually call the summarizer for new papers
            return summarizer.summarize_paper(result, pdf_path)

        workflow._summarize_single_paper = summarize_single

        # Execute
        results = workflow._summarize_papers_parallel(downloaded, max_workers=2)

        # Verify
        assert len(results) == 2
        
        # Paper 1 should be skipped
        paper1_result = next(r for r in results if r.citation_key == "paper1")
        assert paper1_result.skipped is True
        assert paper1_result.success is True

        # Paper 2 should be generated
        paper2_result = next(r for r in results if r.citation_key == "paper2")
        assert paper2_result.skipped is False
        assert paper2_result.success is True

        # Verify summarizer was only called for paper2
        assert summarizer.summarize_paper.call_count == 1

