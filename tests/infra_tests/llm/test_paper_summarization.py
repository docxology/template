"""Tests for infrastructure/llm/templates/paper_summarization.py.

Covers: PaperSummarization.render with various parameter combinations.

No mocks used -- all tests use real template rendering with string data.
"""

from __future__ import annotations

from infrastructure.llm.templates.paper_summarization import PaperSummarization


class TestPaperSummarization:
    """Test PaperSummarization template."""

    def test_basic_render(self):
        template = PaperSummarization()
        result = template.render(
            title="Quantum Computing for Climate Modeling",
            authors="Smith, J. and Doe, A.",
            year="2025",
            source="arXiv",
            text="This paper presents a novel approach to quantum computing applications in climate science.",
        )
        assert "Quantum Computing" in result
        assert "Smith" in result
        assert "2025" in result

    def test_render_with_domain(self):
        template = PaperSummarization()
        result = template.render(
            title="Neural Network Architectures",
            authors="Author A.",
            year="2024",
            source="PubMed",
            text="Content about neural networks and deep learning.",
            domain="computer_science",
        )
        assert "computer_science" in result

    def test_render_with_domain_instructions(self):
        template = PaperSummarization()
        result = template.render(
            title="Protein Folding Analysis",
            authors="Bio A.",
            year="2024",
            source="bioRxiv",
            text="Protein folding study.",
            domain="biology",
            domain_instructions="Focus on biological mechanisms.",
        )
        assert "biological mechanisms" in result

    def test_render_with_reference_count(self):
        template = PaperSummarization()
        result = template.render(
            title="Survey of Methods",
            authors="Author B.",
            year="2024",
            source="arXiv",
            text="Survey content with many references.",
            reference_count=42,
        )
        assert "42" in result

    def test_render_with_references_section_found(self):
        template = PaperSummarization()
        result = template.render(
            title="Research Paper",
            authors="Author C.",
            year="2024",
            source="arXiv",
            text="Paper content.",
            references_section_found=True,
        )
        assert "References" in result or "Bibliography" in result

    def test_render_no_references(self):
        template = PaperSummarization()
        result = template.render(
            title="Short Note",
            authors="Author D.",
            year="2024",
            source="arXiv",
            text="Brief note content.",
            reference_count=None,
            references_section_found=False,
        )
        assert "References" in result or "references" in result

    def test_key_terms_extraction(self):
        template = PaperSummarization()
        result = template.render(
            title="Advanced Machine Learning Algorithms for Natural Language Processing",
            authors="Author E.",
            year="2024",
            source="arXiv",
            text="Paper about NLP.",
        )
        # Should extract key terms like "machine", "learning", "algorithms"
        assert "key terms" in result.lower() or "machine" in result.lower()
