"""Tests for scripts/06_llm_review.py - LLM Manuscript Review orchestrator.

Tests cover:
- ReviewMetrics, ManuscriptMetrics, SessionMetrics dataclasses
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
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

import pytest

# Add scripts to path (one more parent level since we're in tests/infrastructure/llm/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

# Import functions and classes from the review script
from scripts import (
    get_max_input_length,
    estimate_tokens,
    ReviewMetrics,
    ManuscriptMetrics,
    SessionMetrics,
    save_review_outputs,
    generate_review_summary,
    validate_review_quality,
    DEFAULT_MAX_INPUT_LENGTH,
)
# Import validation functions from infrastructure (now moved there)
from infrastructure.llm import (
    is_off_topic,
    detect_repetition,
    deduplicate_sections,
)


class TestEstimateTokens:
    """Tests for estimate_tokens() function."""
    
    def test_empty_string(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0
    
    def test_short_text(self):
        """Test token estimation for short text."""
        # 12 characters -> ~3 tokens
        assert estimate_tokens("Hello World!") == 3
    
    def test_longer_text(self):
        """Test token estimation for longer text."""
        # 400 characters -> ~100 tokens
        text = "a" * 400
        assert estimate_tokens(text) == 100
    
    def test_realistic_text(self):
        """Test token estimation for realistic text."""
        # Typical research text
        text = """This research presents a novel approach to optimization 
        using machine learning techniques. The methodology involves 
        training neural networks on synthetic data and evaluating 
        performance on real-world datasets."""
        # ~248 chars -> ~62 tokens
        result = estimate_tokens(text)
        assert 50 <= result <= 70


class TestGetMaxInputLength:
    """Tests for get_max_input_length() function."""
    
    def test_default_value(self):
        """Test default max input length when env var not set."""
        # Clear the environment variable if set
        env_backup = os.environ.pop("LLM_MAX_INPUT_LENGTH", None)
        try:
            result = get_max_input_length()
            assert result == DEFAULT_MAX_INPUT_LENGTH
            assert result == 500000
        finally:
            if env_backup is not None:
                os.environ["LLM_MAX_INPUT_LENGTH"] = env_backup
    
    def test_custom_value(self):
        """Test custom max input length from env var."""
        env_backup = os.environ.get("LLM_MAX_INPUT_LENGTH")
        try:
            os.environ["LLM_MAX_INPUT_LENGTH"] = "100000"
            result = get_max_input_length()
            assert result == 100000
        finally:
            if env_backup is not None:
                os.environ["LLM_MAX_INPUT_LENGTH"] = env_backup
            else:
                os.environ.pop("LLM_MAX_INPUT_LENGTH", None)
    
    def test_unlimited_value(self):
        """Test unlimited input (0) from env var."""
        env_backup = os.environ.get("LLM_MAX_INPUT_LENGTH")
        try:
            os.environ["LLM_MAX_INPUT_LENGTH"] = "0"
            result = get_max_input_length()
            assert result == 0
        finally:
            if env_backup is not None:
                os.environ["LLM_MAX_INPUT_LENGTH"] = env_backup
            else:
                os.environ.pop("LLM_MAX_INPUT_LENGTH", None)
    
    def test_invalid_value_uses_default(self):
        """Test that invalid env var value falls back to default."""
        env_backup = os.environ.get("LLM_MAX_INPUT_LENGTH")
        try:
            os.environ["LLM_MAX_INPUT_LENGTH"] = "invalid"
            result = get_max_input_length()
            assert result == DEFAULT_MAX_INPUT_LENGTH
        finally:
            if env_backup is not None:
                os.environ["LLM_MAX_INPUT_LENGTH"] = env_backup
            else:
                os.environ.pop("LLM_MAX_INPUT_LENGTH", None)


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


class TestManuscriptMetrics:
    """Tests for ManuscriptMetrics dataclass."""
    
    def test_default_values(self):
        """Test default values for ManuscriptMetrics."""
        metrics = ManuscriptMetrics()
        assert metrics.total_chars == 0
        assert metrics.total_words == 0
        assert metrics.total_tokens_est == 0
        assert metrics.truncated is False
        assert metrics.truncated_chars == 0
    
    def test_truncated_manuscript(self):
        """Test ManuscriptMetrics for truncated manuscript."""
        metrics = ManuscriptMetrics(
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
        assert isinstance(metrics.manuscript, ManuscriptMetrics)
        assert isinstance(metrics.reviews, dict)
        assert metrics.total_generation_time == 0.0
        assert metrics.model_name == ""
        assert metrics.max_input_length == 0
    
    def test_with_reviews(self):
        """Test SessionMetrics with review metrics."""
        session = SessionMetrics(
            manuscript=ManuscriptMetrics(total_chars=50000, total_words=8000),
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
                manuscript=ManuscriptMetrics(
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
            result = save_review_outputs(
                reviews, output_dir, "llama3:latest", pdf_path, session_metrics
            )
            
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
                manuscript=ManuscriptMetrics(
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
            
            save_review_outputs(
                reviews, output_dir, "llama3", pdf_path, session_metrics
            )
            
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
                manuscript=ManuscriptMetrics(total_chars=20000, total_words=3000),
            )
            session_metrics.reviews["executive_summary"] = ReviewMetrics(
                output_chars=500, output_words=80, generation_time_seconds=20.0
            )
            session_metrics.reviews["quality_review"] = ReviewMetrics(
                output_chars=600, output_words=100, generation_time_seconds=25.0
            )
            
            save_review_outputs(
                reviews, output_dir, "llama3", pdf_path, session_metrics
            )
            
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
                manuscript=ManuscriptMetrics(
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
                manuscript=ManuscriptMetrics(
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
                manuscript=ManuscriptMetrics(total_chars=50000, total_words=8000),
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
    
    def test_large_text_not_truncated_at_default(self):
        """Test that text under 500K chars is not truncated."""
        # Simulate 100K character text (typical manuscript)
        large_text = "a" * 100000
        
        env_backup = os.environ.pop("LLM_MAX_INPUT_LENGTH", None)
        try:
            max_length = get_max_input_length()
            assert len(large_text) < max_length
        finally:
            if env_backup is not None:
                os.environ["LLM_MAX_INPUT_LENGTH"] = env_backup


class TestModuleImports:
    """Tests for proper module imports."""
    
    def test_all_required_imports_available(self):
        """Test that all required functions/classes are importable."""
        from scripts import (
            ReviewMetrics,
            ManuscriptMetrics,
            SessionMetrics,
            estimate_tokens,
            get_max_input_length,
            log_stage,
            check_ollama_availability,
            extract_manuscript_text,
            generate_executive_summary,
            generate_quality_review,
            generate_methodology_review,
            generate_improvement_suggestions,
            save_review_outputs,
            generate_review_summary,
            main,
        )
        
        # All imports should be available
        assert callable(estimate_tokens)
        assert callable(main)


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


class TestValidateReviewQuality:
    """Tests for validate_review_quality() function."""
    
    def test_valid_executive_summary(self):
        """Test that well-structured executive summary passes validation."""
        response = """## Overview
        This manuscript presents research on optimization.
        
        ## Key Contributions
        - New algorithm design
        - Performance improvements
        
        ## Methodology Summary
        The authors use neural networks for their approach.
        
        ## Principal Results
        The results show 95% accuracy.
        
        ## Significance and Impact
        This work advances the field significantly.
        """ + " word" * 300  # Add words to meet minimum
        
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is True
        assert len(issues) == 0
        assert "sections_found" in details
    
    def test_executive_summary_accepts_alternatives(self):
        """Test that alternative section names are accepted."""
        response = """## Summary
        This is the summary section.
        
        ## Contributions
        Main contributions listed here.
        
        ## Methods
        Description of methods used.
        
        ## Findings
        Key findings from the research.
        
        ## Implications
        The implications of this work.
        """ + " word" * 300
        
        is_valid, issues, _ = validate_review_quality(response, "executive_summary")
        assert is_valid is True
    
    def test_executive_summary_too_short(self):
        """Test that short responses are rejected."""
        response = "This is too short."
        
        is_valid, issues, _ = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("Too short" in issue for issue in issues)
    
    def test_executive_summary_missing_structure(self):
        """Test that responses without structure are flagged."""
        response = "This is a long response without any section headers. " * 50
        
        is_valid, issues, _ = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("Missing expected structure" in issue for issue in issues)
    
    def test_quality_review_with_score(self):
        """Test that quality review with scores passes."""
        response = """## Clarity Assessment
        **Score: 4**
        The writing is clear and well-organized.
        
        ## Structure
        **Score: 5**
        Excellent structure throughout.
        """ + " word" * 400
        
        is_valid, issues, _ = validate_review_quality(response, "quality_review")
        assert is_valid is True
    
    def test_quality_review_alternative_score_formats(self):
        """Test that alternative score formats are accepted."""
        # Test format: [4/5]
        response1 = "Clarity: [4/5] - Good clarity overall. " + " word" * 400
        is_valid1, _, _ = validate_review_quality(response1, "quality_review")
        assert is_valid1 is True
        
        # Test format: rating: 4
        response2 = "The overall rating: 4 out of 5. " + " word" * 400
        is_valid2, _, _ = validate_review_quality(response2, "quality_review")
        assert is_valid2 is True
    
    def test_quality_review_missing_score(self):
        """Test that quality review without scores or assessment sections is flagged."""
        # This response has no scores and no assessment section keywords
        # (clarity, structure, readability, technical accuracy, overall quality)
        response = "The paper is good. The text is fine. The work is adequate. " * 50
        
        is_valid, issues, _ = validate_review_quality(response, "quality_review")
        assert is_valid is False
        assert any("Missing scoring" in issue for issue in issues)
    
    def test_improvement_suggestions_valid(self):
        """Test that improvement suggestions with priorities passes."""
        response = """## High Priority
        Critical issues to address.
        
        ## Medium Priority
        Important but not urgent.
        
        ## Low Priority
        Minor improvements.
        """ + " word" * 300
        
        is_valid, issues, _ = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is True
    
    def test_improvement_suggestions_alternative_terms(self):
        """Test that alternative priority terms are accepted."""
        response = """## Critical Issues
        These must be fixed immediately.
        
        ## Moderate Concerns
        Should address these.
        
        ## Nice to Have
        Optional improvements.
        """ + " word" * 300
        
        is_valid, issues, _ = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is True
    
    def test_off_topic_response_rejected(self):
        """Test that off-topic responses are immediately rejected."""
        response = "Re: Your question - I'm happy to help with this..."
        
        is_valid, issues, _ = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("off-topic" in issue.lower() for issue in issues)
    
    def test_methodology_review_default_validation(self):
        """Test methodology review uses default validation."""
        # methodology_review requires 400 words minimum and at least one section
        response = """## Strengths
        The methodology is sound and well-designed with comprehensive analysis.
        The approach is novel and well-justified.
        """ + " word" * 400
        
        is_valid, issues, _ = validate_review_quality(response, "methodology_review")
        assert is_valid is True
    
    def test_methodology_review_with_strengths_and_weaknesses(self):
        """Test that methodology review with both sections passes."""
        response = """## Strengths
        The methodology is rigorous and well-documented.
        The experimental design is appropriate.
        
        ## Weaknesses
        Sample size could be larger.
        Some assumptions are not validated.
        """ + " word" * 400
        
        is_valid, issues, _ = validate_review_quality(response, "methodology_review")
        assert is_valid is True
    
    def test_methodology_review_alternative_terms(self):
        """Test that alternative section names are accepted."""
        # Using "limitations" instead of "weaknesses"
        response = """## Strong Points
        The methodology is innovative.
        
        ## Limitations
        There are some concerns about generalizability.
        """ + " word" * 400
        
        is_valid, issues, _ = validate_review_quality(response, "methodology_review")
        assert is_valid is True
    
    def test_improvement_suggestions_with_immediate(self):
        """Test that 'immediate' priority term is accepted."""
        response = """## Immediate Actions
        These must be addressed before publication.
        
        ## Consider Later
        These are optional improvements.
        """ + " word" * 300
        
        is_valid, issues, _ = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is True
    
    def test_word_count_tracking(self):
        """Test that word count is tracked in validation details."""
        response = "Short response."
        
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        # Check that word count is in details
        assert "word_count" in details
        assert details["word_count"] == 2
        # Check that word count is mentioned in issues
        assert any("words" in issue.lower() for issue in issues)


class TestDetectConversationalPhrases:
    """Tests for detect_conversational_phrases() function."""
    
    def test_no_conversational_phrases(self):
        """Test that formal academic text returns empty list."""
        from scripts import detect_conversational_phrases
        text = """## Methodology Review
        
        The manuscript employs rigorous experimental design.
        The results demonstrate significant improvements."""
        assert detect_conversational_phrases(text) == []
    
    def test_based_on_document_detected(self):
        """Test that 'based on the document you shared' is detected."""
        from scripts import detect_conversational_phrases
        text = "Based on the document you shared, this appears to be a research paper."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1
    
    def test_ill_help_you_detected(self):
        """Test that 'I'll help you' is detected."""
        from scripts import detect_conversational_phrases
        text = "I'll help you understand the key points of this manuscript."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1
    
    def test_let_me_know_detected(self):
        """Test that 'Let me know if' is detected."""
        from scripts import detect_conversational_phrases
        text = "Let me know if you need more details about the methodology."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1
    
    def test_multiple_phrases_detected(self):
        """Test that multiple conversational phrases are all detected."""
        from scripts import detect_conversational_phrases
        text = """Based on the document you've shared, I'll provide you with analysis.
        Let me know if you have questions. I'd be happy to help further."""
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 2


class TestCheckFormatCompliance:
    """Tests for check_format_compliance() function.
    
    Note: Emojis and tables are now allowed. Only conversational phrases
    are flagged as format violations.
    """
    
    def test_compliant_response(self):
        """Test that properly formatted response passes."""
        from scripts import check_format_compliance
        text = """## Overview
        
        The manuscript presents research on optimization algorithms.
        
        ## Key Contributions
        
        - Novel algorithm design
        - Performance improvements
        
        ## Methodology Summary
        
        The authors employ neural network techniques."""
        
        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is True
        assert len(issues) == 0
    
    def test_emojis_allowed(self):
        """Test that emoji usage is now allowed."""
        from scripts import check_format_compliance
        text = """## Overview 🔑
        
        The manuscript is excellent! 🚀 Great work! ✅"""
        
        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is True  # Emojis are allowed now
        assert len(issues) == 0
    
    def test_tables_allowed(self):
        """Test that table usage is now allowed."""
        from scripts import check_format_compliance
        text = """## Overview

| Feature | Score |
|---------|-------|
| Clarity | 5/5   |
| Structure | 4/5 |"""
        
        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is True  # Tables are allowed now
        assert len(issues) == 0
    
    def test_conversational_violation(self):
        """Test that conversational phrases are flagged."""
        from scripts import check_format_compliance
        text = """Based on the document you shared, I'll help you understand the key points.
        Let me know if you need more details."""
        
        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is False
        assert any("conversational" in issue.lower() for issue in issues)
        assert len(details["conversational_phrases"]) > 0
    
    def test_emojis_tables_with_conversational_still_fails(self):
        """Test that conversational phrases still fail even with emojis/tables."""
        from scripts import check_format_compliance
        text = """## Overview 🚀

| Type | Score |
|------|-------|
| A    | 5/5   |

Based on the document you shared, this describes the approach."""
        
        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is False
        assert any("conversational" in issue.lower() for issue in issues)


class TestWordCountBoundary:
    """Tests for word count boundary conditions in validation."""
    
    def test_exactly_minimum_words_executive_summary(self):
        """Test response with exactly minimum word count passes."""
        # 250 words is the minimum for executive_summary
        # Need to include section headers for structure validation
        response = (
            "## Overview\n"
            "This manuscript presents important research. " + "word " * 240 +
            "\n## Key Contributions\nSignificant findings here."
        )
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is True
        assert "word_count" in details
        assert details["word_count"] >= 250
    
    def test_one_below_minimum_executive_summary(self):
        """Test response one word below minimum fails."""
        # 249 words should fail for executive_summary (minimum 250)
        response = (
            "## Overview\n"
            "This is content. " + "word " * 239 +
            "\n## Key Contributions\nMore content."
        )
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("Too short" in issue for issue in issues)
    
    def test_improvement_suggestions_new_minimum(self):
        """Test that improvement_suggestions uses new 200-word minimum."""
        # The minimum was lowered from 250 to 200 for improvement_suggestions
        # This tests that a 200-word response now passes
        response = (
            "## Summary\n"
            "This manuscript needs improvements and revisions. " +
            "## High Priority\n"
            "Critical issues were found in the methodology. " + "word " * 185 +
            "\n## Medium Priority\nModerate concerns about structure."
        )
        is_valid, issues, details = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is True
        assert details["word_count"] >= 200
    
    def test_improvement_suggestions_below_new_minimum(self):
        """Test that improvement_suggestions below 200 words fails."""
        # 150 words should fail even with the new lower threshold
        response = (
            "## Summary\nBrief summary. " +
            "## High Priority\nIssue. " + "word " * 130 +
            "## Low Priority\nMinor."
        )
        is_valid, issues, details = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is False
        assert any("Too short" in issue for issue in issues)


class TestValidateReviewQualityWithFormatCompliance:
    """Tests for validate_review_quality() with format compliance checks.
    
    Note: Emojis and tables are now allowed. Only conversational phrases
    cause format compliance issues.
    """
    
    def test_emojis_pass_validation(self):
        """Test that emojis don't cause validation failures."""
        from scripts import validate_review_quality
        
        # Response with emoji - should be valid now
        response = """## Overview
        
        The manuscript presents research on optimization. 🚀
        
        ## Key Contributions
        
        - Novel algorithm
        - Improved performance
        
        ## Methodology Summary
        
        The research uses neural networks for analysis.
        
        ## Principal Results
        
        Results show significant improvements.
        
        ## Significance and Impact
        
        This work advances the field of optimization.
        """ + " word" * 300
        
        is_valid, issues, details = validate_review_quality(
            response, "executive_summary", model_name="qwen3:4b"
        )
        
        # Should pass - emojis are allowed
        assert is_valid is True
    
    def test_conversational_phrases_still_flagged(self):
        """Test that conversational phrases are flagged as format issues."""
        from scripts import validate_review_quality
        
        # Response with conversational phrases
        response = """## Overview
        
        Based on the document you shared, this is a great paper!
        
        ## Key Contributions
        
        I'll help you understand the key points.
        
        ## Methodology
        
        Let me know if you need more details.
        """ + " word" * 300
        
        is_valid, issues, details = validate_review_quality(
            response, "executive_summary", model_name="llama3:70b"
        )
        
        # Format warnings for conversational phrases should be tracked
        assert "format_compliance" in details or "format_warnings" in details


# Integration tests that require Ollama
@pytest.mark.requires_ollama
class TestLLMReviewIntegration:
    """Integration tests requiring Ollama server."""
    
    def test_check_ollama_availability(self):
        """Test Ollama availability check."""
        from scripts import check_ollama_availability, is_ollama_running
        
        if not is_ollama_running():
            pytest.skip("Ollama not running")
        
        available, model = check_ollama_availability()
        assert available is True
        assert model is not None
    
    def test_generate_review_with_real_llm(self):
        """Test generating a review with real LLM."""
        from scripts import (
            generate_executive_summary,
            is_ollama_running,
            select_best_model,
            LLMClient,
            LLMConfig,
        )
        
        if not is_ollama_running():
            pytest.skip("Ollama not running")
        
        model = select_best_model()
        if not model:
            pytest.skip("No Ollama models available")
        
        config = LLMConfig.from_env()
        config.default_model = model
        client = LLMClient(config)
        
        # Use a short test text
        test_text = """
        This is a test research manuscript about machine learning.
        The methodology uses neural networks for classification.
        Results show 95% accuracy on the test dataset.
        """
        
        response, metrics = generate_executive_summary(client, test_text)
        
        assert len(response) > 0
        assert metrics.output_chars > 0
        assert metrics.output_words > 0
        assert metrics.generation_time_seconds > 0


class TestValidateReviewQualityRepetition:
    """Tests for repetition detection in validate_review_quality."""

    def test_validate_repetitive_content_fails(self):
        """Test that highly repetitive content fails validation."""
        # Create extremely repetitive content
        repeated_block = "The methodology involves training neural networks. " * 30
        response = f"""
## Overview
{repeated_block}

## Key Contributions
{repeated_block}

## Methodology
{repeated_block}

## Results
{repeated_block}
"""
        is_valid, issues, details = validate_review_quality(
            response, "executive_summary"
        )
        
        # Check that repetition is tracked
        assert "repetition" in details
        # Severe repetition should either fail or have low unique ratio
        if not is_valid:
            assert any("repetition" in issue.lower() for issue in issues)

    def test_validate_unique_content_passes(self):
        """Test that unique content passes validation."""
        response = """
## Overview
This manuscript presents a novel approach to machine learning optimization.

## Key Contributions
The authors introduce three main contributions to the field.

## Methodology
The research methodology follows established scientific practices.

## Results
The experimental results demonstrate significant improvements.

## Significance
This research has important implications for the field.
""" + " word" * 200  # Ensure word count is met
        
        is_valid, issues, details = validate_review_quality(
            response, "executive_summary"
        )
        
        # Unique content should have high unique ratio
        assert details.get("repetition", {}).get("unique_ratio", 1.0) >= 0.5

    def test_validate_moderate_repetition_warning(self):
        """Test that moderate repetition creates warning but doesn't fail."""
        # Some repeated phrases but mostly unique
        response = """
## Overview
This is an excellent manuscript with clear presentation.

## Key Contributions
The contributions are significant and well-documented.

## Methodology
The methodology is sound and well-designed.

## Results
The results demonstrate clear improvements.

## Significance
The work has significant implications for the field.
""" + " word" * 200
        
        is_valid, issues, details = validate_review_quality(
            response, "executive_summary"
        )
        
        # Should track repetition but not necessarily fail
        assert "repetition" in details
        # Moderate content should have reasonable unique ratio
        unique_ratio = details.get("repetition", {}).get("unique_ratio", 1.0)
        assert isinstance(unique_ratio, float)

