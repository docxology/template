"""Tests for summarization prompt builder.

Tests that prompts include enhanced requirements for quotes, length,
and formatting instructions.
"""
from __future__ import annotations

import pytest

from infrastructure.literature.summarization.prompt_builder import SummarizationPromptBuilder
from infrastructure.literature.summarization.models import SummarizationContext


class TestPromptBuilder:
    """Test SummarizationPromptBuilder functionality."""

    @pytest.fixture
    def builder(self):
        """Create a prompt builder instance."""
        return SummarizationPromptBuilder()

    @pytest.fixture
    def sample_context(self):
        """Create a sample context for testing."""
        return SummarizationContext(
            title="Test Paper: A Comprehensive Study",
            abstract="This is a test abstract about machine learning.",
            introduction="This paper introduces novel techniques.",
            conclusion="In conclusion, we have demonstrated...",
            key_terms=["machine learning", "neural networks", "optimization"],
            equations=["E = mc²"],
            full_text="This is the full paper text with comprehensive content."
        )

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return {
            "title": "Test Paper: A Comprehensive Study",
            "authors": ["Author One", "Author Two"],
            "year": "2024",
            "source": "test"
        }

    def test_draft_prompt_includes_quote_requirements(self, builder, sample_context, sample_metadata):
        """Test that draft prompt includes 10-15 quote requirement."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should mention 10-15 quotes
        assert "10-15" in prompt or "10 to 15" in prompt or "ten to fifteen" in prompt.lower()
        assert "quote" in prompt.lower() or "quotes" in prompt.lower()

    def test_draft_prompt_includes_length_requirement(self, builder, sample_context, sample_metadata):
        """Test that draft prompt includes 1000-1500 word requirement."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should mention 1000-1500 words
        assert "1000-1500" in prompt or "1000 to 1500" in prompt

    def test_draft_prompt_includes_quote_formatting(self, builder, sample_context, sample_metadata):
        """Test that draft prompt includes quote formatting instructions."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should include quote formatting guidance
        assert "quote" in prompt.lower()
        assert "format" in prompt.lower() or "formatting" in prompt.lower()
        assert "authors state" in prompt.lower() or "according to" in prompt.lower()

    def test_draft_prompt_includes_evidence_requirements(self, builder, sample_context, sample_metadata):
        """Test that draft prompt requires evidence for claims."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should require evidence
        assert "evidence" in prompt.lower()
        assert "claim" in prompt.lower() or "claims" in prompt.lower()

    def test_draft_prompt_includes_comprehensive_coverage(self, builder, sample_context, sample_metadata):
        """Test that draft prompt includes comprehensive coverage requirements."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should mention methodology, results, discussion
        assert "methodology" in prompt.lower() or "experimental" in prompt.lower()
        assert "results" in prompt.lower() or "findings" in prompt.lower()
        assert "discussion" in prompt.lower() or "contribution" in prompt.lower()

    def test_draft_prompt_includes_full_text_emphasis(self, builder, sample_context, sample_metadata):
        """Test that draft prompt emphasizes using full text."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should emphasize full text
        assert "full paper text" in prompt.lower() or "full text" in prompt.lower()
        assert "primary source" in prompt.lower() or "primary" in prompt.lower()

    def test_refinement_prompt_includes_enhanced_quote_requirements(self, builder, sample_context):
        """Test that refinement prompt includes 10-15 quote requirement."""
        draft = "This is a draft summary."
        issues = ["Missing quotes", "Too short"]
        
        prompt = builder.build_refinement_prompt(draft, issues, sample_context)
        
        # Should mention 10-15 quotes
        assert "10-15" in prompt or "10 to 15" in prompt

    def test_refinement_prompt_includes_length_requirement(self, builder, sample_context):
        """Test that refinement prompt includes 1000-1500 word requirement."""
        draft = "This is a draft summary."
        issues = ["Too short"]
        
        prompt = builder.build_refinement_prompt(draft, issues, sample_context)
        
        # Should mention 1000-1500 words
        assert "1000-1500" in prompt or "1000 to 1500" in prompt

    def test_refinement_prompt_includes_quote_extraction_guidance(self, builder, sample_context):
        """Test that refinement prompt includes quote extraction guidance."""
        draft = "This is a draft summary."
        issues = ["Missing quotes"]
        
        prompt = builder.build_refinement_prompt(draft, issues, sample_context)
        
        # Should guide quote extraction
        assert "quote" in prompt.lower()
        assert "full paper text" in prompt.lower() or "full text" in prompt.lower()
        assert "search" in prompt.lower() or "find" in prompt.lower()

    def test_refinement_prompt_includes_methodology_requirements(self, builder, sample_context):
        """Test that refinement prompt requires methodology details."""
        draft = "This is a draft summary."
        issues = ["Missing methodology"]
        
        prompt = builder.build_refinement_prompt(draft, issues, sample_context)
        
        # Should require methodology details
        assert "methodology" in prompt.lower() or "experimental" in prompt.lower()
        assert "setup" in prompt.lower() or "algorithm" in prompt.lower()

    def test_refinement_prompt_includes_results_requirements(self, builder, sample_context):
        """Test that refinement prompt requires results with numbers."""
        draft = "This is a draft summary."
        issues = ["Missing results"]
        
        prompt = builder.build_refinement_prompt(draft, issues, sample_context)
        
        # Should require numerical results
        assert "results" in prompt.lower() or "findings" in prompt.lower()
        assert "number" in prompt.lower() or "metric" in prompt.lower()

    def test_instructions_section_quote_requirements(self, builder, sample_context):
        """Test that instructions section includes quote requirements."""
        instructions = builder._build_instructions_section(sample_context)
        
        # Should mention 10-15 quotes
        assert "10-15" in instructions or "10 to 15" in instructions
        assert "quote" in instructions.lower()

    def test_instructions_section_length_requirement(self, builder, sample_context):
        """Test that instructions section includes length requirement."""
        instructions = builder._build_instructions_section(sample_context)
        
        # Should mention 1000-1500 words
        assert "1000-1500" in instructions or "1000 to 1500" in instructions

    def test_instructions_section_quote_formatting(self, builder, sample_context):
        """Test that instructions section includes quote formatting."""
        instructions = builder._build_instructions_section(sample_context)
        
        # Should include formatting guidance
        assert "format" in instructions.lower() or "formatting" in instructions.lower()
        assert "authors state" in instructions.lower() or "according to" in instructions.lower()

    def test_validation_checklist_quote_requirement(self, builder, sample_context):
        """Test that validation checklist includes quote requirement."""
        checklist = builder._build_validation_checklist(sample_context)
        
        # Should mention quotes in checklist
        assert "quote" in checklist.lower()
        assert "10-15" in checklist or "10 to 15" in checklist

    def test_validation_checklist_length_requirement(self, builder, sample_context):
        """Test that validation checklist includes length requirement."""
        checklist = builder._build_validation_checklist(sample_context)
        
        # Should mention 1000-1500 words
        assert "1000-1500" in checklist or "1000 to 1500" in checklist

    def test_prompt_includes_key_terms(self, builder, sample_context, sample_metadata):
        """Test that prompt includes key terms."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should include key terms
        for term in sample_context.key_terms:
            assert term in prompt

    def test_prompt_includes_title(self, builder, sample_context, sample_metadata):
        """Test that prompt includes paper title."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should include title
        assert sample_context.title in prompt or sample_metadata["title"] in prompt

    def test_prompt_includes_full_text(self, builder, sample_context, sample_metadata):
        """Test that prompt includes full text."""
        prompt = builder.build_draft_prompt(sample_context, sample_metadata)
        
        # Should include full text
        assert sample_context.full_text in prompt


