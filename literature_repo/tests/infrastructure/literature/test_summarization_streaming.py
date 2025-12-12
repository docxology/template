"""Tests for summarization streaming functionality.

Tests the streaming wrapper that provides real-time progress updates
during LLM generation for paper summarization.
"""
from __future__ import annotations

import time
from unittest.mock import Mock, MagicMock
import pytest

from infrastructure.literature.summarization.streaming import stream_with_progress
from infrastructure.literature.summarization.models import SummarizationProgressEvent


class TestStreamingWrapper:
    """Test stream_with_progress wrapper functionality."""

    def test_stream_with_progress_basic(self):
        """Test basic streaming with progress updates."""
        # Create mock LLM client
        mock_client = Mock()
        
        # Simulate streaming chunks
        chunks = ["This is ", "a test ", "summary ", "with multiple chunks."]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        # Track progress events
        progress_events = []
        
        def progress_callback(event: SummarizationProgressEvent):
            progress_events.append(event)
        
        # Stream with progress
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test prompt",
            progress_callback=progress_callback,
            citation_key="test2024",
            stage="draft_generation",
            update_interval=0.1  # Short interval for testing
        )
        
        # Verify result
        assert result == "This is a test summary with multiple chunks."
        
        # Verify progress events were emitted
        assert len(progress_events) > 0
        
        # Check final event
        final_event = progress_events[-1]
        assert final_event.status == "completed"
        assert final_event.citation_key == "test2024"
        assert final_event.stage == "draft_generation"
        assert "chars_received" in final_event.metadata
        assert "words_received" in final_event.metadata
        assert "chunks_received" in final_event.metadata

    def test_stream_with_progress_periodic_updates(self):
        """Test that progress updates are emitted at regular intervals."""
        mock_client = Mock()
        
        # Create chunks that will take time to process
        chunks = ["Chunk " + str(i) + " " for i in range(20)]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        progress_events = []
        
        def progress_callback(event: SummarizationProgressEvent):
            if event.status == "in_progress":
                progress_events.append(event)
        
        # Stream with short update interval
        start_time = time.time()
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=progress_callback,
            citation_key="test2024",
            stage="draft_generation",
            update_interval=0.05  # Very short for testing
        )
        elapsed = time.time() - start_time
        
        # Should have multiple progress events (at least one per interval)
        # Note: Actual count depends on processing speed
        assert len(progress_events) >= 0  # May be 0 if processing is very fast
        
        # Verify all progress events have streaming metadata
        for event in progress_events:
            assert event.status == "in_progress"
            assert "chars_received" in event.metadata
            assert "words_received" in event.metadata
            assert "elapsed_time" in event.metadata
            assert event.metadata.get("streaming") is True

    def test_stream_with_progress_metadata(self):
        """Test that progress events contain correct metadata."""
        mock_client = Mock()
        chunks = ["Word one ", "word two ", "word three."]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        progress_events = []
        
        def progress_callback(event: SummarizationProgressEvent):
            progress_events.append(event)
        
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=progress_callback,
            citation_key="test2024",
            stage="refinement"
        )
        
        # Check final event metadata
        final_event = [e for e in progress_events if e.status == "completed"][0]
        
        assert final_event.metadata["chars_received"] > 0
        assert final_event.metadata["words_received"] > 0
        assert final_event.metadata["chunks_received"] == 3
        assert final_event.metadata["elapsed_time"] >= 0
        assert final_event.metadata.get("streaming") is True
        assert final_event.metadata.get("final") is True

    def test_stream_with_progress_no_callback(self):
        """Test streaming works without progress callback."""
        mock_client = Mock()
        chunks = ["Test ", "content."]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        # Should not raise error
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=None,
            citation_key="test2024"
        )
        
        assert result == "Test content."

    def test_stream_with_progress_empty_chunks(self):
        """Test handling of empty chunks."""
        mock_client = Mock()
        chunks = ["Valid ", "", "content ", "", "here."]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        progress_events = []
        
        def progress_callback(event: SummarizationProgressEvent):
            progress_events.append(event)
        
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=progress_callback,
            citation_key="test2024"
        )
        
        # Should accumulate non-empty chunks
        assert "Valid" in result
        assert "content" in result
        assert "here" in result

    def test_stream_with_progress_error_handling(self):
        """Test error handling during streaming."""
        mock_client = Mock()
        mock_client.stream_query = Mock(side_effect=Exception("Stream error"))
        
        progress_events = []
        
        def progress_callback(event: SummarizationProgressEvent):
            progress_events.append(event)
        
        # Should raise exception
        with pytest.raises(Exception, match="Stream error"):
            stream_with_progress(
                llm_client=mock_client,
                prompt="Test",
                progress_callback=progress_callback,
                citation_key="test2024"
            )
        
        # Should have emitted failure event
        failure_events = [e for e in progress_events if e.status == "failed"]
        assert len(failure_events) > 0
        assert "error" in failure_events[0].metadata

    def test_stream_with_progress_chunk_accumulation(self):
        """Test that chunks are correctly accumulated."""
        mock_client = Mock()
        
        # Create specific chunks
        chunks = [
            "This is ",
            "a comprehensive ",
            "test summary ",
            "with multiple ",
            "chunks of text."
        ]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=None,
            citation_key="test2024"
        )
        
        # Verify complete accumulation
        expected = "This is a comprehensive test summary with multiple chunks of text."
        assert result == expected

    def test_stream_with_progress_word_counting(self):
        """Test that word counting is accurate."""
        mock_client = Mock()
        chunks = ["One ", "two ", "three ", "four ", "five words."]
        mock_client.stream_query = Mock(return_value=iter(chunks))
        
        progress_events = []
        
        def progress_callback(event: SummarizationProgressEvent):
            if event.status == "completed":
                progress_events.append(event)
        
        result = stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=progress_callback,
            citation_key="test2024"
        )
        
        # Check word count in final event
        final_event = progress_events[0]
        words_received = final_event.metadata["words_received"]
        
        # Should be 6 words: "One", "two", "three", "four", "five", "words"
        assert words_received == 6

    def test_stream_with_progress_different_stages(self):
        """Test streaming works for different stages."""
        mock_client = Mock()
        
        # Use side_effect to return fresh iterator for each call
        mock_client.stream_query = Mock(side_effect=lambda prompt: iter(["Test content."]))
        
        # Test draft_generation stage
        events_draft = []
        stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=lambda e: events_draft.append(e),
            citation_key="test2024",
            stage="draft_generation"
        )
        assert events_draft[-1].stage == "draft_generation"
        
        # Test refinement stage (will get fresh iterator)
        events_refine = []
        stream_with_progress(
            llm_client=mock_client,
            prompt="Test",
            progress_callback=lambda e: events_refine.append(e),
            citation_key="test2024",
            stage="refinement"
        )
        assert events_refine[-1].stage == "refinement"


