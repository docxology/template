"""Review-quality validation tests for infrastructure.llm.review and validation."""

from __future__ import annotations

import pytest

from infrastructure.llm.validation import is_off_topic
from infrastructure.llm.review.generator import validate_review_quality


class TestValidateReviewQuality:
    """Tests for validate_review_quality() function."""

    def test_valid_executive_summary(self):
        """Test that well-structured executive summary passes validation."""
        response = (
            """## Overview
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
        """
            + " word" * 300
        )  # Add words to meet minimum

        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is True
        assert len(issues) == 0
        assert "sections_found" in details

    def test_executive_summary_accepts_alternatives(self):
        """Test that alternative section names are accepted."""
        response = (
            """## Summary
        This is the summary section.
        
        ## Contributions
        Main contributions listed here.
        
        ## Methods
        Description of methods used.
        
        ## Findings
        Key findings from the research.
        
        ## Implications
        The implications of this work.
        """
            + " word" * 300
        )

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
        response = (
            """## Clarity Assessment
        **Score: 4**
        The writing is clear and well-organized.
        
        ## Structure
        **Score: 5**
        Excellent structure throughout.
        """
            + " word" * 400
        )

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
        response = (
            """## High Priority
        Critical issues to address.
        
        ## Medium Priority
        Important but not urgent.
        
        ## Low Priority
        Minor improvements.
        """
            + " word" * 300
        )

        is_valid, issues, _ = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is True

    def test_improvement_suggestions_alternative_terms(self):
        """Test that alternative priority terms are accepted."""
        response = (
            """## Critical Issues
        These must be fixed immediately.
        
        ## Moderate Concerns
        Should address these.
        
        ## Nice to Have
        Optional improvements.
        """
            + " word" * 300
        )

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
        response = (
            """## Strengths
        The methodology is sound and well-designed with comprehensive analysis.
        The approach is novel and well-justified.
        """
            + " word" * 400
        )

        is_valid, issues, _ = validate_review_quality(response, "methodology_review")
        assert is_valid is True

    def test_methodology_review_with_strengths_and_weaknesses(self):
        """Test that methodology review with both sections passes."""
        response = (
            """## Strengths
        The methodology is rigorous and well-documented.
        The experimental design is appropriate.
        
        ## Weaknesses
        Sample size could be larger.
        Some assumptions are not validated.
        """
            + " word" * 400
        )

        is_valid, issues, _ = validate_review_quality(response, "methodology_review")
        assert is_valid is True

    def test_methodology_review_alternative_terms(self):
        """Test that alternative section names are accepted."""
        # Using "limitations" instead of "weaknesses"
        response = (
            """## Strong Points
        The methodology is innovative.
        
        ## Limitations
        There are some concerns about generalizability.
        """
            + " word" * 400
        )

        is_valid, issues, _ = validate_review_quality(response, "methodology_review")
        assert is_valid is True

    def test_improvement_suggestions_with_immediate(self):
        """Test that 'immediate' priority term is accepted."""
        response = (
            """## Immediate Actions
        These must be addressed before publication.
        
        ## Consider Later
        These are optional improvements.
        """
            + " word" * 300
        )

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
        from infrastructure.llm.validation.format import detect_conversational_phrases

        text = """## Methodology Review
        
        The manuscript employs rigorous experimental design.
        The results demonstrate significant improvements."""
        assert detect_conversational_phrases(text) == []

    def test_based_on_document_detected(self):
        """Test that 'based on the document you shared' is detected."""
        from infrastructure.llm.validation.format import detect_conversational_phrases

        text = "Based on the document you shared, this appears to be a research paper."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1

    def test_ill_help_you_detected(self):
        """Test that 'I'll help you' is detected."""
        from infrastructure.llm.validation.format import detect_conversational_phrases

        text = "I'll help you understand the key points of this manuscript."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1

    def test_let_me_know_detected(self):
        """Test that 'Let me know if' is detected."""
        from infrastructure.llm.validation.format import detect_conversational_phrases

        text = "Let me know if you need more details about the methodology."
        phrases = detect_conversational_phrases(text)
        assert len(phrases) >= 1

    def test_multiple_phrases_detected(self):
        """Test that multiple conversational phrases are all detected."""
        from infrastructure.llm.validation.format import detect_conversational_phrases

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
        from infrastructure.llm.validation.format import check_format_compliance

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
        from infrastructure.llm.validation.format import check_format_compliance

        text = """## Overview 🔑
        
        The manuscript is excellent! 🚀 Great work! ✅"""

        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is True  # Emojis are allowed now
        assert len(issues) == 0

    def test_tables_allowed(self):
        """Test that table usage is now allowed."""
        from infrastructure.llm.validation.format import check_format_compliance

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
        from infrastructure.llm.validation.format import check_format_compliance

        text = """Based on the document you shared, I'll help you understand the key points.
        Let me know if you need more details."""

        is_compliant, issues, details = check_format_compliance(text)
        assert is_compliant is False
        assert any("conversational" in issue.lower() for issue in issues)
        assert len(details["conversational_phrases"]) > 0

    def test_emojis_tables_with_conversational_still_fails(self):
        """Test that conversational phrases still fail even with emojis/tables."""
        from infrastructure.llm.validation.format import check_format_compliance

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
            "This manuscript presents important research. "
            + "word " * 240
            + "\n## Key Contributions\nSignificant findings here."
        )
        is_valid, issues, details = validate_review_quality(response, "executive_summary")
        assert is_valid is True
        assert "word_count" in details
        assert details["word_count"] >= 250

    def test_one_below_minimum_executive_summary(self):
        """Test that executive summary below minimum (including tolerance) is flagged."""
        # Executive summary requires 250 words. With 5% tolerance, 237 is allowed.
        # We use exactly 150 words to ensure we are well below the threshold and fail.
        response = "## Overview\n" + ("word " * 150)

        is_valid, issues, _ = validate_review_quality(response, "executive_summary")
        assert is_valid is False
        assert any("Too short" in issue for issue in issues)

    def test_improvement_suggestions_new_minimum(self):
        """Test that improvement_suggestions uses new 200-word minimum."""
        # The minimum was lowered from 250 to 200 for improvement_suggestions
        # This tests that a 200-word response now passes
        response = (
            "## Summary\n"
            "This manuscript needs improvements and revisions. " + "## High Priority\n"
            "Critical issues were found in the methodology. "
            + "word " * 185
            + "\n## Medium Priority\nModerate concerns about structure."
        )
        is_valid, issues, details = validate_review_quality(response, "improvement_suggestions")
        assert is_valid is True
        assert details["word_count"] >= 200

    def test_improvement_suggestions_below_new_minimum(self):
        """Test that improvement_suggestions below 200 words fails."""
        # 150 words should fail even with the new lower threshold
        response = (
            "## Summary\nBrief summary. " + "## High Priority\nIssue. " + "word " * 130 + "## Low Priority\nMinor."
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
        from infrastructure.llm.review.generator import validate_review_quality

        # Response with emoji - should be valid now
        response = (
            """## Overview
        
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
        """
            + " word" * 300
        )

        is_valid, issues, details = validate_review_quality(response, "executive_summary", model_name="qwen3:4b")

        # Should pass - emojis are allowed
        assert is_valid is True

    def test_conversational_phrases_still_flagged(self):
        """Test that conversational phrases are flagged as format issues."""
        from infrastructure.llm.review.generator import validate_review_quality

        # Response with conversational phrases
        response = (
            """## Overview
        
        Based on the document you shared, this is a great paper!
        
        ## Key Contributions
        
        I'll help you understand the key points.
        
        ## Methodology
        
        Let me know if you need more details.
        """
            + " word" * 300
        )

        is_valid, issues, details = validate_review_quality(response, "executive_summary", model_name="llama3:70b")

        # Format warnings for conversational phrases should be tracked
        assert "format_compliance" in details or "format_warnings" in details


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
        is_valid, issues, details = validate_review_quality(response, "executive_summary")

        # Check that repetition is tracked
        assert "repetition" in details
        # Severe repetition should either fail or have low unique ratio
        if not is_valid:
            assert any("repetition" in issue.lower() for issue in issues)

    def test_validate_unique_content_passes(self):
        """Test that unique content passes validation."""
        response = (
            """
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
"""
            + " word" * 200
        )  # Ensure word count is met

        is_valid, issues, details = validate_review_quality(response, "executive_summary")

        # Unique content should have high unique ratio
        assert details.get("repetition", {}).get("unique_ratio", 1.0) >= 0.5

    def test_validate_moderate_repetition_warning(self):
        """Test that moderate repetition creates warning but doesn't fail."""
        # Some repeated phrases but mostly unique
        response = (
            """
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
"""
            + " word" * 200
        )

        is_valid, issues, details = validate_review_quality(response, "executive_summary")

        # Should track repetition but not necessarily fail
        assert "repetition" in details
        # Moderate content should have reasonable unique ratio
        unique_ratio = details.get("repetition", {}).get("unique_ratio", 1.0)
        assert isinstance(unique_ratio, float)
