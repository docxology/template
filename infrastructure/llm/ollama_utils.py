"""Ollama utility functions for model discovery and server management.

Provides utilities for:
- Discovering available local Ollama models
- Selecting the best model based on preferences
- Checking Ollama server status
- Starting Ollama server if needed
- Checking if a model is loaded in GPU memory
- Preloading models into GPU memory
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import requests

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Default model preferences in order of preference
DEFAULT_MODEL_PREFERENCES = [
    "llama3-gradient:latest",  # Large context (256K), reliable, no thinking mode issues
    "llama3.1:latest",  # Good balance of speed and quality
    "llama2:latest",    # Widely available, reliable
    "gemma2:2b",        # Fast, small, good instruction following
    "gemma3:4b",        # Medium size, good quality
    "mistral:latest",   # Alternative
    "codellama:latest", # Code-focused but can do general tasks
    # Note: qwen3 models use "thinking" mode which requires special handling
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


def check_model_loaded(
    model_name: str,
    base_url: str = "http://localhost:11434"
) -> Tuple[bool, Optional[str]]:
    """Check if a model is currently loaded AND active in Ollama's memory.
    
    Uses Ollama's process list endpoint and checks the expires_at field
    to verify the model is truly loaded and hasn't been evicted from cache.
    
    Args:
        model_name: Name of the model to check
        base_url: Ollama server URL
        
    Returns:
        Tuple of (is_loaded_and_active, loaded_model_name or None)
    """
    try:
        # Use /api/ps to check what models are currently loaded
        response = requests.get(f"{base_url}/api/ps", timeout=5.0)
        if response.status_code != 200:
            return False, None
        
        data = response.json()
        models = data.get("models", [])
        
        if not models:
            return False, None
        
        # Parse current time for expiration check
        now = datetime.now(timezone.utc)
        
        # Check if our target model is loaded AND not expired
        for model in models:
            loaded_name = model.get("name", "")
            expires_at = model.get("expires_at", "")
            
            # Check if model matches
            is_match = model_name in loaded_name or loaded_name.startswith(model_name.split(":")[0])
            
            if is_match:
                # Check if model cache has expired
                if expires_at:
                    try:
                        # Parse ISO format: 2025-12-01T12:26:06.473937-08:00
                        exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        if exp_time > now:
                            # Model is loaded and cache is still valid
                            return True, loaded_name
                        else:
                            # Model listed but cache expired - needs reload
                            logger.debug(f"Model {loaded_name} cache expired at {expires_at}")
                            return False, f"{loaded_name} (cache expired)"
                    except ValueError:
                        # Can't parse expiration, assume it's valid
                        return True, loaded_name
                else:
                    # No expiration info, assume it's loaded
                    return True, loaded_name
        
        # A different model is loaded - report it
        if models:
            other_model = models[0].get("name", "unknown")
            return False, other_model
        
        return False, None
        
    except requests.exceptions.RequestException as e:
        logger.debug(f"Could not check loaded models: {e}")
        return False, None


def preload_model(
    model_name: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 180.0
) -> bool:
    """Force-load a model into GPU memory using Ollama's API.
    
    Uses a real prompt to force actual model loading - empty prompts don't
    trigger model loading in Ollama.
    
    Args:
        model_name: Name of the model to preload
        base_url: Ollama server URL
        timeout: Maximum time to wait for model loading
        
    Returns:
        True if model was loaded successfully
    """
    try:
        # Use a real prompt - empty prompts don't trigger model loading!
        # The model only loads when it has actual content to process
        with requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model_name,
                "prompt": "Say OK",  # Simple prompt to force loading
                "options": {"num_predict": 5},  # Generate a few tokens
                "keep_alive": "10m",  # Keep model in memory for 10 minutes
            },
            timeout=timeout,
            stream=True,
        ) as response:
            if response.status_code != 200:
                return False
            # Read at least one chunk with actual content
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("response"):
                            # Got actual generated content - model is loaded
                            return True
                    except json.JSONDecodeError:
                        continue
            return True  # Got through without error
    except requests.exceptions.RequestException:
        return False

