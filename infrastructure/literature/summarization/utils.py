"""Utility functions for summarization module.

Shared utilities for model detection, configuration, and common operations.
"""
from __future__ import annotations

import os
import re
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.llm.core.client import LLMClient


def detect_model_size(llm_client: Optional["LLMClient"] = None, metadata: Optional[dict] = None) -> float:
    """Detect model size in billions of parameters.
    
    Attempts to detect model size from multiple sources:
    1. LLM client configuration
    2. Metadata dictionary
    3. Environment variables (OLLAMA_MODEL, LLM_MODEL)
    
    Args:
        llm_client: Optional LLM client for model detection.
        metadata: Optional metadata dictionary that may contain model info.
        
    Returns:
        Model size in billions (e.g., 4.0 for gemma3:4b), or 7.0 as default (medium model).
    """
    model_name = None
    
    # Try to get from LLM client
    if llm_client:
        config = getattr(llm_client, 'config', None)
        if config:
            model_name = getattr(config, 'default_model', None) or getattr(config, 'model', None)
    
    # Try metadata
    if not model_name and metadata:
        model_name = metadata.get('model_name') or metadata.get('model')
    
    # Try environment
    if not model_name:
        model_name = os.environ.get('OLLAMA_MODEL') or os.environ.get('LLM_MODEL')
    
    if model_name:
        # Extract size (e.g., "gemma3:4b" -> 4.0, "llama3.1:70b" -> 70.0)
        size_match = re.search(r':?(\d+(?:\.\d+)?)b', str(model_name).lower())
        if size_match:
            return float(size_match.group(1))
    
    # Default: assume medium model
    return 7.0


def get_model_category(model_size: float) -> str:
    """Get model category based on size.
    
    Args:
        model_size: Model size in billions of parameters.
        
    Returns:
        Category string: "small" (<7B), "medium" (7-13B), or "large" (>13B).
    """
    if model_size < 7:
        return "small"
    elif model_size <= 13:
        return "medium"
    else:
        return "large"


