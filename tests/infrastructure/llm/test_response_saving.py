"""Tests for response saving functionality."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from infrastructure.llm.core.response_saver import (
    ResponseMetadata,
    save_response,
    save_streaming_response,
)


class TestResponseMetadata:
    """Test ResponseMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test creating ResponseMetadata."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test prompt",
            prompt_length=11,
            response_length=100,
            response_tokens_est=25,
        )
        
        assert metadata.model == "llama3"
        assert metadata.prompt == "Test prompt"
        assert metadata.response_length == 100
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = ResponseMetadata(
            timestamp="2024-01-01T00:00:00",
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
        )
        
        data = metadata.to_dict()
        
        assert isinstance(data, dict)
        assert data["model"] == "llama3"
        assert data["timestamp"] == "2024-01-01T00:00:00"
    
    def test_metadata_with_streaming(self):
        """Test metadata with streaming information."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=100,
            response_tokens_est=25,
            streaming=True,
            chunk_count=10,
            streaming_time_seconds=5.0,
        )
        
        assert metadata.streaming is True
        assert metadata.chunk_count == 10
        assert metadata.streaming_time_seconds == 5.0


class TestSaveResponse:
    """Test general response saving."""
    
    def test_save_response_markdown(self, tmp_path):
        """Test saving response as markdown."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="What is AI?",
            prompt_length=10,
            response_length=50,
            response_tokens_est=12,
        )
        
        output_path = tmp_path / "response"
        saved_path = save_response("AI is artificial intelligence.", output_path, metadata, format="markdown")
        
        assert saved_path.exists()
        assert saved_path.suffix == ".md"
        
        content = saved_path.read_text()
        assert "AI is artificial intelligence" in content
        assert "What is AI?" in content
        assert "llama3" in content
    
    def test_save_response_json(self, tmp_path):
        """Test saving response as JSON."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
        )
        
        output_path = tmp_path / "response.json"
        saved_path = save_response("Response text", output_path, metadata, format="json")
        
        assert saved_path.exists()
        
        data = json.loads(saved_path.read_text())
        assert "metadata" in data
        assert "response" in data
        assert data["response"] == "Response text"
    
    def test_save_response_txt(self, tmp_path):
        """Test saving response as plain text."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
        )
        
        output_path = tmp_path / "response.txt"
        saved_path = save_response("Response text", output_path, metadata, format="txt")
        
        assert saved_path.exists()
        
        content = saved_path.read_text()
        assert "Response text" in content
    
    def test_save_response_auto_extension(self, tmp_path):
        """Test save_response adds extension if missing."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
        )
        
        output_path = tmp_path / "response"  # No extension
        saved_path = save_response("Response", output_path, metadata, format="markdown")
        
        assert saved_path.suffix == ".md"
    
    def test_save_response_creates_directory(self, tmp_path):
        """Test save_response creates output directory."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
        )
        
        output_path = tmp_path / "subdir" / "response.md"
        saved_path = save_response("Response", output_path, metadata)
        
        assert output_path.parent.exists()
        assert saved_path.exists()


class TestSaveStreamingResponse:
    """Test streaming response saving."""
    
    def test_save_streaming_response(self, tmp_path):
        """Test saving streaming response."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=100,
            response_tokens_est=25,
            streaming=True,
            chunk_count=5,
            streaming_time_seconds=2.5,
        )
        
        output_path = tmp_path / "streaming.md"
        saved_path = save_streaming_response("Streamed response", output_path, metadata)
        
        assert saved_path.exists()
        
        content = saved_path.read_text()
        assert "Streamed response" in content
        assert "streaming" in content.lower() or "chunk" in content.lower()
    
    def test_save_streaming_partial(self, tmp_path):
        """Test saving partial streaming response."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
            streaming=True,
            chunk_count=3,
            streaming_time_seconds=1.0,
            partial_response=True,
        )
        
        output_path = tmp_path / "partial.md"
        saved_path = save_streaming_response("Partial", output_path, metadata)
        
        assert saved_path.exists()
        
        content = saved_path.read_text()
        assert "Partial" in content
        assert "partial" in content.lower()


class TestResponseSavingIntegration:
    """Integration tests for response saving."""
    
    def test_save_with_metadata_options(self, tmp_path):
        """Test saving with generation options in metadata."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
            options={
                "temperature": 0.7,
                "max_tokens": 100,
                "seed": 42,
            },
        )
        
        output_path = tmp_path / "response.md"
        save_response("Response", output_path, metadata)
        
        content = output_path.read_text()
        # Metadata should be in the file
        assert "temperature" in content or "metadata" in content.lower()
    
    def test_save_with_error_flag(self, tmp_path):
        """Test saving response with error flag."""
        metadata = ResponseMetadata(
            timestamp=datetime.now().isoformat(),
            model="llama3",
            prompt="Test",
            prompt_length=4,
            response_length=50,
            response_tokens_est=12,
            error_occurred=True,
        )
        
        output_path = tmp_path / "error.md"
        save_response("Response", output_path, metadata)
        
        assert output_path.exists()
        # Error flag should be in metadata
        data = metadata.to_dict()
        assert data["error_occurred"] is True


