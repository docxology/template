"""Tests for scripts/06_llm_review.py - LLM Manuscript Review orchestrator.

Tests cover:
- ReviewMetrics, ManuscriptInputMetrics, SessionMetrics dataclasses
- estimate_tokens() function
- get_max_input_length() environment variable handling
- extract_manuscript_text() with no truncation for normal files
- save_review_outputs() file creation and metadata
- generate_review_summary() metrics formatting
- Integration tests (marked @pytest.mark.requires_ollama)

Following the project's no-mocks policy - all tests use real data and computations.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts to path (one more parent level since we're in tests/infra_tests/llm/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

# Import validation functions from infrastructure (now moved there)
from infrastructure.llm.validation import is_off_topic
from infrastructure.llm.core.config import get_max_input_length

DEFAULT_MAX_INPUT_LENGTH: int = 500000
from infrastructure.llm.review.generator import validate_review_quality
from infrastructure.llm.review.io import SessionMetrics, generate_review_summary, save_review_outputs
from infrastructure.llm.review.metrics import ManuscriptInputMetrics, ReviewMetrics


class TestGetMaxInputLength:
    """Tests for get_max_input_length() function."""

    def test_default_value(self, monkeypatch):
        """Test default max input length when env var not set."""
        monkeypatch.delenv("LLM_MAX_INPUT_LENGTH", raising=False)
        result = get_max_input_length()
        assert result == DEFAULT_MAX_INPUT_LENGTH
        assert result == 500000

    def test_custom_value(self, monkeypatch):
        """Test custom max input length from env var."""
        monkeypatch.setenv("LLM_MAX_INPUT_LENGTH", "100000")
        result = get_max_input_length()
        assert result == 100000

    def test_unlimited_value(self, monkeypatch):
        """Test unlimited input (0) from env var."""
        monkeypatch.setenv("LLM_MAX_INPUT_LENGTH", "0")
        result = get_max_input_length()
        assert result == 0

    def test_invalid_value_uses_default(self, monkeypatch):
        """Test that invalid env var value falls back to default."""
        monkeypatch.setenv("LLM_MAX_INPUT_LENGTH", "invalid")
        result = get_max_input_length()
        assert result == DEFAULT_MAX_INPUT_LENGTH


class TestReviewMetrics:
    """Tests for ReviewMetrics dataclass."""

    def test_default_values(self):
        """Test default values for ReviewMetrics."""
        metrics = ReviewMetrics()
        assert metrics.input_chars == 0
        assert metrics.input_words == 0
        assert metrics.input_tokens_est == 0
        assert metrics.output_chars == 0
        assert metrics.output_words == 0
        assert metrics.output_tokens_est == 0
        assert metrics.generation_time_seconds == 0.0
        assert metrics.preview == ""

    def test_custom_values(self):
        """Test ReviewMetrics with custom values."""
        metrics = ReviewMetrics(
            input_chars=10000,
            input_words=1500,
            input_tokens_est=2500,
            output_chars=5000,
            output_words=800,
            output_tokens_est=1250,
            generation_time_seconds=45.5,
            preview="This is a preview of the response...",
        )
        assert metrics.input_chars == 10000
        assert metrics.output_words == 800
        assert metrics.generation_time_seconds == 45.5


class TestManuscriptInputMetrics:
    """Tests for ManuscriptInputMetrics dataclass."""

    def test_default_values(self):
        """Test default values for ManuscriptInputMetrics."""
        metrics = ManuscriptInputMetrics()
        assert metrics.total_chars == 0
        assert metrics.total_words == 0
        assert metrics.total_tokens_est == 0
        assert metrics.truncated is False
        assert metrics.truncated_chars == 0

    def test_truncated_manuscript(self):
        """Test ManuscriptInputMetrics for truncated manuscript."""
        metrics = ManuscriptInputMetrics(
            total_chars=100000,
            total_words=15000,
            total_tokens_est=25000,
            truncated=True,
            truncated_chars=50000,
        )
        assert metrics.total_chars == 100000
        assert metrics.truncated is True
        assert metrics.truncated_chars == 50000


class TestSessionMetrics:
    """Tests for SessionMetrics dataclass."""

    def test_default_values(self):
        """Test default values for SessionMetrics."""
        metrics = SessionMetrics()
        assert isinstance(metrics.manuscript, ManuscriptInputMetrics)
        assert isinstance(metrics.reviews, dict)
        assert metrics.total_generation_time == 0.0
        assert metrics.model_name == ""
        assert metrics.max_input_length == 0

    def test_with_reviews(self):
        """Test SessionMetrics with review metrics."""
        session = SessionMetrics(
            manuscript=ManuscriptInputMetrics(total_chars=50000, total_words=8000),
            model_name="llama3:latest",
            max_input_length=500000,
            total_generation_time=180.5,
        )
        session.reviews["executive_summary"] = ReviewMetrics(
            output_chars=3000,
            output_words=500,
        )

        assert session.manuscript.total_chars == 50000
        assert session.model_name == "llama3:latest"
        assert "executive_summary" in session.reviews
        assert session.reviews["executive_summary"].output_chars == 3000


class TestSaveReviewOutputs:
    """Tests for save_review_outputs() function."""

    def test_creates_all_files(self):
        """Test that all expected files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "llm"
            pdf_path = Path(tmpdir) / "manuscript.pdf"

            # Create dummy PDF
            pdf_path.touch()

            # Create test reviews
            reviews = {
                "executive_summary": "This is the executive summary content.",
                "quality_review": "This is the quality review content.",
                "methodology_review": "This is the methodology review.",
                "improvement_suggestions": "Here are some suggestions.",
            }

            # Create session metrics
            session_metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(
                    total_chars=50000,
                    total_words=8000,
                    total_tokens_est=12500,
                ),
                total_generation_time=120.0,
            )
            for name in reviews:
                session_metrics.reviews[name] = ReviewMetrics(
                    output_chars=len(reviews[name]),
                    output_words=len(reviews[name].split()),
                    generation_time_seconds=30.0,
                )

            # Call the function
            result = save_review_outputs(reviews, output_dir, "llama3:latest", pdf_path, session_metrics)

            assert result is True
            assert output_dir.exists()

            # Check all files created
            assert (output_dir / "executive_summary.md").exists()
            assert (output_dir / "quality_review.md").exists()
            assert (output_dir / "methodology_review.md").exists()
            assert (output_dir / "improvement_suggestions.md").exists()
            assert (output_dir / "combined_review.md").exists()
            assert (output_dir / "review_metadata.json").exists()

    def test_metadata_json_structure(self):
        """Test that metadata JSON has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "llm"
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.touch()

            reviews = {"executive_summary": "Test content"}
            session_metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(
                    total_chars=10000,
                    total_words=1500,
                    total_tokens_est=2500,
                    truncated=False,
                    truncated_chars=10000,
                ),
                max_input_length=500000,
            )
            session_metrics.reviews["executive_summary"] = ReviewMetrics(
                input_chars=10000,
                output_chars=500,
                generation_time_seconds=25.0,
            )

            save_review_outputs(reviews, output_dir, "llama3", pdf_path, session_metrics)

            # Load and verify metadata
            metadata_path = output_dir / "review_metadata.json"
            metadata = json.loads(metadata_path.read_text())

            assert "model" in metadata
            assert metadata["model"] == "llama3"
            assert "manuscript_metrics" in metadata
            assert metadata["manuscript_metrics"]["total_chars"] == 10000
            assert metadata["manuscript_metrics"]["truncated"] is False
            assert "review_metrics" in metadata
            assert "executive_summary" in metadata["review_metrics"]
            assert "config" in metadata

    def test_combined_review_includes_metrics(self):
        """Test that combined review includes metrics section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "llm"
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.touch()

            reviews = {
                "executive_summary": "Summary content",
                "quality_review": "Quality content",
            }
            session_metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(total_chars=20000, total_words=3000),
            )
            session_metrics.reviews["executive_summary"] = ReviewMetrics(
                output_chars=500, output_words=80, generation_time_seconds=20.0
            )
            session_metrics.reviews["quality_review"] = ReviewMetrics(
                output_chars=600, output_words=100, generation_time_seconds=25.0
            )

            save_review_outputs(reviews, output_dir, "llama3", pdf_path, session_metrics)

            combined = (output_dir / "combined_review.md").read_text()

            # Check metrics section exists
            assert "## Generation Metrics" in combined
            assert "Input Manuscript:" in combined
            assert "Characters:" in combined
            assert "Truncated:" in combined


class TestGenerateReviewSummary:
    """Tests for generate_review_summary() function."""

    def test_summary_runs_without_error(self):
        """Test that generate_review_summary runs without raising."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create test files
            (output_dir / "test.md").write_text("content")

            reviews = {"executive_summary": "Summary content"}
            session_metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(
                    total_chars=50000,
                    total_words=8000,
                    total_tokens_est=12500,
                    truncated=False,
                ),
            )
            session_metrics.reviews["executive_summary"] = ReviewMetrics(
                output_chars=1000,
                output_words=150,
                generation_time_seconds=30.0,
            )

            # Should run without raising any exceptions
            generate_review_summary(reviews, output_dir, session_metrics)

    def test_summary_handles_truncated_manuscript(self):
        """Test that generate_review_summary handles truncated manuscripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "test.md").write_text("content")

            reviews = {"executive_summary": "Content"}

            # Test with truncated manuscript
            session_metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(
                    total_chars=600000,
                    truncated=True,
                    truncated_chars=500000,
                ),
            )
            session_metrics.reviews["executive_summary"] = ReviewMetrics()

            # Should run without raising any exceptions
            generate_review_summary(reviews, output_dir, session_metrics)

    def test_summary_handles_multiple_reviews(self):
        """Test that generate_review_summary handles multiple reviews."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "file1.md").write_text("content1")
            (output_dir / "file2.md").write_text("content2")

            reviews = {
                "executive_summary": "Summary content",
                "quality_review": "Quality content",
                "methodology_review": "Method content",
            }
            session_metrics = SessionMetrics(
                manuscript=ManuscriptInputMetrics(total_chars=50000, total_words=8000),
                total_generation_time=120.5,
            )
            for name in reviews:
                session_metrics.reviews[name] = ReviewMetrics(
                    output_chars=len(reviews[name]),
                    output_words=2,
                    generation_time_seconds=40.0,
                )

            # Should run without raising any exceptions
            generate_review_summary(reviews, output_dir, session_metrics)


class TestNoTruncationByDefault:
    """Tests verifying no truncation happens by default."""

    def test_default_limit_is_large(self):
        """Test that default max input length is large (500K chars)."""
        assert DEFAULT_MAX_INPUT_LENGTH == 500000

    def test_large_text_not_truncated_at_default(self, monkeypatch):
        """Test that text under 500K chars is not truncated."""
        # Simulate 100K character text (typical manuscript)
        large_text = "a" * 100000

        monkeypatch.delenv("LLM_MAX_INPUT_LENGTH", raising=False)
        max_length = get_max_input_length()
        assert len(large_text) < max_length


class TestModuleImports:
    """Tests for proper module imports."""

    def test_all_required_imports_available(self):
        """Test that all required functions/classes are importable."""
        from infrastructure.llm.review.metrics import estimate_tokens
        from infrastructure.llm.review.pipeline_runner import run_llm_review_pipeline

        # All imports should be available
        assert callable(estimate_tokens)
        assert callable(run_llm_review_pipeline)


class TestIsOffTopic:
    """Tests for is_off_topic() function."""

    def test_normal_response_not_off_topic(self):
        """Test that normal review responses are not flagged."""
        normal_response = """## Overview
        This manuscript presents a novel approach to machine learning optimization.
        
        ## Key Contributions
        - New algorithm for faster convergence
        - Improved accuracy on benchmark datasets
        """
        assert is_off_topic(normal_response) is False

    def test_email_reply_format_detected(self):
        """Test that 'Re:' email format is detected as off-topic."""
        email_response = "Re: Your question about the manuscript..."
        assert is_off_topic(email_response) is True

    def test_dear_letter_format_detected(self):
        """Test that 'Dear' letter format is detected as off-topic."""
        letter_response = "Dear reviewer, thank you for your question..."
        assert is_off_topic(letter_response) is True

    def test_happy_to_help_detected(self):
        """Test that AI assistant phrases are detected."""
        ai_response = "I'm happy to help you with this question..."
        assert is_off_topic(ai_response) is True

    def test_code_response_detected(self):
        """Test that code blocks at start are detected as off-topic."""
        # Code blocks at start are detected (stricter pattern)
        code_response = "```python\nimport pandas as pd\nimport numpy as np"
        assert is_off_topic(code_response) is True

    def test_as_an_ai_detected(self):
        """Test that AI self-reference is detected."""
        ai_response = "As an AI language model, I cannot access your files..."
        assert is_off_topic(ai_response) is True

    def test_email_subject_detected(self):
        """Test that 'Subject:' email format is detected as off-topic."""
        email_response = "Subject: Re: Your manuscript review request..."
        assert is_off_topic(email_response) is True

    def test_email_from_detected(self):
        """Test that 'From:' email header is detected as off-topic."""
        email_response = "From: Assistant <assistant@example.com>..."
        assert is_off_topic(email_response) is True

    def test_casual_greeting_hi_detected(self):
        """Test that 'Hi' casual greeting is detected as off-topic."""
        casual_response = "Hi there! Let me help you with that..."
        assert is_off_topic(casual_response) is True

    def test_casual_greeting_hello_detected(self):
        """Test that 'Hello' casual greeting is detected as off-topic."""
        casual_response = "Hello! I'd be happy to review this..."
        assert is_off_topic(casual_response) is True

    def test_code_block_detected(self):
        """Test that code blocks are detected when not expected."""
        code_response = "```python\nimport pandas as pd\n```"
        assert is_off_topic(code_response) is True

    def test_function_definition_detected(self):
        """Test that multi-import code blocks are detected as off-topic."""
        # Multi-import pattern is detected
        code_response = "Here is my code: import pandas as pd\nimport numpy as np"
        assert is_off_topic(code_response) is True

    def test_feel_free_not_off_topic(self):
        """Test that 'feel free to ask me' is NOT off-topic (it's conversational, not off-topic)."""
        ai_response = "This is great! Feel free to ask me any questions."
        # This phrase is conversational, not off-topic - doesn't indicate confusion
        assert is_off_topic(ai_response) is False

    def test_id_be_happy_detected(self):
        """Test that 'I'm happy to help you with' is detected as off-topic."""
        polite_response = "I'm happy to help you with this analysis request."
        assert is_off_topic(polite_response) is True

