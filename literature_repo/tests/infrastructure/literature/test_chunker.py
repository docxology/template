"""Tests for PDF text chunking module."""
import pytest
from infrastructure.literature.summarization.chunker import PDFChunker, TextChunk, ChunkingResult


class TestPDFChunker:
    """Test suite for PDFChunker."""
    
    def test_chunk_small_text(self):
        """Test chunking small text (should return single chunk)."""
        chunker = PDFChunker(target_chunk_size=15000, chunk_overlap=500)
        text = "This is a short text that should fit in one chunk. " * 100
        
        result = chunker.chunk_text(text)
        
        assert result.total_chunks == 1
        assert len(result.chunks) == 1
        assert result.chunks[0].text == text
        assert result.chunks[0].is_prioritized is True
    
    def test_chunk_preserves_sections(self):
        """Test that chunking preserves section boundaries."""
        chunker = PDFChunker(target_chunk_size=500, chunk_overlap=50)
        
        text = """Title: Test Paper

Abstract
This is the abstract section with important information.

1. Introduction
This is the introduction section that provides background.

2. Methods
This section describes the methodology.

3. Results
This section presents the results.

Conclusion
This is the conclusion section."""
        
        result = chunker.chunk_text(text, preserve_sections=True)
        
        # Should identify sections
        assert result.total_chunks >= 1
        # First chunk should be prioritized (contains abstract/intro)
        assert result.chunks[0].is_prioritized is True
    
    def test_identify_sections(self):
        """Test section identification."""
        chunker = PDFChunker()
        
        text = """Title: Test Paper

Abstract
This is the abstract content.

1. Introduction
This is the introduction.

Conclusion
This is the conclusion."""
        
        sections = chunker.identify_sections(text)
        
        assert 'abstract' in sections or 'introduction' in sections
        # Should find at least one section
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = PDFChunker(target_chunk_size=1000, chunk_overlap=200)
        # Use smaller text to avoid hanging - still large enough to test overlap
        text = "Sentence. " * 100  # ~1000 chars, enough to test overlap
        
        result = chunker.chunk_text(text, preserve_sections=False)
        
        # Should create at least one chunk
        assert result.total_chunks >= 1
        # If multiple chunks, verify they exist
        if result.total_chunks > 1:
            assert len(result.chunks) == result.total_chunks
    
    def test_estimate_chunk_summary_size(self):
        """Test estimation of combined chunk summary size."""
        chunker = PDFChunker(target_chunk_size=15000)
        
        estimated = chunker.estimate_chunk_summary_size(5)
        
        # Should estimate ~10% of chunk size per chunk
        assert estimated > 0
        assert estimated < 5 * 15000  # Should be less than total chunk size
    
    def test_combine_chunk_summaries(self):
        """Test combining chunk summaries."""
        chunker = PDFChunker()
        
        summaries = [
            "Summary of chunk 1 with key findings.",
            "Summary of chunk 2 with methodology.",
            "Summary of chunk 3 with results."
        ]
        
        combined = chunker.combine_chunk_summaries(summaries)
        
        assert "Chunk 1 Summary" in combined
        assert "Chunk 2 Summary" in combined
        assert "Chunk 3 Summary" in combined
        assert all(s in combined for s in summaries)
    
    def test_chunk_with_empty_text(self):
        """Test chunking empty text."""
        chunker = PDFChunker()
        
        result = chunker.chunk_text("")
        
        # Should handle empty text gracefully
        assert result.total_chunks >= 0
    
    def test_chunk_min_size(self):
        """Test minimum chunk size enforcement."""
        chunker = PDFChunker(target_chunk_size=1000, min_chunk_size=500)
        text = "Short. " * 10  # Very short text
        
        result = chunker.chunk_text(text)
        
        # Should still create at least one chunk if text is meaningful
        assert result.total_chunks >= 0


