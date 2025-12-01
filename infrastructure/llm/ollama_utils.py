"""Ollama utility functions for model discovery and server management.

Provides utilities for:
- Discovering available local Ollama models
- Selecting the best model based on preferences
- Checking Ollama server status
- Starting Ollama server if needed
"""
from __future__ import annotations

import subprocess
import time
from typing import Optional, List, Dict, Any
import requests

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Default model preferences in order of preference
DEFAULT_MODEL_PREFERENCES = [
    "qwen3:4b",  # Fast with 128K context, excellent instruction following
    "llama3-gradient:latest",  # Large context (256K tokens), ideal for full manuscripts
    "llama3.1:latest",  # Good balance of speed and quality
    "gemma2:2b",        # Fast, small, good instruction following
    "llama2:latest",    # Widely available, reliable
    "gemma3:4b",        # Medium size, good quality
    "mistral:latest",   # Alternative
    "codellama:latest", # Code-focused but can do general tasks
    "smollm2",          # Very fast but limited instruction following
]


def is_ollama_running(base_url: str = "http://localhost:11434", timeout: float = 2.0) -> bool:
    """Check if Ollama server is running and responding.
    
    Args:
        base_url: Ollama server URL
        timeout: Connection timeout in seconds
        
    Returns:
        True if Ollama is responding, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_ollama_server(wait_seconds: float = 3.0) -> bool:
    """Attempt to start the Ollama server.
    
    Args:
        wait_seconds: How long to wait for server to start
        
    Returns:
        True if server started successfully, False otherwise
    """
    try:
        # Try to start ollama serve in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for server to be ready
        time.sleep(wait_seconds)
        return is_ollama_running()
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_available_models(base_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
    """Get list of available models from Ollama.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        List of model dictionaries with 'name', 'size', etc.
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to get available models: {e}")
        return []


def get_model_names(base_url: str = "http://localhost:11434") -> List[str]:
    """Get list of available model names from Ollama.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        List of model names (e.g., ["llama3:latest", "mistral:7b"])
    """
    models = get_available_models(base_url)
    return [m["name"] for m in models]


def select_best_model(
    preferences: Optional[List[str]] = None,
    base_url: str = "http://localhost:11434"
) -> Optional[str]:
    """Select the best available model based on preferences.
    
    Iterates through preference list and returns first available model.
    Falls back to first available model if no preference matches.
    
    Args:
        preferences: Ordered list of preferred model names
        base_url: Ollama server URL
        
    Returns:
        Model name to use, or None if no models available
    """
    available = get_model_names(base_url)
    
    if not available:
        return None
    
    prefs = preferences or DEFAULT_MODEL_PREFERENCES
    
    # Try each preference in order
    for pref in prefs:
        # Check for exact match
        if pref in available:
            logger.info(f"Selected model: {pref}")
            return pref
        
        # Check for partial match (e.g., "llama3" matches "llama3:latest")
        for model in available:
            if pref in model or model.startswith(pref.split(":")[0]):
                logger.info(f"Selected model: {model} (matched preference: {pref})")
                return model
    
    # Fall back to first available
    first = available[0]
    logger.info(f"No preference matched, using first available: {first}")
    return first


def select_small_fast_model(base_url: str = "http://localhost:11434") -> Optional[str]:
    """Select a small, fast model for testing.
    
    Prioritizes smaller models for faster test execution.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        Model name to use, or None if no models available
    """
    fast_preferences = [
        "smollm2",
        "gemma2:2b",
        "gemma3:4b",
        "llama2:latest",
        "mistral:latest",
    ]
    return select_best_model(fast_preferences, base_url)


def ensure_ollama_ready(
    base_url: str = "http://localhost:11434",
    auto_start: bool = True
) -> bool:
    """Ensure Ollama server is running and has models available.
    
    Args:
        base_url: Ollama server URL
        auto_start: Whether to attempt starting Ollama if not running
        
    Returns:
        True if Ollama is ready with models, False otherwise
    """
    # Check if running
    if not is_ollama_running(base_url):
        if auto_start:
            logger.info("Ollama not running, attempting to start...")
            if not start_ollama_server():
                logger.warning("Failed to start Ollama server")
                return False
        else:
            return False
    
    # Check for available models
    models = get_model_names(base_url)
    if not models:
        logger.warning("No Ollama models available. Install with: ollama pull <model>")
        return False
    
    logger.info(f"Ollama ready with {len(models)} model(s): {', '.join(models[:5])}")
    return True


def get_model_info(model_name: str, base_url: str = "http://localhost:11434") -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model
        base_url: Ollama server URL
        
    Returns:
        Model info dictionary or None if not found
    """
    models = get_available_models(base_url)
    for model in models:
        if model["name"] == model_name or model_name in model["name"]:
            return model
    return None

