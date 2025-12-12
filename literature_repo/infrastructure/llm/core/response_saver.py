"""General-purpose response saving utilities for LLM operations."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ResponseMetadata:
    """Metadata for a saved LLM response."""
    timestamp: str
    model: str
    prompt: str
    prompt_length: int
    response_length: int
    response_tokens_est: int
    generation_time_seconds: Optional[float] = None
    options: Optional[Dict[str, Any]] = None
    streaming: bool = False
    chunk_count: Optional[int] = None
    streaming_time_seconds: Optional[float] = None
    error_occurred: bool = False
    partial_response: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "prompt": self.prompt,
            "prompt_length": self.prompt_length,
            "response_length": self.response_length,
            "response_tokens_est": self.response_tokens_est,
            "generation_time_seconds": self.generation_time_seconds,
            "options": self.options,
            "streaming": self.streaming,
            "chunk_count": self.chunk_count,
            "streaming_time_seconds": self.streaming_time_seconds,
            "error_occurred": self.error_occurred,
            "partial_response": self.partial_response,
        }


def save_response(
    response: str,
    output_path: Path,
    metadata: ResponseMetadata,
    format: str = "markdown"
) -> Path:
    """Save LLM response to file with metadata.
    
    Args:
        response: Response text to save
        output_path: Path to save file (extension may be added based on format)
        metadata: Response metadata
        format: Output format ("markdown", "json", "txt")
        
    Returns:
        Path to saved file
        
    Example:
        >>> metadata = ResponseMetadata(
        ...     timestamp=datetime.now().isoformat(),
        ...     model="llama3",
        ...     prompt="What is AI?",
        ...     prompt_length=10,
        ...     response_length=100,
        ...     response_tokens_est=25
        ... )
        >>> path = save_response("AI is...", Path("response.md"), metadata)
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add extension if not present
    if not output_path.suffix:
        extensions = {"markdown": ".md", "json": ".json", "txt": ".txt"}
        output_path = output_path.with_suffix(extensions.get(format, ".md"))
    
    if format == "markdown":
        time_str = f"{metadata.generation_time_seconds:.2f}s" if metadata.generation_time_seconds is not None else "N/A"
        content = f"""# LLM Response

*Generated on {metadata.timestamp}*
*Model: {metadata.model}*
*Generation time: {time_str}*

## Prompt

{metadata.prompt}

## Response

{response}

---
*Metadata: {json.dumps(metadata.to_dict(), indent=2)}*
"""
    elif format == "json":
        content_dict = {
            "metadata": metadata.to_dict(),
            "prompt": metadata.prompt,
            "response": response,
        }
        content = json.dumps(content_dict, indent=2)
    else:  # txt
        content = f"""LLM Response
Generated: {metadata.timestamp}
Model: {metadata.model}
Prompt: {metadata.prompt}

Response:
{response}
"""
    
    output_path.write_text(content, encoding="utf-8")
    logger.info(
        f"Saved response to {output_path} "
        f"({metadata.response_length:,} chars, {metadata.response_tokens_est:,} tokens est.)"
    )
    
    return output_path


def save_streaming_response(
    response: str,
    output_path: Path,
    metadata: ResponseMetadata,
    format: str = "markdown"
) -> Path:
    """Save streaming response with streaming-specific metadata.
    
    Args:
        response: Accumulated response text
        output_path: Path to save file
        metadata: Response metadata (should have streaming=True)
        format: Output format
        
    Returns:
        Path to saved file
    """
    if metadata.streaming:
        # Add streaming-specific info to metadata
        streaming_info = f"\n*Streaming: {metadata.chunk_count} chunks in {metadata.streaming_time_seconds:.2f}s*"
        if metadata.partial_response:
            streaming_info += " (partial response saved)"
    else:
        streaming_info = ""
    
    # Temporarily modify metadata for display
    original_dict = metadata.to_dict()
    if streaming_info:
        original_dict["streaming_info"] = streaming_info
    
    return save_response(response, output_path, metadata, format)


